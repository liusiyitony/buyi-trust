"""
Buyi Trust Protocol — Daily Batch Onchain Timestamp

Runs daily at midnight UTC. Computes Merkle root of all certificates
created today and submits a single EAS onchain attestation.

Cost: ~$0.002/day on Base (one transaction for unlimited certificates).
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import get_today_certificates, save_daily_root, init_db
from eas_client import batch_timestamp_onchain
from datetime import datetime, timezone, date


def run():
    init_db()
    
    today = date.today().isoformat()
    rows = get_today_certificates()
    
    if not rows:
        print(f"📭 No certificates created today ({today}). Nothing to timestamp.")
        return
    
    certificates = [json.loads(r["cert_json"]) for r in rows]
    print(f"📜 {len(certificates)} certificates to timestamp ({today})")
    
    result = batch_timestamp_onchain(certificates)
    
    merkle_root = result.get("merkleRoot", "")
    tx_hash = result.get("txHash", "")
    
    save_daily_root(
        date=today,
        merkle_root=merkle_root,
        cert_count=len(certificates),
        tx_hash=tx_hash,
    )
    
    print(f"🔗 Merkle Root: {merkle_root}")
    print(f"⛓  Tx Hash: {tx_hash or 'pending'}")
    print(f"✓ Daily batch timestamp complete at {datetime.now(timezone.utc).isoformat()}")
    
    # Phase 2: Post Merkle root to WeChat public account article
    # publish_daily_hash_article(merkle_root, len(certificates))


if __name__ == '__main__':
    run()
