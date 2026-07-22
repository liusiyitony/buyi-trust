"""
Buyi Trust Protocol — Decision Certificate API
Flask blueprint mounted at /api/certificate

Schema (split into two EAS Schemas):
  Schema 1: DecisionCertificate (created once, immutable)
    bytes32 certId, address provider, string category,
    bytes32 questionHash, bytes32 conclusionHash, uint8 confidence

  Schema 2: DecisionVerification (appendable, linked via refUID)
    bytes32 refCertId, uint8 accuracy, uint8 valueScore,
    bytes32 emotionalTagsHash, bytes32 feedbackHash
"""

import json
import hashlib
import time
import sqlite3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, render_template_string, g

from eas_client import create_offchain_attestation, verify_offchain_attestation
from reputation import compute_reputation
from db import get_db

cert_bp = Blueprint('cert', __name__, url_prefix='/api/cert')

# ── Certificate ID Generator ────────────────────────────────────────
def _generate_cert_id() -> str:
    """BUYI-YYYYMMDD-NNNNN"""
    today = datetime.now(timezone.utc).strftime('%Y%m%d')
    ts = int(time.time() * 1000) % 100000
    return f"BUYI-{today}-{ts:05d}"


def _hash_field(value: str) -> str:
    """SHA256 hash of a string field, returned as hex."""
    if not value:
        return hashlib.sha256(b"").hexdigest()
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


# ── POST /api/certificate — Create a decision certificate ──────────
@cert_bp.route('', methods=['POST'])
def create_certificate():
    data = request.get_json(silent=True) or {}

    # Required fields
    provider_type = data.get('provider_type', 'agent')
    provider_id   = data.get('provider_id', 'buyi-decision-engine')
    provider_name = data.get('provider_name', '不思议决策引擎')
    category      = data.get('category', '事业决策')
    service_type  = data.get('service_type', 'predictive')
    question      = data.get('question', '')
    conclusion    = data.get('conclusion', '')
    confidence    = data.get('confidence', 0)
    detail        = data.get('detail', '')
    client_name   = data.get('client_name', '匿名用户')
    client_wallet = data.get('client_wallet', None)

    if not question or not conclusion:
        return jsonify({"error": "question and conclusion are required"}), 400

    cert_id = _generate_cert_id()
    now = datetime.now(timezone.utc)
    expected_verify = now + timedelta(days=30)

    # Build the certificate record
    cert = {
        "id": cert_id,
        "version": "1.0",
        "provider": {
            "type": provider_type,
            "id": provider_id,
            "name": provider_name,
        },
        "client": {
            "displayName": client_name,
            "wallet": client_wallet,
        },
        "service": {
            "category": category,
            "serviceType": service_type,
            "question": question,
            "questionHash": _hash_field(question),
            "conclusion": conclusion,
            "conclusionHash": _hash_field(conclusion),
            "confidence": min(100, max(0, int(confidence))),
            "detail": detail,
        },
        "verification": {
            "status": "pending",
            "valueScore": 0,
            "emotionalTags": [],
            "clientFeedback": "",
            "verifiedAt": None,
        },
        "createdAt": now.isoformat(),
        "expectedVerifyAt": expected_verify.isoformat(),
        "proof": {
            "schemaCert": "0xfae61079081cb7b718a8b4a1eb8925b8abac936c067538099653ad18cfc148a8",
            "schemaVerify": "PENDING",
            "certHash": "",  # computed below after cert is fully built
        }
    }

    # Compute certHash AFTER cert is fully built
    cert["proof"]["certHash"] = _hash_field(json.dumps(cert, sort_keys=True, ensure_ascii=False))

    # Create EAS offchain attestation for the certificate
    eas_result = create_offchain_attestation(cert)
    cert["proof"]["easUid"] = eas_result.get("uid", "")
    cert["proof"]["easSignature"] = eas_result.get("signature", "")

    # Store in DB
    db = get_db()
    db.execute("""
        INSERT INTO certificates (cert_id, cert_json, provider_type, provider_id,
            provider_name, category, service_type, confidence, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (
        cert_id,
        json.dumps(cert, ensure_ascii=False),
        provider_type,
        provider_id,
        provider_name,
        category,
        service_type,
        confidence,
        now.isoformat(),
    ))
    db.commit()

    share_url = f"https://cert.diubige.com/{cert_id}"

    return jsonify({
        "cert_id": cert_id,
        "share_url": share_url,
        "cert": cert,
    }), 201


# ── POST /api/certificate/<cert_id>/verify — Submit verification ────
@cert_bp.route('/<cert_id>/verify', methods=['POST'])
def verify_certificate(cert_id):
    data = request.get_json(silent=True) or {}

    accuracy      = data.get('accuracy')        # "correct" | "partial" | "incorrect" | null
    value_score   = data.get('valueScore', 0)   # 1-5
    emotional_tags = data.get('emotionalTags', [])
    feedback      = data.get('clientFeedback', '')
    client_name   = data.get('clientName', '匿名用户')

    if not (1 <= value_score <= 5):
        return jsonify({"error": "valueScore must be 1-5"}), 400

    # Verify certificate exists
    db = get_db()
    row = db.execute("SELECT cert_json FROM certificates WHERE cert_id = ?", (cert_id,)).fetchone()
    if not row:
        return jsonify({"error": "certificate not found"}), 404

    cert = json.loads(row["cert_json"])
    now = datetime.now(timezone.utc)

    # Update verification in the certificate
    if accuracy:
        cert["verification"]["status"] = accuracy
    cert["verification"]["valueScore"] = value_score
    cert["verification"]["emotionalTags"] = emotional_tags
    cert["verification"]["clientFeedback"] = feedback
    cert["verification"]["verifiedAt"] = now.isoformat()

    # Create EAS offchain attestation for verification
    verify_record = {
        "refCertId": cert_id,
        "accuracy": accuracy or "pending",
        "valueScore": value_score,
        "emotionalTagsHash": _hash_field(",".join(sorted(emotional_tags))),
        "feedbackHash": _hash_field(feedback),
        "clientName": client_name,
        "verifiedAt": now.isoformat(),
    }
    eas_result = create_offchain_attestation(verify_record, schema="buyi-decision-verify-v1")

    # Update DB
    cert_json = json.dumps(cert, ensure_ascii=False)
    db.execute("""
        UPDATE certificates SET cert_json = ?, status = ?, value_score = ?
        WHERE cert_id = ?
    """, (cert_json, cert["verification"]["status"], value_score, cert_id))

    db.execute("""
        INSERT INTO verifications (cert_id, accuracy, value_score, emotional_tags,
            client_feedback, verified_at, eas_uid)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        cert_id,
        cert["verification"]["status"],
        value_score,
        json.dumps(emotional_tags, ensure_ascii=False),
        feedback,
        now.isoformat(),
        eas_result.get("uid", ""),
    ))
    db.commit()

    return jsonify({
        "cert_id": cert_id,
        "status": cert["verification"]["status"],
        "valueScore": value_score,
        "verifiedAt": now.isoformat(),
    })


# ── GET /api/certificate/<cert_id> — Get certificate data ───────────
@cert_bp.route('/<cert_id>', methods=['GET'])
def get_certificate(cert_id):
    db = get_db()
    row = db.execute("SELECT cert_json, status FROM certificates WHERE cert_id = ?", (cert_id,)).fetchone()
    if not row:
        return jsonify({"error": "certificate not found"}), 404

    cert = json.loads(row["cert_json"])

    # Get verification history
    verifications = db.execute(
        "SELECT accuracy, value_score, emotional_tags, client_feedback, verified_at, eas_uid "
        "FROM verifications WHERE cert_id = ? ORDER BY verified_at DESC",
        (cert_id,)
    ).fetchall()

    verify_list = []
    for v in verifications:
        verify_list.append({
            "accuracy": v["accuracy"],
            "valueScore": v["value_score"],
            "emotionalTags": json.loads(v["emotional_tags"]) if v["emotional_tags"] else [],
            "clientFeedback": v["client_feedback"],
            "verifiedAt": v["verified_at"],
            "easUid": v["eas_uid"],
        })

    return jsonify({
        "cert": cert,
        "verifications": verify_list,
        "verifyUrl": f"https://cert.diubige.com/{cert_id}/verify",
    })


# ── GET /api/reputation/<provider_id> — Get provider reputation ─────
@cert_bp.route('/reputation/<provider_id>', methods=['GET'])
def get_reputation(provider_id):
    db = get_db()
    rows = db.execute(
        "SELECT cert_json FROM certificates WHERE provider_id = ?",
        (provider_id,)
    ).fetchall()

    if not rows:
        return jsonify({"error": "provider not found"}), 404

    certs = [json.loads(r["cert_json"]) for r in rows]
    rep = compute_reputation(certs)

    return jsonify(rep)
