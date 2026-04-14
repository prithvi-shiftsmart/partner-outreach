#!/usr/bin/env python3
"""
show_dashboard.py — Quick funnel metrics from SQLite tracking DB.

Usage: python3 scripts/show_dashboard.py [--days 7]
"""

import sqlite3
import os
import argparse
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'tracking', 'outreach.db')


def show_dashboard(days=7):
    if not os.path.exists(DB_PATH):
        print("No database found. Run: python3 scripts/init_db.py")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    print(f"\n{'='*60}")
    print(f"  OUTREACH DASHBOARD — Last {days} days")
    print(f"{'='*60}\n")

    # Messages by campaign
    rows = conn.execute("""
        SELECT campaign_id, COUNT(*) as count, status
        FROM message_log
        WHERE logged_at > ?
        GROUP BY campaign_id, status
        ORDER BY campaign_id
    """, (cutoff,)).fetchall()

    if rows:
        print("MESSAGES BY CAMPAIGN")
        print(f"  {'Campaign':<30} {'Status':<12} {'Count':>6}")
        print(f"  {'-'*30} {'-'*12} {'-'*6}")
        for r in rows:
            print(f"  {r['campaign_id']:<30} {r['status']:<12} {r['count']:>6}")
    else:
        print("MESSAGES: None logged yet")

    # Messages by market
    rows = conn.execute("""
        SELECT market, COUNT(*) as count
        FROM message_log
        WHERE logged_at > ?
        GROUP BY market
        ORDER BY count DESC
        LIMIT 10
    """, (cutoff,)).fetchall()

    if rows:
        print(f"\nTOP MARKETS")
        print(f"  {'Market':<30} {'Messages':>8}")
        print(f"  {'-'*30} {'-'*8}")
        for r in rows:
            print(f"  {r['market']:<30} {r['count']:>8}")

    # Replies
    rows = conn.execute("""
        SELECT classified_intent, COUNT(*) as count
        FROM reply_chain
        WHERE logged_at > ? AND direction = 'inbound'
        GROUP BY classified_intent
        ORDER BY count DESC
    """, (cutoff,)).fetchall()

    if rows:
        print(f"\nREPLIES BY INTENT")
        print(f"  {'Intent':<30} {'Count':>6}")
        print(f"  {'-'*30} {'-'*6}")
        for r in rows:
            intent = r['classified_intent'] or 'unclassified'
            print(f"  {intent:<30} {r['count']:>6}")

    # Reply rate
    total_msgs = conn.execute(
        "SELECT COUNT(*) FROM message_log WHERE logged_at > ?", (cutoff,)
    ).fetchone()[0]
    total_replies = conn.execute(
        "SELECT COUNT(DISTINCT parent_message_id) FROM reply_chain WHERE logged_at > ? AND direction='inbound'",
        (cutoff,)
    ).fetchone()[0]

    if total_msgs > 0:
        rate = (total_replies / total_msgs) * 100
        print(f"\nREPLY RATE: {total_replies}/{total_msgs} ({rate:.1f}%)")

    # Outcome events
    rows = conn.execute("""
        SELECT event_type, COUNT(*) as count
        FROM outcome_events
        WHERE logged_at > ?
        GROUP BY event_type
        ORDER BY event_type
    """, (cutoff,)).fetchall()

    if rows:
        print(f"\nFUNNEL EVENTS (attributed to outreach)")
        print(f"  {'Event':<12} {'Count':>6}")
        print(f"  {'-'*12} {'-'*6}")
        for r in rows:
            print(f"  {r['event_type']:<12} {r['count']:>6}")

    print(f"\n{'='*60}\n")
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=7)
    args = parser.parse_args()
    show_dashboard(args.days)
