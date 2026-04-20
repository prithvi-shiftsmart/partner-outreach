"""SQLite database connection and migrations."""

import json
import sqlite3
from contextlib import contextmanager

from server.config import DB_PATH


@contextmanager
def get_db():
    """Context manager for database connections with WAL mode."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
    finally:
        conn.close()


def _column_exists(conn, table, column):
    """Check if a column exists in a table."""
    cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    return column in cols


def _table_exists(conn, table):
    """Check if a table exists."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def run_migrations():
    """Run all schema migrations. Idempotent — safe to call on every startup."""
    with get_db() as conn:
        # -- partner_conversations: first-class partner fields --
        for col, col_type in [
            ("first_name", "TEXT"),
            ("last_name", "TEXT"),
            ("market", "TEXT"),
            ("bq_partner_id", "TEXT"),
            ("excluded_campaigns", "TEXT"),
        ]:
            if not _column_exists(conn, "partner_conversations", col):
                conn.execute(f"ALTER TABLE partner_conversations ADD COLUMN {col} {col_type}")

        # -- reply_chain: MMS + auto-draft --
        for col, col_type in [
            ("media_urls", "TEXT"),
            ("draft_status", "TEXT"),
            ("draft_content", "TEXT"),
        ]:
            if not _column_exists(conn, "reply_chain", col):
                conn.execute(f"ALTER TABLE reply_chain ADD COLUMN {col} {col_type}")

        # -- campaign_context: per-campaign auto-respond --
        conn.execute("""
            CREATE TABLE IF NOT EXISTS campaign_context (
                campaign_id TEXT PRIMARY KEY,
                context TEXT,
                auto_respond_enabled INTEGER DEFAULT 0,
                updated_at DATETIME DEFAULT (datetime('now'))
            )
        """)
        if not _column_exists(conn, "campaign_context", "auto_respond_enabled"):
            conn.execute(
                "ALTER TABLE campaign_context ADD COLUMN auto_respond_enabled INTEGER DEFAULT 0"
            )

        # -- salesmsg_sync: better tracking --
        for col, col_type in [
            ("pages_scanned", "INTEGER DEFAULT 0"),
            ("mode", "TEXT DEFAULT 'quick'"),
            ("duration_seconds", "REAL"),
        ]:
            col_name = col.split()[0]
            if not _column_exists(conn, "salesmsg_sync", col_name):
                conn.execute(f"ALTER TABLE salesmsg_sync ADD COLUMN {col} {col_type}")

        # -- app_settings table --
        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT (datetime('now'))
            )
        """)

        # -- Performance indexes --
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reply_direction_logged ON reply_chain(direction, logged_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_campaign_logged ON message_log(campaign_id, logged_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_bq_pid ON partner_conversations(bq_partner_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_dnm ON partner_conversations(do_not_message)")

        conn.commit()


def backfill_partner_fields():
    """One-time backfill: populate first_name, last_name, market, bq_partner_id
    from notes JSON in message_log and reply_chain."""
    with get_db() as conn:
        # From message_log notes
        rows = conn.execute("""
            SELECT DISTINCT ml.partner_id, ml.notes, ml.market
            FROM message_log ml
            WHERE ml.notes IS NOT NULL
            AND ml.partner_id IN (
                SELECT partner_id FROM partner_conversations WHERE first_name IS NULL
            )
        """).fetchall()

        for row in rows:
            try:
                notes = json.loads(row["notes"])
            except (json.JSONDecodeError, TypeError):
                continue
            first_name = notes.get("first_name") or None
            last_name = notes.get("last_name") or None
            bq_pid = notes.get("bq_partner_id") or None
            market = row["market"] or None
            if first_name or last_name or bq_pid or market:
                conn.execute("""
                    UPDATE partner_conversations
                    SET first_name = COALESCE(first_name, ?),
                        last_name = COALESCE(last_name, ?),
                        market = COALESCE(market, ?),
                        bq_partner_id = COALESCE(bq_partner_id, ?)
                    WHERE partner_id = ?
                """, (first_name, last_name, market, bq_pid, row["partner_id"]))

        # From reply_chain notes (has partner_name as "First Last")
        rows2 = conn.execute("""
            SELECT DISTINCT rc.partner_id, rc.notes
            FROM reply_chain rc
            WHERE rc.notes IS NOT NULL
            AND rc.partner_id IN (
                SELECT partner_id FROM partner_conversations WHERE first_name IS NULL
            )
        """).fetchall()

        for row in rows2:
            try:
                notes = json.loads(row["notes"])
            except (json.JSONDecodeError, TypeError):
                continue
            name = notes.get("partner_name", "")
            if name and name != "None None":
                parts = name.split(" ", 1)
                first_name = parts[0] if parts[0] != "None" else None
                last_name = parts[1] if len(parts) > 1 and parts[1] != "None" else None
                if first_name or last_name:
                    conn.execute("""
                        UPDATE partner_conversations
                        SET first_name = COALESCE(first_name, ?),
                            last_name = COALESCE(last_name, ?)
                        WHERE partner_id = ?
                    """, (first_name, last_name, row["partner_id"]))

        conn.commit()
