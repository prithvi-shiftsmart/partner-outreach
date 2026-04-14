#!/usr/bin/env python3
"""
retry_errors.py — Retry all messages with status='error' in the DB.

Reads phone + message from the DB, resends via Salesmsg API, updates status.
Usage: python3 scripts/retry_errors.py [--dry-run]
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from salesmsg_config import API_URL, HEADERS, DB_PATH

import requests


def send_one(phone, message, team_id=None):
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
    dry_run = "--dry-run" in sys.argv

    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    # Get all error messages
    rows = conn.execute("""
        SELECT message_id, partner_id, campaign_id, message_content, notes
        FROM message_log
        WHERE status = 'error'
        ORDER BY message_id
    """).fetchall()

    total = len(rows)
    print(f"Found {total} failed messages to retry")

    if dry_run:
        print("DRY RUN — not sending")
        for r in rows[:5]:
            notes = json.loads(r["notes"]) if r["notes"] else {}
            print(f"  {r['message_id']}: {notes.get('phone', '?')} - {notes.get('first_name', '?')}")
        if total > 5:
            print(f"  ... and {total - 5} more")
        conn.close()
        return

    sent = 0
    errors = 0
    start = time.time()

    for i, r in enumerate(rows):
        notes = json.loads(r["notes"]) if r["notes"] else {}
        phone = notes.get("phone", "")
        if not phone:
            print(f"  SKIP {r['message_id']}: no phone number")
            errors += 1
            continue

        # Extract team_id from notes or use default
        team_id = notes.get("team_id") or 66423

        success, output = send_one(phone, r["message_content"], team_id)

        if success:
            for attempt in range(5):
                try:
                    conn.execute("""
                        UPDATE message_log SET sent_at = datetime('now'), status = 'sent'
                        WHERE message_id = ?
                    """, (r["message_id"],))
                    conn.execute("""
                        UPDATE partner_conversations
                        SET last_message_at = datetime('now'), total_message_count = total_message_count + 1
                        WHERE partner_id = ?
                    """, (r["partner_id"],))
                    conn.commit()
                    break
                except sqlite3.OperationalError:
                    time.sleep(1)
            sent += 1
        else:
            errors += 1
            if errors <= 3:
                print(f"  ERROR {r['message_id']}: {output}")
            elif errors == 4:
                print("  (suppressing further error details)")
            # If we get 5 consecutive errors at the start, token might be bad
            if sent == 0 and errors >= 5:
                print(f"\n5 consecutive errors with 0 successes — token may be invalid. Aborting.")
                conn.close()
                sys.exit(1)

        # Progress update every 50
        if (i + 1) % 50 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            print(f"  Progress: {i+1}/{total} ({sent} sent, {errors} errors) — {rate:.1f} msg/s")
            time.sleep(1)  # Rate limit pause

    conn.close()
    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.0f}s. Sent: {sent}/{total}. Errors: {errors}")


if __name__ == "__main__":
    main()
