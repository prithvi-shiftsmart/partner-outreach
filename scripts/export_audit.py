#!/usr/bin/env python3
"""
export_audit.py — Export tracking data to CSV + markdown for Ted review.

Usage: python3 scripts/export_audit.py [--days 7]
Output: tracking/exports/audit_YYYYMMDD.csv + audit_YYYYMMDD.md
"""

import sqlite3
import csv
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'tracking', 'outreach.db')
EXPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'tracking', 'exports')


def export_audit(days=7):
    if not os.path.exists(DB_PATH):
        print("No database found. Run: python3 scripts/init_db.py")
        return

    os.makedirs(EXPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    date_str = datetime.now().strftime('%Y%m%d')

    # Export messages to CSV
    csv_path = os.path.join(EXPORT_DIR, f'messages_{date_str}.csv')
    rows = conn.execute("""
        SELECT message_id, partner_id, campaign_id, market, company,
               channel, status, message_content, logged_at, notes
        FROM message_log
        WHERE logged_at > ?
        ORDER BY logged_at DESC
    """, (cutoff,)).fetchall()

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([desc[0] for desc in conn.execute("SELECT * FROM message_log LIMIT 0").description])
        for r in rows:
            writer.writerow(list(r))

    print(f"Messages CSV: {csv_path} ({len(rows)} rows)")

    # Export replies to CSV
    csv_path_replies = os.path.join(EXPORT_DIR, f'replies_{date_str}.csv')
    reply_rows = conn.execute("""
        SELECT reply_id, parent_message_id, partner_id, direction, content,
               classified_intent, confidence, response_content,
               response_approved, requires_human, logged_at
        FROM reply_chain
        WHERE logged_at > ?
        ORDER BY logged_at DESC
    """, (cutoff,)).fetchall()

    with open(csv_path_replies, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([desc[0] for desc in conn.execute("SELECT * FROM reply_chain LIMIT 0").description])
        for r in reply_rows:
            writer.writerow(list(r))

    print(f"Replies CSV: {csv_path_replies} ({len(reply_rows)} rows)")

    # Export summary markdown
    md_path = os.path.join(EXPORT_DIR, f'audit_{date_str}.md')
    with open(md_path, 'w') as f:
        f.write(f"# Outreach Audit — {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Period: last {days} days\n\n")

        f.write(f"## Messages Sent: {len(rows)}\n\n")
        if rows:
            f.write("| Partner | Campaign | Market | Status | Date |\n")
            f.write("|---------|----------|--------|--------|------|\n")
            for r in rows:
                f.write(f"| {r['partner_id'][:12]} | {r['campaign_id']} | {r['market']} | {r['status']} | {r['logged_at'][:10]} |\n")

        f.write(f"\n## Replies: {len(reply_rows)}\n\n")
        if reply_rows:
            f.write("| Partner | Direction | Intent | Approved | Date |\n")
            f.write("|---------|-----------|--------|----------|------|\n")
            for r in reply_rows:
                intent = r['classified_intent'] or '-'
                approved = 'Yes' if r['response_approved'] else 'No'
                f.write(f"| {r['partner_id'][:12]} | {r['direction']} | {intent} | {approved} | {r['logged_at'][:10]} |\n")

    print(f"Audit markdown: {md_path}")
    conn.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=7)
    args = parser.parse_args()
    export_audit(args.days)
