"""
Buyi Trust Protocol — Reputation Engine

Three-dimensional weighted scoring with exponential time decay.

Dimensions:
  1. Accuracy:    "correct" / "partial" / "incorrect" (predictive services only)
  2. Value Score: 1-5 client rating (all services)
  3. Emotional:   Tag match rate (experiential services only)

Weights by service type:
  Predictive:   accuracy×0.55 + value×0.30 + volume×0.15
  Experiential: value×0.55    + emotional×0.30 + volume×0.15
  Mixed:        accuracy×0.35 + value×0.35 + emotional×0.15 + volume×0.15

Time decay: exponential, half-life 6 months.
  weight(t) = 0.5 ^ (months_ago / 6)
  Equivalent to: weight(t) = exp(-0.1155 × months_ago)

Anti-gaming:
  - Minimum 5 verifications to show public score
  - Same client can only verify same provider once every 30 days
  - No score shown for <5 verifications ("数据积累中")
"""

import json
import math
from datetime import datetime, timezone
from typing import Any


# ── Time Decay ──────────────────────────────────────────────────────
HALF_LIFE_MONTHS = 6.0
DECAY_LAMBDA = math.log(2) / HALF_LIFE_MONTHS  # ≈ 0.1155


def _months_ago(iso_timestamp: str) -> float:
    """Calculate months between now and an ISO timestamp."""
    if not iso_timestamp:
        return 12.0  # default: treat as old
    
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = now - dt
        return delta.days / 30.44  # average days per month
    except (ValueError, TypeError):
        return 12.0


def _time_weight(iso_timestamp: str) -> float:
    """Exponential decay weight: 0.5^(months/6)."""
    months = _months_ago(iso_timestamp)
    return math.pow(0.5, months / HALF_LIFE_MONTHS)


# ── Accuracy Scoring ────────────────────────────────────────────────
def _accuracy_score(status: str) -> float:
    """Convert accuracy status to numeric score."""
    scores = {
        "correct": 1.0,
        "partial": 0.5,
        "incorrect": 0.0,
        "pending": None,  # excluded from calculation
    }
    return scores.get(status, None)


# ── Emotional Tag Matching ──────────────────────────────────────────
# Core emotional tags we care about
CORE_TAGS = {"理清思路", "得到安心", "打开新视角", "心情变好", "增强信心"}


def _emotional_score(tags: list[str]) -> float:
    """
    Score based on how many core emotional tags are matched.
    Range: 0.0 (none matched) to 1.0 (all matched).
    """
    if not tags:
        return 0.0
    matched = sum(1 for t in tags if t in CORE_TAGS)
    return matched / len(CORE_TAGS)


# ── Main Reputation Computation ─────────────────────────────────────
def compute_reputation(certificates: list[dict]) -> dict:
    """
    Compute reputation for a provider from their certificates.
    
    Args:
        certificates: List of certificate dicts (from DB)
    
    Returns:
        Dict with total score, trend, breakdown by category, and time-window stats.
    """
    total = len(certificates)
    
    if total < 5:
        return {
            "providerType": certificates[0].get("provider", {}).get("type", "unknown") if certificates else "unknown",
            "totalServices": total,
            "status": "accumulating",
            "message": "数据积累中（需要至少5次验证才能展示声誉评分）",
            "predictive": None,
            "experiential": None,
            "mixed": None,
            "trend": None,
            "onChainCount": 0,
            "pendingCount": sum(1 for c in certificates 
                              if c.get("verification", {}).get("status") == "pending"),
        }
    
    # Separate by service type
    predictive = []
    experiential = []
    mixed = []
    
    for cert in certificates:
        st = cert.get("service", {}).get("serviceType", "predictive")
        verify = cert.get("verification", {})
        verified_at = verify.get("verifiedAt", "")
        
        if not verified_at:
            continue
        
        if st == "predictive":
            predictive.append(cert)
        elif st == "experiential":
            experiential.append(cert)
        else:
            mixed.append(cert)
    
    result = {
        "providerType": certificates[0].get("provider", {}).get("type", "unknown"),
        "providerName": certificates[0].get("provider", {}).get("name", ""),
        "totalServices": total,
        "status": "ready",
        "onChainCount": total,
        "pendingCount": sum(1 for c in certificates 
                          if c.get("verification", {}).get("status") == "pending"),
    }
    
    # Compute by type
    result["predictive"] = _compute_type_score(predictive, "predictive")
    result["experiential"] = _compute_type_score(experiential, "experiential")
    result["mixed"] = _compute_type_score(mixed, "mixed")
    
    # Trend: compare last 3 months vs previous 3 months
    result["trend"] = _compute_trend(certificates)
    
    return result


def _compute_type_score(certs: list[dict], service_type: str) -> dict | None:
    """Compute weighted reputation score for a specific service type."""
    if not certs:
        return None
    
    total_weight = 0.0
    weighted_accuracy = 0.0
    weighted_value = 0.0
    weighted_emotional = 0.0
    accuracy_count = 0
    verified_count = 0
    
    accuracy_dist = {"correct": 0, "partial": 0, "incorrect": 0}
    
    for cert in certs:
        verify = cert.get("verification", {})
        verified_at = verify.get("verifiedAt", "")
        
        if not verified_at:
            continue
        
        verified_count += 1
        w = _time_weight(verified_at)
        total_weight += w
        
        # Accuracy
        acc_status = verify.get("status", "pending")
        acc = _accuracy_score(acc_status)
        if acc is not None:
            weighted_accuracy += acc * w
            accuracy_count += 1
            accuracy_dist[acc_status] = accuracy_dist.get(acc_status, 0) + 1
        
        # Value
        vs = verify.get("valueScore", 0)
        if vs:
            weighted_value += (vs / 5.0) * w
        
        # Emotional
        tags = verify.get("emotionalTags", [])
        weighted_emotional += _emotional_score(tags) * w
    
    if total_weight == 0:
        return None
    
    avg_accuracy = weighted_accuracy / total_weight if accuracy_count > 0 else 0
    avg_value = weighted_value / total_weight if verified_count > 0 else 0
    avg_emotional = weighted_emotional / total_weight if verified_count > 0 else 0
    
    # Final aggregated score based on service type
    if service_type == "predictive":
        final = avg_accuracy * 0.55 + avg_value * 0.30
        # Add volume bonus (max 0.15)
        volume_bonus = min(0.15, math.log2(max(verified_count, 1)) * 0.03)
        final += volume_bonus
    elif service_type == "experiential":
        final = avg_value * 0.55 + avg_emotional * 0.30
        volume_bonus = min(0.15, math.log2(max(verified_count, 1)) * 0.03)
        final += volume_bonus
    else:  # mixed
        final = avg_accuracy * 0.35 + avg_value * 0.35 + avg_emotional * 0.15
        volume_bonus = min(0.15, math.log2(max(verified_count, 1)) * 0.03)
        final += volume_bonus
    
    # Scale to 0-5
    display_score = round(final * 5, 1)
    display_score = min(5.0, max(1.0, display_score))
    
    total_verified = sum(accuracy_dist.values())
    
    return {
        "count": verified_count,
        "displayScore": display_score,
        "rawScore": round(final, 4),
        "accuracyRate": round(accuracy_dist.get("correct", 0) / max(total_verified, 1) * 100, 1),
        "partialRate": round(accuracy_dist.get("partial", 0) / max(total_verified, 1) * 100, 1),
        "incorrectRate": round(accuracy_dist.get("incorrect", 0) / max(total_verified, 1) * 100, 1),
        "avgValueScore": round(avg_value * 5, 1),
        "avgEmotionalScore": round(avg_emotional * 100, 1),
    }


def _compute_trend(certificates: list[dict]) -> dict | None:
    """Compare recent 3 months vs previous 3 months."""
    recent_certs = []
    older_certs = []
    
    for cert in certificates:
        created = cert.get("createdAt", "")
        months = _months_ago(created)
        if months <= 3:
            recent_certs.append(cert)
        elif months <= 6:
            older_certs.append(cert)
    
    if not recent_certs or not older_certs:
        return None
    
    recent_score = _compute_raw_score(recent_certs)
    older_score = _compute_raw_score(older_certs)
    
    delta = recent_score - older_score
    
    return {
        "recent3Months": round(recent_score * 5, 1),
        "previous3Months": round(older_score * 5, 1),
        "delta": round(delta * 5, 1),
        "direction": "up" if delta > 0.05 else "down" if delta < -0.05 else "stable",
    }


def _compute_raw_score(certs: list[dict]) -> float:
    """Simple raw score for trend comparison."""
    total_w = 0.0
    total_score = 0.0
    
    for cert in certs:
        verify = cert.get("verification", {})
        verified_at = verify.get("verifiedAt", "")
        if not verified_at:
            continue
        
        w = _time_weight(verified_at)
        total_w += w
        
        acc = _accuracy_score(verify.get("status", "pending"))
        vs = verify.get("valueScore", 0) / 5.0
        
        if acc is not None:
            total_score += (acc * 0.5 + vs * 0.5) * w
        else:
            total_score += vs * w
    
    return total_score / total_w if total_w > 0 else 0.0
