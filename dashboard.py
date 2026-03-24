#!/usr/bin/env python3
"""
Partner Outreach Dashboard — Streamlit app.

Run: streamlit run dashboard.py
"""

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta

import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "tracking", "outreach.db")
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_sync():
    """Run salesmsg_sync.py to pull new messages."""
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "salesmsg_sync.py")],
        capture_output=True, text=True, cwd=os.path.dirname(__file__)
    )
    return result.stdout + result.stderr


def send_via_salesmsg(conversation_id, message_text):
    """Send a reply via salesmsg_sync.py --send."""
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, "salesmsg_sync.py"),
         "--send", str(conversation_id), message_text],
        capture_output=True, text=True, cwd=os.path.dirname(__file__)
    )
    return result.returncode == 0, result.stdout + result.stderr


# ──────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Partner Outreach", page_icon="📱", layout="wide")
st.title("Partner Outreach Dashboard")

tab_query, tab_inbox, tab_convos, tab_metrics, tab_send = st.tabs(
    ["🔍 Query → Draft", "📥 Inbox", "💬 Conversations", "📊 Metrics", "✉️ Send"]
)


# ──────────────────────────────────────────────────────────────────────
# Sidebar: Sync controls
# ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Salesmsg Sync")

    if st.button("🔄 Sync Now", use_container_width=True):
        with st.spinner("Pulling from Salesmsg..."):
            output = run_sync()
        st.success("Sync complete")
        st.code(output, language="text")

    # Last sync info
    try:
        conn = get_db()
        sync_row = conn.execute(
            "SELECT * FROM salesmsg_sync ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if sync_row:
            st.caption(f"Last sync: {sync_row['last_sync_at']}")
            st.caption(f"Conversations: {sync_row['conversations_synced']} | Messages: {sync_row['messages_synced']}")
        conn.close()
    except Exception:
        st.caption("No sync history yet")

    st.divider()
    st.header("Quick Stats")
    try:
        conn = get_db()
        total_msgs = conn.execute("SELECT COUNT(*) FROM message_log").fetchone()[0]
        total_replies = conn.execute("SELECT COUNT(*) FROM reply_chain WHERE direction='inbound'").fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM reply_chain WHERE direction='inbound' AND response_approved=0"
        ).fetchone()[0]
        conn.close()
        st.metric("Total Outbound", total_msgs)
        st.metric("Total Inbound", total_replies)
        st.metric("Pending Review", pending)
    except Exception:
        pass

    if st.button("⟳ Refresh Dashboard", use_container_width=True):
        st.rerun()


# ──────────────────────────────────────────────────────────────────────
# Tab 0: Query → Draft — paste BQ SQL, run, draft messages, send
# ──────────────────────────────────────────────────────────────────────
with tab_query:
    st.header("Query → Draft → Send")
    st.caption("Paste a BQ query that returns partner_id, first_name, phone_number (and optionally last_name, company_name, market, distance_miles). Review results, draft messages, approve, and send.")

    # Load saved queries from a session or file
    SAVED_QUERIES_PATH = os.path.join(os.path.dirname(__file__), "stages", "01_identify", "queries")

    # Saved query selector
    saved_files = []
    if os.path.exists(SAVED_QUERIES_PATH):
        saved_files = [f for f in os.listdir(SAVED_QUERIES_PATH) if f.endswith(".sql")]

    col_saved, col_clear = st.columns([3, 1])
    with col_saved:
        saved_choice = st.selectbox(
            "Load a saved query",
            ["(paste your own)"] + sorted(saved_files),
            key="saved_query_select"
        )
    with col_clear:
        st.write("")  # spacing

    default_sql = ""
    if saved_choice != "(paste your own)":
        with open(os.path.join(SAVED_QUERIES_PATH, saved_choice)) as f:
            default_sql = f.read()

    sql_input = st.text_area(
        "BigQuery SQL",
        value=default_sql,
        height=200,
        placeholder="SELECT partner_id, first_name, last_name, phone_number, company_name, market, distance_miles FROM ...",
        key="bq_sql_input"
    )

    col_run, col_limit = st.columns([2, 1])
    with col_limit:
        row_limit = st.number_input("Max rows", value=50, min_value=1, max_value=500, step=10)

    # Run query
    with col_run:
        run_clicked = st.button("▶ Run Query", type="primary", disabled=not sql_input.strip())

    if run_clicked and sql_input.strip():
        with st.spinner("Running BigQuery..."):
            result = subprocess.run(
                ["bq", "query", "--use_legacy_sql=false", "--format=json", "--quiet",
                 f"--max_rows={row_limit}"],
                input=sql_input, capture_output=True, text=True
            )

        if result.returncode != 0:
            st.error(f"Query failed:\n{result.stderr}")
        else:
            try:
                rows = json.loads(result.stdout)
                st.session_state["query_results"] = rows
                st.success(f"Returned {len(rows)} partners")
            except json.JSONDecodeError:
                st.error(f"Could not parse results:\n{result.stdout[:500]}")

    # Show results + drafting
    if "query_results" in st.session_state and st.session_state["query_results"]:
        results = st.session_state["query_results"]

        st.divider()
        st.subheader(f"Results: {len(results)} partners")

        # Show as table
        import pandas as pd
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, height=300)

        # Message template
        st.divider()
        st.subheader("Draft Messages")

        # Load templates
        templates_dir = os.path.join(os.path.dirname(__file__), "_config", "message_templates")
        template_files = [f for f in os.listdir(templates_dir) if f.endswith(".md")] if os.path.exists(templates_dir) else []

        col_tmpl, col_custom = st.columns([1, 2])
        with col_tmpl:
            template_choice = st.selectbox("Template", ["(custom)"] + template_files, key="template_select")

        template_text = ""
        if template_choice != "(custom)" and template_choice:
            with open(os.path.join(templates_dir, template_choice)) as f:
                raw = f.read()
            # Extract the first ## Message section
            lines = raw.split("\n")
            in_message = False
            msg_lines = []
            for line in lines:
                if line.strip().startswith("## Message"):
                    in_message = True
                    continue
                elif line.strip().startswith("## ") and in_message:
                    break
                elif in_message:
                    msg_lines.append(line)
            template_text = "\n".join(msg_lines).strip()

        with col_custom:
            message_template = st.text_area(
                "Message template (use {first_name}, {company_name}, {market}, {distance_miles})",
                value=template_text,
                height=120,
                key="msg_template"
            )

        if message_template:
            # Generate previews
            st.divider()
            st.subheader("Preview & Approve")

            drafts = []
            for row in results:
                first = (row.get("first_name", "") or "").strip().title()
                company = row.get("company_name", "Shiftsmart")
                # Friendly company names
                company_display = company.replace("Circle K - Premium", "Circle K").replace("PepsiCo Beverages", "PepsiCo").replace("PepsiCo Foods", "Frito-Lay")
                market = row.get("market", row.get("msa", ""))
                distance = row.get("distance_miles", "")

                msg = message_template
                msg = msg.replace("{first_name}", first)
                msg = msg.replace("{company_name}", company_display)
                msg = msg.replace("{company}", company_display)
                msg = msg.replace("{market}", market or "your area")
                msg = msg.replace("{distance_miles}", str(distance) if distance else "nearby")

                drafts.append({
                    "partner_id": row.get("partner_id", ""),
                    "first_name": first,
                    "last_name": row.get("last_name", ""),
                    "phone": row.get("phone_number", ""),
                    "company": company,
                    "market": market,
                    "message": msg.strip()
                })

            # Show first few previews
            with st.expander(f"Preview ({min(5, len(drafts))} of {len(drafts)})", expanded=True):
                for d in drafts[:5]:
                    st.markdown(f"**{d['first_name']} {d['last_name']}** ({d['phone']}) — {d['market']}")
                    st.code(d["message"], language=None)
                    st.write("---")

            st.session_state["drafts"] = drafts

            # Campaign name for logging
            campaign_name = st.text_input("Campaign name (for tracking)", value="new_dl_orientation_push", key="campaign_name")

            col_approve_all, col_export, col_log = st.columns(3)

            with col_approve_all:
                if st.button(f"✅ Approve & Log All ({len(drafts)})", type="primary"):
                    conn = get_db()
                    logged = 0
                    for i, d in enumerate(drafts):
                        msg_id = f"{campaign_name}_{datetime.now().strftime('%Y%m%d')}_{i+1:04d}"
                        conn.execute("""
                            INSERT OR IGNORE INTO message_log
                            (message_id, partner_id, campaign_id, market, company,
                             channel, message_content, status)
                            VALUES (?, ?, ?, ?, ?, 'salesmsg', ?, 'approved')
                        """, (msg_id, d["partner_id"], campaign_name, d["market"],
                              d["company"], d["message"]))
                        logged += 1
                    conn.commit()
                    conn.close()
                    st.success(f"Logged {logged} messages to SQLite. Ready for Salesmsg broadcast.")

            with col_export:
                if st.button("📋 Export CSV"):
                    csv_lines = ["partner_id,first_name,last_name,phone_number,company,market,message"]
                    for d in drafts:
                        msg_escaped = d["message"].replace('"', '""')
                        csv_lines.append(f'{d["partner_id"]},{d["first_name"]},{d["last_name"]},{d["phone"]},{d["company"]},{d["market"]},"{msg_escaped}"')
                    csv_text = "\n".join(csv_lines)

                    export_path = os.path.join(os.path.dirname(__file__), "tracking", "exports",
                                               f"{campaign_name}_{datetime.now().strftime('%Y%m%d')}.csv")
                    os.makedirs(os.path.dirname(export_path), exist_ok=True)
                    with open(export_path, "w") as f:
                        f.write(csv_text)
                    st.success(f"Exported to {export_path}")
                    st.download_button("⬇ Download CSV", csv_text, file_name=f"{campaign_name}.csv", mime="text/csv")

            with col_log:
                st.caption(f"{len(drafts)} messages ready")


# ──────────────────────────────────────────────────────────────────────
# Tab 1: Inbox — pending inbound messages
# ──────────────────────────────────────────────────────────────────────
with tab_inbox:
    st.header("Pending Inbound Messages")

    conn = get_db()
    pending_rows = conn.execute("""
        SELECT r.reply_id, r.partner_id, r.content, r.logged_at,
               r.classified_intent, r.response_content, r.response_approved,
               r.requires_human, r.notes, r.parent_message_id
        FROM reply_chain r
        WHERE r.direction = 'inbound'
          AND r.response_approved = 0
        ORDER BY r.logged_at DESC
    """).fetchall()
    conn.close()

    if not pending_rows:
        st.info("No pending messages. Click **Sync Now** in the sidebar to check for new replies.")
    else:
        st.write(f"**{len(pending_rows)} messages** awaiting response")

        for row in pending_rows:
            notes = json.loads(row["notes"]) if row["notes"] else {}
            name = notes.get("partner_name", row["partner_id"])
            phone = notes.get("phone", "")
            conv_id = notes.get("salesmsg_conv_id", "")
            intent = row["classified_intent"] or "unclassified"
            draft = row["response_content"] or ""

            with st.expander(f"**{name}** ({phone}) — {row['content'][:80]}...", expanded=True):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Message:** {row['content']}")
                    st.caption(f"Time: {row['logged_at']} | Intent: {intent} | ID: {row['reply_id']}")

                with col2:
                    if row["requires_human"]:
                        st.warning("⚠️ Flagged for human review")

                st.divider()

                # Draft response area
                response_key = f"response_{row['reply_id']}"
                edited_response = st.text_area(
                    "Draft Response",
                    value=draft,
                    key=response_key,
                    height=100,
                    placeholder="Enter response or process in Claude Code first..."
                )

                col_approve, col_skip, col_escalate = st.columns(3)

                with col_approve:
                    if st.button("✅ Approve & Send", key=f"approve_{row['reply_id']}", type="primary",
                                 disabled=not edited_response or not conv_id):
                        # Send via Salesmsg
                        success, output = send_via_salesmsg(conv_id, edited_response)
                        if success:
                            # Update SQLite
                            conn = get_db()
                            conn.execute("""
                                UPDATE reply_chain
                                SET response_content = ?, response_approved = 1,
                                    classified_intent = ?
                                WHERE reply_id = ?
                            """, (edited_response, intent, row["reply_id"]))
                            # Log outbound reply
                            conn.execute("""
                                INSERT INTO reply_chain
                                (reply_id, parent_message_id, partner_id, direction,
                                 content, response_approved, logged_at, notes)
                                VALUES (?, ?, ?, 'outbound', ?, 1, datetime('now'), ?)
                            """, (
                                f"out_{row['reply_id']}",
                                row["parent_message_id"],
                                row["partner_id"],
                                edited_response,
                                json.dumps({"salesmsg_conv_id": conv_id})
                            ))
                            conn.commit()
                            conn.close()
                            st.success(f"Sent to {name}!")
                            st.rerun()
                        else:
                            st.error(f"Send failed: {output}")

                with col_skip:
                    if st.button("⏭️ Skip", key=f"skip_{row['reply_id']}"):
                        conn = get_db()
                        conn.execute(
                            "UPDATE reply_chain SET response_approved = -1 WHERE reply_id = ?",
                            (row["reply_id"],)
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()

                with col_escalate:
                    if st.button("🚨 Escalate", key=f"escalate_{row['reply_id']}"):
                        conn = get_db()
                        conn.execute(
                            "UPDATE reply_chain SET requires_human = 1 WHERE reply_id = ?",
                            (row["reply_id"],)
                        )
                        conn.commit()
                        conn.close()
                        st.warning("Flagged for human review")
                        st.rerun()


# ──────────────────────────────────────────────────────────────────────
# Tab 2: Conversations — full thread view
# ──────────────────────────────────────────────────────────────────────
with tab_convos:
    st.header("Partner Conversations")

    conn = get_db()
    partners = conn.execute("""
        SELECT pc.partner_id, pc.phone_number, pc.current_state,
               pc.last_message_at, pc.total_message_count
        FROM partner_conversations pc
        ORDER BY pc.last_message_at DESC NULLS LAST
        LIMIT 50
    """).fetchall()
    conn.close()

    if not partners:
        st.info("No conversations yet. Sync from Salesmsg to populate.")
    else:
        # Partner selector
        partner_options = {
            f"{p['phone_number'] or p['partner_id']} — state: {p['current_state']} ({p['total_message_count']} msgs)": p['partner_id']
            for p in partners
        }
        selected_label = st.selectbox("Select partner", list(partner_options.keys()))
        selected_partner = partner_options[selected_label]

        # Show conversation thread
        conn = get_db()
        messages = conn.execute("""
            SELECT reply_id, direction, content, classified_intent,
                   response_content, response_approved, logged_at, notes
            FROM reply_chain
            WHERE partner_id = ?
            ORDER BY logged_at ASC
        """, (selected_partner,)).fetchall()

        # Also get outbound messages from message_log
        outbound = conn.execute("""
            SELECT message_id, message_content, logged_at, campaign_id, status
            FROM message_log
            WHERE partner_id = ?
            ORDER BY logged_at ASC
        """, (selected_partner,)).fetchall()
        conn.close()

        # Merge and display chronologically
        all_msgs = []
        for m in messages:
            all_msgs.append({
                "time": m["logged_at"],
                "direction": m["direction"],
                "content": m["content"],
                "intent": m["classified_intent"],
                "source": "reply_chain"
            })
        for m in outbound:
            all_msgs.append({
                "time": m["logged_at"],
                "direction": "outbound",
                "content": m["message_content"],
                "intent": m["campaign_id"],
                "source": "message_log"
            })

        all_msgs.sort(key=lambda x: x["time"] or "")

        if not all_msgs:
            st.info("No messages for this partner yet.")
        else:
            for msg in all_msgs:
                if msg["direction"] == "inbound":
                    st.chat_message("user").write(f"{msg['content']}\n\n*{msg['time']}*")
                else:
                    st.chat_message("assistant").write(f"{msg['content']}\n\n*{msg['time']}*")


# ──────────────────────────────────────────────────────────────────────
# Tab 3: Metrics
# ──────────────────────────────────────────────────────────────────────
with tab_metrics:
    st.header("Campaign Metrics")

    days = st.slider("Time window (days)", 1, 30, 7)
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    conn = get_db()

    # Messages by campaign
    campaign_data = conn.execute("""
        SELECT campaign_id, status, COUNT(*) as count
        FROM message_log WHERE logged_at > ?
        GROUP BY campaign_id, status
        ORDER BY campaign_id
    """, (cutoff,)).fetchall()

    if campaign_data:
        st.subheader("Messages by Campaign")
        for r in campaign_data:
            st.write(f"**{r['campaign_id']}** — {r['status']}: {r['count']}")
    else:
        st.info("No outbound messages in this period.")

    # Top markets
    market_data = conn.execute("""
        SELECT market, COUNT(*) as count
        FROM message_log WHERE logged_at > ? AND market IS NOT NULL
        GROUP BY market ORDER BY count DESC LIMIT 10
    """, (cutoff,)).fetchall()

    if market_data:
        st.subheader("Top Markets")
        for r in market_data:
            st.write(f"**{r['market']}**: {r['count']} messages")

    # Reply stats
    st.subheader("Reply Stats")
    total_out = conn.execute(
        "SELECT COUNT(*) FROM message_log WHERE logged_at > ?", (cutoff,)
    ).fetchone()[0]
    total_in = conn.execute(
        "SELECT COUNT(*) FROM reply_chain WHERE direction='inbound' AND logged_at > ?", (cutoff,)
    ).fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Outbound", total_out)
    col2.metric("Inbound Replies", total_in)
    col3.metric("Reply Rate", f"{(total_in/total_out*100):.1f}%" if total_out > 0 else "N/A")

    # Intent breakdown
    intent_data = conn.execute("""
        SELECT classified_intent, COUNT(*) as count
        FROM reply_chain
        WHERE direction='inbound' AND logged_at > ?
        GROUP BY classified_intent ORDER BY count DESC
    """, (cutoff,)).fetchall()

    if intent_data:
        st.subheader("Reply Intents")
        for r in intent_data:
            intent = r["classified_intent"] or "unclassified"
            st.write(f"**{intent}**: {r['count']}")

    conn.close()


# ──────────────────────────────────────────────────────────────────────
# Tab 4: Send — manual compose
# ──────────────────────────────────────────────────────────────────────
with tab_send:
    st.header("Send Message")

    conn = get_db()
    partners = conn.execute("""
        SELECT partner_id, phone_number, current_state, notes
        FROM partner_conversations
        ORDER BY last_message_at DESC NULLS LAST
        LIMIT 50
    """).fetchall()
    conn.close()

    if not partners:
        st.info("No partners in the system yet. Sync from Salesmsg first.")
    else:
        # Get conversation IDs from notes in reply_chain
        conn = get_db()
        conv_map = {}
        for p in partners:
            row = conn.execute("""
                SELECT notes FROM reply_chain
                WHERE partner_id = ? AND notes IS NOT NULL
                ORDER BY logged_at DESC LIMIT 1
            """, (p["partner_id"],)).fetchone()
            if row and row["notes"]:
                try:
                    notes = json.loads(row["notes"])
                    conv_map[p["partner_id"]] = notes.get("salesmsg_conv_id", "")
                except (json.JSONDecodeError, TypeError):
                    pass
        conn.close()

        partner_options = {
            f"{p['phone_number'] or p['partner_id']} (state: {p['current_state']})": p["partner_id"]
            for p in partners
        }
        selected = st.selectbox("Select partner", list(partner_options.keys()), key="send_partner")
        partner_id = partner_options[selected]
        conv_id = conv_map.get(partner_id, "")

        message = st.text_area("Message", height=100, placeholder="Type your message...")

        if st.button("📤 Send via Salesmsg", type="primary", disabled=not message or not conv_id):
            success, output = send_via_salesmsg(conv_id, message)
            if success:
                # Log to message_log
                conn = get_db()
                msg_id = f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                conn.execute("""
                    INSERT INTO message_log
                    (message_id, partner_id, campaign_id, channel, message_content, status, sent_at)
                    VALUES (?, ?, 'manual_send', 'salesmsg', ?, 'sent', datetime('now'))
                """, (msg_id, partner_id, message))
                conn.commit()
                conn.close()
                st.success("Message sent!")
            else:
                st.error(f"Send failed: {output}")

        if not conv_id:
            st.warning("No Salesmsg conversation ID found for this partner. Sync first or select a partner who has replied.")
