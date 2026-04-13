"""Metrics API — campaign performance, reply rates, top markets."""

from fastapi import APIRouter, Query

from server.database import get_db

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("")
def get_metrics(days: int = Query(default=7)):
    with get_db() as conn:
        by_campaign = conn.execute("""
            SELECT campaign_id, status, COUNT(*) AS cnt
            FROM message_log
            WHERE DATE(COALESCE(sent_at, logged_at)) >= DATE('now', '-' || ? || ' days')
            GROUP BY campaign_id, status ORDER BY cnt DESC
        """, (days,)).fetchall()

        top_markets = conn.execute("""
            SELECT market, COUNT(*) AS cnt FROM message_log
            WHERE market IS NOT NULL AND market != ''
            AND DATE(COALESCE(sent_at, logged_at)) >= DATE('now', '-' || ? || ' days')
            GROUP BY market ORDER BY cnt DESC LIMIT 10
        """, (days,)).fetchall()

        outbound = conn.execute("""
            SELECT COUNT(DISTINCT partner_id) FROM message_log
            WHERE DATE(COALESCE(sent_at, logged_at)) >= DATE('now', '-' || ? || ' days')
        """, (days,)).fetchone()[0]

        inbound = conn.execute("""
            SELECT COUNT(DISTINCT partner_id) FROM reply_chain
            WHERE direction = 'inbound' AND DATE(logged_at) >= DATE('now', '-' || ? || ' days')
        """, (days,)).fetchone()[0]

        intents = conn.execute("""
            SELECT classified_intent, COUNT(*) AS cnt FROM reply_chain
            WHERE classified_intent IS NOT NULL AND DATE(logged_at) >= DATE('now', '-' || ? || ' days')
            GROUP BY classified_intent ORDER BY cnt DESC
        """, (days,)).fetchall()

        return {
            "by_campaign": [dict(r) for r in by_campaign],
            "top_markets": [dict(r) for r in top_markets],
            "outbound_partners": outbound, "inbound_partners": inbound,
            "reply_rate": round(inbound / outbound * 100, 1) if outbound > 0 else 0,
            "intents": [dict(r) for r in intents],
        }
