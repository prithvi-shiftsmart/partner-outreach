#!/usr/bin/env python3
"""
log_reply.py — Log a partner reply and optionally our response to SQLite.

Usage from Claude Code:
  python3 scripts/log_reply.py \
    --id reply_001 \
    --parent msg_20260324_001 \
    --partner abc-123 \
    --direction inbound \
    --content "How much does it pay?" \
    --intent pay_question \
    --confidence high

Or import and call:
  from scripts.log_reply import log_reply
"""

import sqlite3
import os
import argparse

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'tracking', 'outreach.db')


def log_reply(reply_id, parent_message_id, partner_id, direction, content,
              classified_intent=None, confidence=None, response_content=None,
              response_approved=0, requires_human=0, notes=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT OR REPLACE INTO reply_chain
           (reply_id, parent_message_id, partner_id, direction, content,
            classified_intent, confidence, response_content,
            response_approved, requires_human, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (reply_id, parent_message_id, partner_id, direction, content,
         classified_intent, confidence, response_content,
         response_approved, requires_human, notes)
    )
    conn.commit()
    conn.close()
    print(f"Logged reply: {reply_id} | {direction} | {partner_id} | intent={classified_intent}")


def main():
    parser = argparse.ArgumentParser(description='Log reply')
    parser.add_argument('--id', required=True)
    parser.add_argument('--parent', required=True)
    parser.add_argument('--partner', required=True)
    parser.add_argument('--direction', required=True, choices=['inbound', 'outbound'])
    parser.add_argument('--content', required=True)
    parser.add_argument('--intent', default=None)
    parser.add_argument('--confidence', default=None)
    parser.add_argument('--response', default=None)
    parser.add_argument('--approved', type=int, default=0)
    parser.add_argument('--human', type=int, default=0)
    parser.add_argument('--notes', default=None)
    args = parser.parse_args()

    log_reply(args.id, args.parent, args.partner, args.direction, args.content,
              args.intent, args.confidence, args.response, args.approved, args.human, args.notes)


if __name__ == '__main__':
    main()
