#!/usr/bin/env python3
"""
send_batch.py — Send messages from a JSON file in the background.

Usage: python3 scripts/send_batch.py <batch_file.json>

The batch file is a JSON array of objects with: phone, message, partner_id, campaign, market, company, first_name, last_name, team_id
Writes progress to a status file next to the batch file.
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime

# Load salesmsg config
sys.path.insert(0, os.path.dirname(__file__))
from salesmsg_config import API_URL, HEADERS, DB_PATH

import requests


def send_one(phone, message, team_id):
    payload = {"number": phone, "message": message}
    if team_id:
        payload["team_id"] = team_id
    try:
        resp = requests.post(f"{API_URL}/messages", headers=HEADERS, json=payload)
        if resp.status_code in (200, 201):
            return True, "Sent"
        else:
            return False, f"HTTP {resp.status_code}: {resp.text[:150]}"
    except Exception as e:
        return False, str(e)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/send_batch.py <batch_file.json>")
        sys.exit(1)

    batch_file = sys.argv[1]
    with open(batch_file) as f:
        drafts = json.load(f)

    status_file = batch_file.replace(".json", "_status.json")
    total = len(drafts)
    sent = 0
    errors = []

    # Write initial status
    def write_status():
        with open(status_file, "w") as sf:
            json.dump({
                "total": total, "sent": sent, "errors": len(errors),
                "error_details": errors[-5:],  # last 5 errors
                "done": sent + len(errors) >= total,
                "updated_at": datetime.now().isoformat()
            }, sf)

    write_status()

    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    for i, d in enumerate(drafts):
        phone = d["phone"]
        pid = d.get("partner_id") or f"sm_{phone}"
        team_id = d.get("team_id")
        campaign = d.get("campaign", "batch_send")
        msg_id = f"{campaign}_{datetime.now().strftime('%Y%m%d')}_{i+1:04d}"

        # Create partner_conversations entry
        conn.execute("""
            INSERT OR IGNORE INTO partner_conversations
            (partner_id, phone_number, current_state, channel, last_message_at, total_message_count)
            VALUES (?, ?, 'new_download', 'sms', datetime('now'), 0)
        """, (pid, phone))

        # Log to message_log
        conn.execute("""
            INSERT OR IGNORE INTO message_log
            (message_id, partner_id, campaign_id, market, company,
             channel, message_content, status, notes)
            VALUES (?, ?, ?, ?, ?, 'salesmsg', ?, 'sending', ?)
        """, (msg_id, pid, campaign, d.get("market", ""),
              d.get("company", ""), d["message"],
              json.dumps({"first_name": d.get("first_name", ""), "last_name": d.get("last_name", ""),
                          "phone": phone, "bq_partner_id": d.get("partner_id", "")})))
        conn.commit()

        # Send
        success, output = send_one(phone, d["message"], team_id)
        if success:
            conn.execute("""
                UPDATE message_log SET sent_at = datetime('now'), status = 'sent'
                WHERE message_id = ?
            """, (msg_id,))
            conn.execute("""
                UPDATE partner_conversations
                SET last_message_at = datetime('now'), total_message_count = total_message_count + 1
                WHERE partner_id = ?
            """, (pid,))
            conn.commit()
            sent += 1
        else:
            conn.execute("UPDATE message_log SET status = 'error', notes = ? WHERE message_id = ?",
                         (output[:200], msg_id))
            conn.commit()
            errors.append(f"{d.get('first_name', phone)}: {output[:100]}")

        write_status()

        # Rate limit: don't exceed 60 req/min
        if (i + 1) % 50 == 0:
            time.sleep(2)

    conn.close()
    write_status()
    print(f"Done. Sent {sent}/{total}. Errors: {len(errors)}")


if __name__ == "__main__":
    main()
