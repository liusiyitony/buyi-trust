"""
Buyi Trust Protocol — Verification Reminder Cron Job

Runs daily. Checks for certificates that were created ~30 days ago
and haven't been verified yet. Sends reminders.

For Phase 1: logs certificates to be reminded.
Phase 2: integrates with WeChat API to send actual messages.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import get_pending_verifications, init_db
from datetime import datetime, timezone


def run():
    init_db()
    
    # Get certificates from 7, 14, and 30 days ago
    for days in [7, 14, 30]:
        certs = get_pending_verifications(days_ago=days)
        if certs:
            print(f"\n📬 {len(certs)} certificates need {days}-day verification reminder:")
            for cert in certs:
                import json
                c = json.loads(cert["cert_json"])
                client = c.get("client", {}).get("displayName", "匿名")
                service = c.get("service", {})
                print(f"  · {cert['cert_id']} | {client} | {service.get('category','?')} | created {cert['created_at'][:10]}")
                
                # Phase 2: send_wechat_reminder(cert)
                # send_wechat_reminder(cert) would call WeChat API:
                #   POST https://api.weixin.qq.com/cgi-bin/message/...
    
    print(f"\n✓ Reminder check complete at {datetime.now(timezone.utc).isoformat()}")


if __name__ == '__main__':
    run()
