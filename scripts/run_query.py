#!/usr/bin/env python3
"""
run_query.py — Unified BQ query runner with caching, budget enforcement, and usage logging.

Usage:
  # Run a named campaign (checks cache first):
  python3 scripts/run_query.py --campaign activation_large

  # Force refresh (skip cache):
  python3 scripts/run_query.py --campaign incomplete_orientation --force-refresh

  # Run ad-hoc SQL with caching:
  python3 scripts/run_query.py --sql "SELECT ..." --cache-key custom_xyz

  # Check today's usage:
  python3 scripts/run_query.py --usage

Returns: path to JSON results file on stdout. Metadata on stderr.
"""

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(WORKSPACE, '_config', 'query_registry.json')
CACHE_DIR = os.path.join(WORKSPACE, 'stages', '01_identify', 'output')
DB_PATH = os.path.join(WORKSPACE, 'tracking', 'outreach.db')

DAILY_BUDGET = 15
DEFAULT_TTL_HOURS = 4


def today_et():
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")


def cache_path(cache_key):
    return os.path.join(CACHE_DIR, f"{cache_key}_{today_et()}.json")


def is_fresh(path, ttl_hours=DEFAULT_TTL_HOURS):
    if not os.path.exists(path):
        return False
    age = (datetime.now(timezone.utc) -
           datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc))
    return age.total_seconds() < ttl_hours * 3600


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS bq_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id TEXT, cache_key TEXT, sql_fingerprint TEXT,
        bytes_processed INTEGER DEFAULT 0, row_count INTEGER DEFAULT 0,
        source TEXT, ran_at DATETIME DEFAULT (datetime('now'))
    )""")
    conn.commit()
    return conn


def check_budget(conn):
    count = conn.execute(
        "SELECT COUNT(*) FROM bq_usage WHERE DATE(ran_at) = ? AND source = 'bq'",
        (today_et(),)
    ).fetchone()[0]
    return count, DAILY_BUDGET - count


def log_usage(conn, campaign_id, cache_key, sql_text, bytes_proc, row_count, source):
    conn.execute(
        "INSERT INTO bq_usage (campaign_id, cache_key, sql_fingerprint, bytes_processed, row_count, source) VALUES (?,?,?,?,?,?)",
        (campaign_id, cache_key, hashlib.md5((sql_text or '').encode()).hexdigest()[:12],
         bytes_proc, row_count, source)
    )
    conn.commit()


def run_bq(sql):
    result = subprocess.run(
        ["bq", "query", "--use_legacy_sql=false", "--format=json", "--quiet"],
        input=sql, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[error] BQ query failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(2)
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        # Filter out BQ progress lines
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('['):
                rows = json.loads(line)
                break
        else:
            print(f"[error] Could not parse BQ output", file=sys.stderr)
            sys.exit(2)
    return rows


def show_usage():
    conn = get_db()
    today = today_et()
    rows = conn.execute("""
        SELECT source, COUNT(*) as count, SUM(row_count) as total_rows
        FROM bq_usage WHERE DATE(ran_at) = ?
        GROUP BY source
    """, (today,)).fetchall()
    bq_count = sum(r[1] for r in rows if r[0] == 'bq')
    cache_count = sum(r[1] for r in rows if r[0] == 'cache')
    print(f"Today ({today}): {bq_count} BQ queries, {cache_count} cache hits, {DAILY_BUDGET - bq_count} budget remaining")
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--campaign', help='Campaign ID from query_registry.json')
    parser.add_argument('--sql', help='Ad-hoc SQL to run')
    parser.add_argument('--cache-key', help='Cache key for ad-hoc queries')
    parser.add_argument('--force-refresh', action='store_true')
    parser.add_argument('--ttl', type=float, default=None)
    parser.add_argument('--usage', action='store_true', help='Show today\'s query usage')
    args = parser.parse_args()

    if args.usage:
        show_usage()
        return

    conn = get_db()

    # Resolve SQL and cache key
    if args.campaign:
        with open(REGISTRY_PATH) as f:
            registry = json.load(f)
        cfg = registry['campaigns'][args.campaign]
        sql_path = os.path.join(WORKSPACE, cfg['sql_file'])
        with open(sql_path) as f:
            sql = f.read()
        key = args.campaign
        ttl = args.ttl or (2 if 'referral' in args.campaign else DEFAULT_TTL_HOURS)
    elif args.sql:
        sql = args.sql
        key = args.cache_key or f"adhoc_{hashlib.md5(sql.encode()).hexdigest()[:8]}"
        ttl = args.ttl or 1
    else:
        parser.error('Provide --campaign or --sql')
        return

    cpath = cache_path(key)

    # Cache hit
    if not args.force_refresh and is_fresh(cpath, ttl):
        with open(cpath) as f:
            rows = json.load(f)
        log_usage(conn, args.campaign or 'adhoc', key, '', 0, len(rows), 'cache')
        conn.close()
        print(cpath, end='')
        print(f"[cache] {len(rows)} rows from {os.path.basename(cpath)}", file=sys.stderr)
        return

    # Budget check
    used, remaining = check_budget(conn)
    if remaining <= 0:
        print(f"[budget] Daily limit of {DAILY_BUDGET} reached ({used} queries today).", file=sys.stderr)
        if os.path.exists(cpath):
            print(cpath, end='')
            print(f"[budget] Returning stale cache.", file=sys.stderr)
        else:
            print("NO_CACHE", end='')
        conn.close()
        sys.exit(1)

    # Run BQ
    rows = run_bq(sql)

    # Cache + log
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cpath, 'w') as f:
        json.dump(rows, f, indent=2, default=str)
    log_usage(conn, args.campaign or 'adhoc', key, sql, 0, len(rows), 'bq')
    conn.close()

    print(cpath, end='')
    print(f"[bq] {len(rows)} rows → {os.path.basename(cpath)}", file=sys.stderr)


if __name__ == '__main__':
    main()
