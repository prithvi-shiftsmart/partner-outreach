#!/usr/bin/env python3
"""
export_broadcast_replies.py — Export full conversation histories from Salesmsg broadcasts.

Targets broadcasts from the last N days with >N replies.
For each qualifying broadcast, finds contacts who replied (not opt-outs),
pulls their full conversation history, and exports to CSV.

API notes (discovered 2026-03-26):
  - GET /broadcasts returns paginated list (10/page) with all_statistics.reply_count
  - GET /contacts?broadcast_id=X returns contacts for a broadcast (10/page)
  - GET /conversations?filter=open&contact_id=X returns conversation for a contact
  - GET /messages/{conversation_id} returns messages (source=broadcast for broadcast msgs)
  - Rate limit: 60 req/min

Usage:
  python3 scripts/export_broadcast_replies.py                   # defaults (14 days, 20 min replies)
  python3 scripts/export_broadcast_replies.py --days 14 --min-replies 20
  python3 scripts/export_broadcast_replies.py --dry-run         # show qualifying broadcasts without pulling conversations
  python3 scripts/export_broadcast_replies.py --types orientation,outreach,activation  # filter by broadcast type
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta

import requests

from salesmsg_config import API_URL, HEADERS

OUTPUT_DIR = os.path.expanduser(
    "~/Documents/Obsidian/PK ShiftSmart/Projects/Partner Outreach Platform"
)

# Opt-out patterns — if the FIRST inbound reply matches, skip the conversation
OPT_OUT_PATTERNS = [
    r"(?i)^\s*stop\s*[.!]*\s*$",
    r"(?i)^\s*s\s*t\s*o\s*p\s*$",
    r"(?i)\bunsubscribe\b",
    r"(?i)\bstop (texting|messaging|contacting|sending)\b",
    r"(?i)\bremove me\b",
    r"(?i)\bopt.?out\b",
    r"(?i)^\s*cancel\s*$",
    r"(?i)^\s*quit\s*$",
    r"(?i)^\s*end\s*$",
    r"(?i)\bdon'?t (text|message|contact) me\b",
    r"(?i)\bplease.{0,10}stop\b",
    r"(?i)\bleave me alone\b",
    r"(?i)\btake me off\b",
]

# Broadcast type classification — match broadcast name patterns to categories
BROADCAST_TYPES = {
    "orientation": [
        r"(?i)orientation",
        r"(?i)remote.*orientation",
        r"(?i)OA\b",
        r"(?i)remote.*last.*push",
        r"(?i)first.*shift.*req",
    ],
    "outreach": [
        r"(?i)OP\s*>\s*S1C",
        r"(?i)manual\s*outreach",
        r"(?i)steady\s*state",
        r"(?i)no\s*show",
        r"(?i)low\s*work\s*quality",
        r"(?i)unacceptable",
        r"(?i)mid\s*fill",
        r"(?i)fill\s*rate",
        r"(?i)\bfill\b",
    ],
    "activation": [
        r"(?i)dxgy",
        r"(?i)d[0-9]+g[0-9]+",
        r"(?i)scintilla",
        r"(?i)activation",
        r"(?i)unclaimed",
        r"(?i)reinstall",
        r"(?i)launch",
    ],
}


def classify_broadcast(name):
    """Classify a broadcast by name into one or more types."""
    types = []
    for btype, patterns in BROADCAST_TYPES.items():
        if any(re.search(p, name) for p in patterns):
            types.append(btype)
    return types if types else ["other"]


# Track API calls for reporting
_api_call_count = 0


def api_get(endpoint, params=None):
    """GET request with rate-limit handling and call counting."""
    global _api_call_count
    _api_call_count += 1

    url = f"{API_URL}/{endpoint}"
    try:
        resp = requests.get(url, headers=HEADERS, params=params or {}, timeout=30)
    except requests.exceptions.Timeout:
        print(f"  [timeout] {endpoint}", file=sys.stderr)
        return None

    if resp.status_code == 429:
        print("[rate-limit] Waiting 60s...", file=sys.stderr)
        time.sleep(60)
        resp = requests.get(url, headers=HEADERS, params=params or {}, timeout=30)
    if resp.status_code in (404, 405):
        return None
    if resp.status_code >= 500:
        # Server error — wait and retry once
        print(f"  [server-error] {resp.status_code} on {endpoint}. Retrying in 5s...", file=sys.stderr)
        time.sleep(5)
        resp = requests.get(url, headers=HEADERS, params=params or {}, timeout=30)
        if resp.status_code >= 500:
            print(f"  [server-error] {resp.status_code} on {endpoint} again. Skipping.", file=sys.stderr)
            return None
    resp.raise_for_status()
    return resp.json()


def parse_items(result):
    """Extract list of items from API response (handles both list and dict formats)."""
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        data = result.get("data", [])
        return data if isinstance(data, list) else [data] if data else []
    return []


def is_opt_out(text):
    """Check if a message matches opt-out patterns."""
    if not text:
        return False
    return any(re.search(p, text.strip()) for p in OPT_OUT_PATTERNS)


def strip_html(text):
    """Clean HTML from message body."""
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def get_qualifying_broadcasts(days=14, min_replies=20, types=None):
    """Fetch broadcasts from the last N days with >= min_replies, optionally filtered by type."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00")

    qualifying = []
    skipped_type = 0
    page = 1
    total_scanned = 0

    while True:
        result = api_get("broadcasts", {"limit": 10, "page": page})
        items = parse_items(result)

        if not items:
            break

        past_cutoff = False
        for b in items:
            sent = b.get("sent_at") or b.get("created_at") or ""
            if sent and sent < cutoff:
                past_cutoff = True
                break

            stats = b.get("all_statistics", {})
            reply_count = stats.get("reply_count", 0)
            opt_out_count = stats.get("opt_out_count", 0)
            contacts_count = b.get("contacts_count", 0)
            name = b.get("name", f"Broadcast {b.get('id', '?')}")

            total_scanned += 1

            if reply_count < min_replies:
                continue

            # Classify and filter by type
            bc_types = classify_broadcast(name)
            if types and not any(t in types for t in bc_types):
                skipped_type += 1
                continue

            qualifying.append({
                "id": b["id"],
                "name": name,
                "message": b.get("message", ""),
                "sent_at": sent,
                "reply_count": reply_count,
                "opt_out_count": opt_out_count,
                "contacts_count": contacts_count,
                "types": bc_types,
            })

        if past_cutoff:
            break

        page += 1
        time.sleep(0.3)

    type_str = f", types={types}" if types else ""
    print(f"[broadcasts] Scanned {total_scanned} broadcasts, {len(qualifying)} qualify (>={min_replies} replies{type_str})")
    if skipped_type:
        print(f"[broadcasts] {skipped_type} broadcasts had enough replies but didn't match type filter")
    return qualifying


def get_broadcast_repliers(broadcast_id, expected_replies):
    """Get contacts who replied to a broadcast by paginating through broadcast contacts.

    Only returns contacts where total_received_sms > 0 (i.e., they sent at least one message).
    Stops early once we've found the expected number of repliers.
    """
    repliers = []
    page = 1
    pages_scanned = 0

    while True:
        result = api_get("contacts", {"broadcast_id": broadcast_id, "limit": 10, "page": page})
        items = parse_items(result)

        if not items:
            break

        pages_scanned += 1

        for contact in items:
            total_recv = contact.get("total_received_sms", 0) or 0
            if total_recv > 0:
                repliers.append({
                    "id": contact.get("id"),
                    "name": contact.get("full_name", "").strip()
                        or f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                    "number": contact.get("number", ""),
                    "opt_out": contact.get("opt_out"),
                })

        # Early exit: if we've found all expected repliers (with margin for opt-outs)
        if len(repliers) >= expected_replies * 1.5:
            break

        page += 1

        # Rate-limit awareness: pause every 50 pages
        if pages_scanned % 50 == 0:
            print(f"    Scanned {pages_scanned} pages, found {len(repliers)} repliers so far...")
            time.sleep(1)
        else:
            time.sleep(0.2)

    return repliers, pages_scanned


def get_conversation_for_contact(contact_id):
    """Get the conversation for a contact. Tries open, then closed."""
    for filter_type in ["open", "closed"]:
        result = api_get("conversations", {"filter": filter_type, "contact_id": contact_id, "limit": 1})
        items = parse_items(result)
        if items:
            return items[0]
        time.sleep(0.2)
    return None


def get_conversation_messages(conversation_id, max_pages=20):
    """Get messages in a conversation, paginated. Caps at max_pages to avoid mega-conversations."""
    all_messages = []
    page = 1

    while page <= max_pages:
        try:
            result = api_get(f"messages/{conversation_id}", {"limit": 50, "page": page})
        except Exception as e:
            print(f"    [warn] Error fetching messages page {page} for conv {conversation_id}: {e}", file=sys.stderr)
            break

        items = parse_items(result)

        if not items:
            break

        all_messages.extend(items)

        # If we got fewer than limit, we're done
        if len(items) < 50:
            break

        page += 1
        time.sleep(0.3)

    return all_messages


def parse_messages(raw_messages):
    """Parse raw API messages into clean dicts, sorted by timestamp."""
    parsed = []
    for msg in raw_messages:
        status = msg.get("status", "")
        direction = "inbound" if status == "received" else "outbound"
        content = strip_html(msg.get("body_raw", "") or msg.get("body", ""))
        timestamp = msg.get("created_at", "")
        source = msg.get("source", "")
        source_id = msg.get("source_id")

        # Skip empty messages and call records
        if not content or msg.get("type") == "call":
            continue

        parsed.append({
            "direction": direction,
            "content": content,
            "timestamp": timestamp,
            "source": source,
            "source_id": source_id,
        })

    parsed.sort(key=lambda m: m.get("timestamp", ""))
    return parsed


def export_conversations(days=14, min_replies=20, dry_run=False, types=None):
    """Main export flow."""
    global _api_call_count
    start_time = time.time()

    # Step 1: Get qualifying broadcasts
    qualifying = get_qualifying_broadcasts(days=days, min_replies=min_replies, types=types)

    if not qualifying:
        print("[export] No qualifying broadcasts found.")
        return

    # Show qualifying broadcasts
    print(f"\n{'='*80}")
    print(f"  QUALIFYING BROADCASTS ({len(qualifying)})")
    print(f"{'='*80}")
    for bc in qualifying:
        type_tags = ",".join(bc.get("types", ["other"]))
        print(f"  [{bc['id']}] {bc['name'][:45]:45s} | {type_tags:20s} | {bc['reply_count']:3d} replies | {bc['contacts_count']:5d} contacts | {bc['sent_at'][:10] if bc['sent_at'] else 'no date'}")
    print()

    if dry_run:
        total_contacts = sum(bc["contacts_count"] for bc in qualifying)
        est_pages = total_contacts // 10
        print(f"[dry-run] Would scan ~{est_pages} contact pages + conversation lookups")
        print(f"[dry-run] Estimated API calls: ~{est_pages + sum(bc['reply_count'] for bc in qualifying) * 3}")
        return

    # Step 2: For each broadcast, find repliers and pull conversations
    all_rows = []
    total_contacts_exported = 0
    total_optouts_skipped = 0
    total_pages_scanned = 0

    for i, bc in enumerate(qualifying, 1):
        print(f"\n[{i}/{len(qualifying)}] {bc['name']} ({bc['reply_count']} replies, {bc['contacts_count']} contacts)...")

        # Get contacts who replied
        repliers, pages = get_broadcast_repliers(bc["id"], bc["reply_count"])
        total_pages_scanned += pages
        print(f"  Found {len(repliers)} repliers ({pages} pages scanned)")

        if not repliers:
            continue

        # For each replier, get full conversation history
        for j, replier in enumerate(repliers, 1):
            try:
                # Skip if contact opted out via Salesmsg
                if replier.get("opt_out"):
                    total_optouts_skipped += 1
                    continue

                # Get conversation
                conv = get_conversation_for_contact(replier["id"])
                if not conv:
                    continue

                conv_id = conv.get("id")
                if not conv_id:
                    continue

                # Get messages (capped at 20 pages = 1000 messages max)
                raw_messages = get_conversation_messages(conv_id)
                if not raw_messages:
                    continue

                messages = parse_messages(raw_messages)

                # Find first inbound message — check if it's an opt-out
                first_inbound = next((m for m in messages if m["direction"] == "inbound"), None)
                if first_inbound and is_opt_out(first_inbound["content"]):
                    total_optouts_skipped += 1
                    continue

                # If no inbound at all, skip (shouldn't happen but defensive)
                if not first_inbound:
                    continue

                # Add all messages to export
                for order, msg in enumerate(messages, 1):
                    all_rows.append({
                        "broadcast_id": bc["id"],
                        "broadcast_name": bc["name"],
                        "broadcast_date": bc["sent_at"][:10] if bc["sent_at"] else "",
                        "broadcast_message": bc["message"][:200],
                        "contact_name": replier["name"],
                        "contact_phone": replier["number"],
                        "conversation_id": conv_id,
                        "message_direction": msg["direction"],
                        "message_content": msg["content"],
                        "message_timestamp": msg["timestamp"],
                        "message_source": msg["source"],
                        "message_order": order,
                    })

                total_contacts_exported += 1

            except Exception as e:
                print(f"    [error] Failed on contact {replier.get('name', replier.get('id', '?'))}: {e}", file=sys.stderr)
                continue

            # Progress
            if j % 10 == 0:
                print(f"    Processed {j}/{len(repliers)} repliers...")
            time.sleep(0.3)

        print(f"  Done: {total_contacts_exported} total exported, {total_optouts_skipped} opt-outs skipped")

    # Step 3: Write CSV
    if not all_rows:
        print("\n[export] No conversations to export.")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(OUTPUT_DIR, f"Broadcast_Reply_Conversations_{date_str}.csv")

    fieldnames = [
        "broadcast_id",
        "broadcast_name",
        "broadcast_date",
        "broadcast_message",
        "contact_name",
        "contact_phone",
        "conversation_id",
        "message_direction",
        "message_content",
        "message_timestamp",
        "message_source",
        "message_order",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  EXPORT COMPLETE")
    print(f"{'='*60}")
    print(f"  Broadcasts processed:   {len(qualifying)}")
    print(f"  Contacts exported:      {total_contacts_exported}")
    print(f"  Opt-outs skipped:       {total_optouts_skipped}")
    print(f"  Total message rows:     {len(all_rows)}")
    print(f"  Contact pages scanned:  {total_pages_scanned}")
    print(f"  Total API calls:        {_api_call_count}")
    print(f"  Time elapsed:           {elapsed/60:.1f} minutes")
    print(f"  Output: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Export broadcast reply conversations from Salesmsg")
    parser.add_argument("--days", type=int, default=14, help="Look back N days (default: 14)")
    parser.add_argument("--min-replies", type=int, default=20, help="Min reply count to qualify (default: 20)")
    parser.add_argument("--types", type=str, default=None,
                        help="Comma-separated broadcast types to include: orientation,outreach,activation (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Show qualifying broadcasts without pulling conversations")
    args = parser.parse_args()

    if not HEADERS["Authorization"] or HEADERS["Authorization"] in ("Bearer ", "Bearer your_token_here"):
        print("[error] Set SALESMSG_API_TOKEN in .env file first.", file=sys.stderr)
        sys.exit(1)

    types = [t.strip() for t in args.types.split(",")] if args.types else None
    export_conversations(days=args.days, min_replies=args.min_replies, dry_run=args.dry_run, types=types)


if __name__ == "__main__":
    main()
