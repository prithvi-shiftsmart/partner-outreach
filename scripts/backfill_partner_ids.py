#!/usr/bin/env python3
"""
Backfill real BQ partner UUIDs for records that have sm_{phone} as partner_id.

1. Finds all partner_conversations with sm_ prefix
2. Looks up real partner_id from BQ by phone number
3. Updates partner_conversations, message_log, and reply_chain
"""

import sqlite3
import subprocess
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "tracking", "outreach.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def main():
    conn = get_db()

    # Find all sm_ partner_ids with phone numbers
    sm_rows = conn.execute("""
        SELECT partner_id, phone_number
        FROM partner_conversations
        WHERE partner_id LIKE 'sm_%' AND phone_number IS NOT NULL
    """).fetchall()

    if not sm_rows:
        print("No sm_ partner_ids to backfill.")
        return

    print(f"Found {len(sm_rows)} partners to backfill.")

    # Extract phone numbers for BQ lookup
    phones = [r["phone_number"] for r in sm_rows]
    phone_to_sm = {r["phone_number"]: r["partner_id"] for r in sm_rows}

    # Build BQ query to resolve phone -> partner_id
    phone_list = ", ".join(f"'{p}'" for p in phones)
    sql = f"""
        SELECT user_id, phone_number
        FROM `shiftsmart-api.bi.fct_partner_assessment_status`
        WHERE phone_number IN ({phone_list})
        QUALIFY ROW_NUMBER() OVER (PARTITION BY phone_number ORDER BY last_active_at DESC) = 1
    """

    print("Querying BQ for real partner IDs...")
    result = subprocess.run(
        ["bq", "query", "--use_legacy_sql=false", "--format=json", "--quiet"],
        input=sql, capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"BQ query failed: {result.stderr}")
        return

    try:
        bq_rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Could not parse BQ results: {result.stdout[:500]}")
        return

    print(f"BQ returned {len(bq_rows)} matches.")

    updated = 0
    for row in bq_rows:
        real_id = row["user_id"]
        phone = row["phone_number"]
        sm_id = phone_to_sm.get(phone)

        if not sm_id:
            continue

        print(f"  {sm_id} -> {real_id} ({phone})")

        # Update partner_conversations
        conn.execute("UPDATE partner_conversations SET partner_id = ? WHERE partner_id = ?", (real_id, sm_id))

        # Update message_log
        conn.execute("UPDATE message_log SET partner_id = ? WHERE partner_id = ?", (real_id, sm_id))

        # Update reply_chain
        conn.execute("UPDATE reply_chain SET partner_id = ? WHERE partner_id = ?", (real_id, sm_id))

        updated += 1

    conn.commit()
    conn.close()
    print(f"\nBackfilled {updated}/{len(sm_rows)} partners.")

    not_found = len(sm_rows) - updated
    if not_found:
        print(f"{not_found} partners had no BQ match (phone not in fct_partner_assessment_status).")

if __name__ == "__main__":
    main()
