#!/usr/bin/env python3
"""
log_message.py — Log an approved outbound message to SQLite.

Usage from Claude Code:
  python3 scripts/log_message.py \
    --id msg_20260324_001 \
    --partner abc-123 \
    --campaign activation_small \
    --market Morgantown_WV \
    --company "Circle K - Premium" \
    --message "Hi Jane! I'm your Shiftsmart guide..."

Or import and call directly:
  from scripts.log_message import log_message
  log_message(message_id, partner_id, campaign_id, market, company, message_content)
"""

import sqlite3
import os
import sys
import argparse
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'tracking', 'outreach.db')


def log_message(message_id, partner_id, campaign_id, market, company, message_content,
                template_version=None, channel='manual_zendesk', status='approved', notes=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT OR REPLACE INTO message_log
           (message_id, partner_id, campaign_id, template_version, market, company,
            channel, message_content, status, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (message_id, partner_id, campaign_id, template_version, market, company,
         channel, message_content, status, notes)
    )
    conn.commit()
    conn.close()
    print(f"Logged: {message_id} | {partner_id} | {campaign_id} | {market}")


def main():
    parser = argparse.ArgumentParser(description='Log outbound message')
    parser.add_argument('--id', required=True)
    parser.add_argument('--partner', required=True)
    parser.add_argument('--campaign', required=True)
    parser.add_argument('--market', default='')
    parser.add_argument('--company', default='')
    parser.add_argument('--message', required=True)
    parser.add_argument('--template', default=None)
    parser.add_argument('--channel', default='manual_zendesk')
    parser.add_argument('--notes', default=None)
    args = parser.parse_args()

    log_message(args.id, args.partner, args.campaign, args.market, args.company,
                args.message, args.template, args.channel, notes=args.notes)


if __name__ == '__main__':
    main()
