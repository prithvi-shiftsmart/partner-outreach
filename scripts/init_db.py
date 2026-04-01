#!/usr/bin/env python3
"""
init_db.py — Create the outreach.db SQLite schema.
Run once: python3 scripts/init_db.py
Safe to re-run: uses CREATE TABLE IF NOT EXISTS.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'tracking', 'outreach.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS message_log (
    message_id      TEXT PRIMARY KEY,
    partner_id      TEXT NOT NULL,
    campaign_id     TEXT NOT NULL,
    template_version TEXT,
    market          TEXT,
    company         TEXT,
    channel         TEXT DEFAULT 'manual_zendesk',
    message_content TEXT NOT NULL,
    status          TEXT DEFAULT 'approved',
    logged_at       DATETIME DEFAULT (datetime('now')),
    sent_at         DATETIME,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS reply_chain (
    reply_id        TEXT PRIMARY KEY,
    parent_message_id TEXT,
    partner_id      TEXT NOT NULL,
    direction       TEXT,
    content         TEXT NOT NULL,
    classified_intent TEXT,
    confidence      TEXT,
    response_content TEXT,
    response_approved INTEGER DEFAULT 0,
    requires_human  INTEGER DEFAULT 0,
    logged_at       DATETIME DEFAULT (datetime('now')),
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS outcome_events (
    event_id        TEXT PRIMARY KEY,
    partner_id      TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    event_at        DATETIME,
    attributed_message_id TEXT,
    market          TEXT,
    company         TEXT,
    logged_at       DATETIME DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ab_tests (
    test_id         TEXT PRIMARY KEY,
    campaign_id     TEXT NOT NULL,
    description     TEXT,
    variant_a       TEXT,
    variant_b       TEXT,
    start_date      DATE,
    end_date        DATE,
    winner          TEXT,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS partner_context (
    snapshot_id     TEXT PRIMARY KEY,
    partner_id      TEXT NOT NULL,
    market          TEXT,
    company         TEXT,
    funnel_stage    TEXT,
    modules_completed INTEGER,
    has_active_dxgy INTEGER DEFAULT 0,
    distance_miles  REAL,
    snapshotted_at  DATETIME DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_msg_partner ON message_log(partner_id);
CREATE INDEX IF NOT EXISTS idx_msg_logged ON message_log(logged_at);
CREATE INDEX IF NOT EXISTS idx_msg_campaign ON message_log(campaign_id);
CREATE INDEX IF NOT EXISTS idx_reply_partner ON reply_chain(partner_id);
CREATE INDEX IF NOT EXISTS idx_reply_parent ON reply_chain(parent_message_id);
CREATE INDEX IF NOT EXISTS idx_outcome_partner ON outcome_events(partner_id);

-- Conversation state tracking (maps to Mongo partner_conversations in production)
CREATE TABLE IF NOT EXISTS partner_conversations (
    partner_id      TEXT PRIMARY KEY,
    phone_number    TEXT UNIQUE,
    current_state   TEXT DEFAULT 'new_download',
    channel         TEXT DEFAULT 'sms',
    message_window  TEXT,           -- JSON array, max 6 messages (sliding window for LLM context)
    last_message_at DATETIME,
    total_message_count INTEGER DEFAULT 0,
    state_transitions TEXT,         -- JSON array of {fromState, toState, transitionedAt, trigger}
    do_not_message  INTEGER DEFAULT 0,  -- 1 = opted out, abusive, wrong number — no further outreach
    dnm_reason      TEXT,               -- opt_out, antagonistic, wrong_number
    dnm_at          DATETIME,           -- when they were flagged
    created_at      DATETIME DEFAULT (datetime('now')),
    updated_at      DATETIME DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conv_state ON partner_conversations(current_state);
CREATE INDEX IF NOT EXISTS idx_conv_last_msg ON partner_conversations(last_message_at);

-- BQ query usage tracking and budget enforcement
CREATE TABLE IF NOT EXISTS bq_usage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id     TEXT,
    cache_key       TEXT,
    sql_fingerprint TEXT,
    bytes_processed INTEGER DEFAULT 0,
    row_count       INTEGER DEFAULT 0,
    source          TEXT,           -- 'cache' or 'bq'
    ran_at          DATETIME DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_bq_usage_date ON bq_usage(ran_at);

-- Salesmsg sync tracking
CREATE TABLE IF NOT EXISTS salesmsg_sync (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    last_sync_at        DATETIME,
    conversations_synced INTEGER DEFAULT 0,
    messages_synced     INTEGER DEFAULT 0
);
"""


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()

    print(f"Database: {os.path.abspath(DB_PATH)}")
    print(f"Tables: {[t[0] for t in tables]}")


if __name__ == '__main__':
    init_db()
