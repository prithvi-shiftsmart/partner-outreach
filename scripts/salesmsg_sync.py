#!/usr/bin/env python3
"""
salesmsg_sync.py — Poll Salesmsg API for new messages and sync to SQLite.

Usage:
  python3 scripts/salesmsg_sync.py              # sync new messages
  python3 scripts/salesmsg_sync.py --send CONV_ID "message text"  # send a reply
  python3 scripts/salesmsg_sync.py --conversations  # list active conversations
"""

import argparse
import json
import os
import sqlite3
import sys
import time
import uuid
from datetime import datetime

import requests

from salesmsg_config import API_URL, HEADERS, DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("""CREATE TABLE IF NOT EXISTS salesmsg_sync (
        id INTEGER PRIMARY KEY,
        last_sync_at DATETIME,
        conversations_synced INTEGER DEFAULT 0,
        messages_synced INTEGER DEFAULT 0
    )""")
    conn.commit()
    return conn


def api_get(endpoint, params=None):
    url = f"{API_URL}/{endpoint}"
    resp = requests.get(url, headers=HEADERS, params=params or {})
    if resp.status_code == 429:
        print("[rate-limit] Hit 60 req/min limit. Waiting 60s...", file=sys.stderr)
        time.sleep(60)
        resp = requests.get(url, headers=HEADERS, params=params or {})
    resp.raise_for_status()
    return resp.json()


def api_post(endpoint, data):
    url = f"{API_URL}/{endpoint}"
    resp = requests.post(url, headers=HEADERS, json=data)
    if resp.status_code == 429:
        print("[rate-limit] Hit 60 req/min limit. Waiting 60s...", file=sys.stderr)
        time.sleep(60)
        resp = requests.post(url, headers=HEADERS, json=data)
    resp.raise_for_status()
    return resp.json()


def list_conversations():
    """List active conversations from Salesmsg (paginated)."""
    all_convs = []
    page = 1
    while True:
        data = api_get("conversations", {"filter": "open", "limit": 50, "page": page})
        convs = data.get("data", data) if isinstance(data, dict) else data
        if not convs or not isinstance(convs, list) or len(convs) == 0:
            break
        all_convs.extend(convs)
        if len(convs) < 50:
            break  # last page
        page += 1
        time.sleep(1)  # rate limit
    return all_convs


def get_messages(conversation_id, limit=20):
    """Get messages for a specific conversation."""
    data = api_get(f"messages/{conversation_id}", {"limit": limit})
    messages = data.get("data", data) if isinstance(data, dict) else data
    return messages


def send_reply(conversation_id, message_text, team_id=66423):
    """Send a reply to a conversation via Salesmsg API."""
    result = api_post(f"messages/{conversation_id}", {"message": message_text, "team_id": team_id})
    print(f"[sent] Reply to conversation {conversation_id}: {message_text[:60]}...")
    return result


def sync_inbound():
    """Pull new inbound messages from Salesmsg — only for conversations we initiated."""
    conn = get_db()

    # Get last sync time
    row = conn.execute("SELECT last_sync_at FROM salesmsg_sync ORDER BY id DESC LIMIT 1").fetchone()
    last_sync = row["last_sync_at"] if row else None

    # Get phone numbers of partners WE messaged (from message_log)
    our_partners = conn.execute("""
        SELECT DISTINCT pc.phone_number
        FROM partner_conversations pc
        WHERE pc.partner_id IN (SELECT DISTINCT partner_id FROM message_log)
          AND pc.phone_number IS NOT NULL
    """).fetchall()
    our_phones = set(r["phone_number"] for r in our_partners)

    if not our_phones:
        print(f"[sync] No outbound conversations to sync. Send messages first.")
        conn.execute(
            "INSERT INTO salesmsg_sync (last_sync_at, conversations_synced, messages_synced) VALUES (datetime('now'), 0, 0)"
        )
        conn.commit()
        conn.close()
        return 0

    print(f"[sync] Last sync: {last_sync or 'never'} | Tracking {len(our_phones)} conversations")

    # Page through conversations but only process ones matching our phone numbers.
    # Stop after 3 consecutive pages with zero matches (we've passed our conversations).
    total_new = 0
    conv_count = 0
    empty_pages = 0
    page = 1
    conversations = []

    while empty_pages < 3:
        data = api_get("conversations", {"filter": "open", "limit": 50, "page": page})
        page_convs = data.get("data", data) if isinstance(data, dict) else data
        if not page_convs or not isinstance(page_convs, list) or len(page_convs) == 0:
            break

        matched = 0
        for conv in page_convs:
            contact = conv.get("contact", {})
            phone = contact.get("number", "") or contact.get("phone", "")
            if phone in our_phones:
                conversations.append(conv)
                matched += 1

        print(f"  Page {page}: {len(page_convs)} convos, {matched} matched")
        if matched == 0:
            empty_pages += 1
        else:
            empty_pages = 0

        if len(page_convs) < 50:
            break
        page += 1
        time.sleep(0.5)

    print(f"[sync] Found {len(conversations)} matching conversations across {page} pages")

    for conv in conversations:
        conv_id = str(conv.get("id", ""))
        if not conv_id:
            continue

        contact = conv.get("contact", {})
        phone = contact.get("number", "") or contact.get("phone", "") or conv.get("number", "")
        name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() or phone

        # Only sync conversations with partners WE messaged
        if phone not in our_phones:
            continue

        messages = get_messages(conv_id)
        if not isinstance(messages, list):
            messages = [messages] if messages else []

        for msg in messages:
            msg_id = str(msg.get("id", ""))
            # Salesmsg uses status: "received" for inbound, "sent"/"delivered" for outbound
            msg_status = msg.get("status", "")
            direction = "inbound" if msg_status == "received" else "outbound"
            # Prefer body_raw (plain text) over body (may contain HTML)
            content = msg.get("body_raw", "") or msg.get("body", "")
            # Strip HTML tags (e.g. <br>, <p>, &nbsp;)
            import re
            content = re.sub(r'<br\s*/?>', '\n', content)
            content = re.sub(r'<[^>]+>', '', content)
            content = content.replace('&nbsp;', ' ').replace('&amp;', '&')
            content = re.sub(r'\n{3,}', '\n\n', content).strip()
            created = msg.get("created_at", "")

            if not msg_id or not content:
                continue

            # Skip if we already have this message
            existing = conn.execute(
                "SELECT 1 FROM reply_chain WHERE reply_id = ?", (f"sm_{msg_id}",)
            ).fetchone()
            if existing:
                continue

            # Skip outbound messages we sent (only ingest inbound for processing)
            if direction != "inbound":
                continue

            # Find or create partner conversation
            partner_row = conn.execute(
                "SELECT partner_id FROM partner_conversations WHERE phone_number = ?", (phone,)
            ).fetchone()

            if partner_row:
                partner_id = partner_row["partner_id"]
            else:
                partner_id = f"sm_{phone}"
                conn.execute(
                    """INSERT OR IGNORE INTO partner_conversations
                       (partner_id, phone_number, current_state, channel)
                       VALUES (?, ?, 'answering_qs', 'sms')""",
                    (partner_id, phone)
                )

            # Log inbound message
            conn.execute(
                """INSERT OR IGNORE INTO reply_chain
                   (reply_id, parent_message_id, partner_id, direction, content,
                    logged_at, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f"sm_{msg_id}", f"conv_{conv_id}", partner_id, "inbound",
                 content, created or datetime.now().isoformat(),
                 json.dumps({"salesmsg_conv_id": conv_id, "partner_name": name, "phone": phone}))
            )

            # Auto-detect opt-out / abuse / wrong number → flag do_not_message
            dnm_reason = None
            content_lower = content.strip()
            import re as _re
            # Opt-out patterns
            if (_re.search(r'(?i)^\s*s+t+o+p+\s*[.!]*\s*$', content_lower)
                    or _re.search(r'(?i)\bunsubscribe\b', content_lower)
                    or _re.search(r'(?i)\bstop (texting|messaging|contacting)\b', content_lower)
                    or _re.search(r'(?i)\bremove me\b', content_lower)
                    or _re.search(r'(?i)\bopt.?out\b', content_lower)
                    or _re.search(r'(?i)\bdon\'?t (text|message|contact) me\b', content_lower)
                    or _re.search(r'(?i)\btake me off\b', content_lower)
                    or _re.search(r'(?i)\bdelete my number\b', content_lower)):
                dnm_reason = "opt_out"
            # Abuse patterns
            elif (_re.search(r'(?i)\bf+u+c+k+', content_lower)
                    or _re.search(r'(?i)\ba+s+s+h+o+l+e', content_lower)
                    or _re.search(r'(?i)\bb+i+t+c+h', content_lower)):
                dnm_reason = "antagonistic"
            # Wrong number patterns
            elif (_re.search(r'(?i)wrong number', content_lower)
                    or _re.search(r'(?i)you have the wrong', content_lower)):
                dnm_reason = "wrong_number"

            if dnm_reason:
                conn.execute(
                    """UPDATE partner_conversations
                       SET do_not_message = 1, dnm_reason = ?, dnm_at = datetime('now'),
                           updated_at = datetime('now')
                       WHERE partner_id = ?""",
                    (dnm_reason, partner_id)
                )
                print(f"  ⚠ Flagged {partner_id} as {dnm_reason}: {content[:50]}")

            # Update partner conversation
            conn.execute(
                """UPDATE partner_conversations
                   SET last_message_at = ?, total_message_count = total_message_count + 1,
                       updated_at = datetime('now')
                   WHERE partner_id = ?""",
                (created or datetime.now().isoformat(), partner_id)
            )

            total_new += 1

        conv_count += 1
        # Rate limit awareness: don't hammer the API
        if conv_count % 10 == 0:
            time.sleep(1)

    # Log sync
    conn.execute(
        "INSERT INTO salesmsg_sync (last_sync_at, conversations_synced, messages_synced) VALUES (datetime('now'), ?, ?)",
        (conv_count, total_new)
    )
    conn.commit()
    conn.close()

    print(f"[sync] Done. {conv_count} conversations checked, {total_new} new inbound messages.")
    return total_new


def show_pending():
    """Show inbound messages that haven't been responded to."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT r.reply_id, r.partner_id, r.content, r.logged_at, r.classified_intent,
               r.response_content, r.response_approved, r.notes
        FROM reply_chain r
        WHERE r.direction = 'inbound'
          AND r.response_approved = 0
          AND r.requires_human = 0
        ORDER BY r.logged_at DESC
        LIMIT 20
    """).fetchall()

    if not rows:
        print("No pending inbound messages.")
    else:
        print(f"\n{'='*60}")
        print(f"  PENDING INBOUND MESSAGES ({len(rows)})")
        print(f"{'='*60}")
        for r in rows:
            notes = json.loads(r["notes"]) if r["notes"] else {}
            name = notes.get("partner_name", r["partner_id"])
            phone = notes.get("phone", "")
            draft = r["response_content"] or "(no draft yet)"
            intent = r["classified_intent"] or "unclassified"
            print(f"\n  [{r['reply_id']}]")
            print(f"  From: {name} ({phone})")
            print(f"  Time: {r['logged_at']}")
            print(f"  Message: {r['content']}")
            print(f"  Intent: {intent}")
            print(f"  Draft: {draft}")
            print(f"  ---")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Salesmsg sync")
    parser.add_argument("--send", nargs=2, metavar=("CONV_ID", "MESSAGE"), help="Send a reply")
    parser.add_argument("--conversations", action="store_true", help="List conversations")
    parser.add_argument("--pending", action="store_true", help="Show pending inbound messages")
    args = parser.parse_args()

    if not HEADERS["Authorization"] or HEADERS["Authorization"] == "Bearer " or HEADERS["Authorization"] == "Bearer your_token_here":
        print("[error] Set SALESMSG_API_TOKEN in .env file first.", file=sys.stderr)
        sys.exit(1)

    if args.send:
        conv_id, message = args.send
        send_reply(conv_id, message)
    elif args.conversations:
        convs = list_conversations()
        print(json.dumps(convs, indent=2, default=str))
    elif args.pending:
        show_pending()
    else:
        sync_inbound()


if __name__ == "__main__":
    main()
