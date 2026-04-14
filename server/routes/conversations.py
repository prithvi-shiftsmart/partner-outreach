"""Conversations API — list conversations and get full thread for a partner."""

import json

from fastapi import APIRouter, Query

from server.database import get_db

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("")
def list_conversations(
    campaigns: str = Query(default="", description="Comma-separated campaign IDs to filter"),
    days: int = Query(default=1, description="Number of days to look back"),
    include_read: bool = Query(default=True),
):
    """List conversations initiated by us, with latest message preview."""
    with get_db() as conn:
        campaign_filter = ""
        params = []

        if campaigns:
            campaign_list = [c.strip() for c in campaigns.split(",") if c.strip()]
            if campaign_list:
                placeholders = ",".join("?" * len(campaign_list))
                campaign_filter = f"AND campaign_id IN ({placeholders})"
                params.extend(campaign_list)

        rows = conn.execute(f"""
            SELECT
                pc.partner_id,
                pc.first_name,
                pc.last_name,
                pc.phone_number,
                pc.market,
                pc.bq_partner_id,
                pc.current_state,
                pc.do_not_message,
                pc.excluded_campaigns,
                ml_latest.campaign_id,
                COALESCE(last_reply.content, ml_latest.message_content) AS last_message,
                COALESCE(last_reply.logged_at, ml_latest.sent_at, ml_latest.logged_at) AS last_message_at,
                CASE WHEN last_reply.direction = 'inbound' THEN 'inbound' ELSE 'outbound' END AS last_direction,
                CASE WHEN unread_count.cnt > 0 THEN 1 ELSE 0 END AS unread,
                latest_draft.draft_status
            FROM partner_conversations pc
            INNER JOIN (
                SELECT partner_id, campaign_id, message_content, sent_at, logged_at,
                       ROW_NUMBER() OVER (PARTITION BY partner_id ORDER BY COALESCE(sent_at, logged_at) DESC) AS rn
                FROM message_log
                WHERE DATE(COALESCE(sent_at, logged_at)) >= DATE('now', '-' || ? || ' days')
                {campaign_filter}
            ) ml_latest ON ml_latest.partner_id = pc.partner_id AND ml_latest.rn = 1
            LEFT JOIN (
                SELECT partner_id, content, direction, logged_at,
                       ROW_NUMBER() OVER (PARTITION BY partner_id ORDER BY logged_at DESC) AS rn
                FROM reply_chain
            ) last_reply ON last_reply.partner_id = pc.partner_id AND last_reply.rn = 1
            LEFT JOIN (
                SELECT partner_id, COUNT(*) AS cnt
                FROM reply_chain
                WHERE direction = 'inbound' AND response_approved = 0
                GROUP BY partner_id
            ) unread_count ON unread_count.partner_id = pc.partner_id
            LEFT JOIN (
                SELECT partner_id, draft_status,
                       ROW_NUMBER() OVER (PARTITION BY partner_id ORDER BY logged_at DESC) AS rn
                FROM reply_chain
                WHERE direction = 'inbound' AND draft_status IS NOT NULL
            ) latest_draft ON latest_draft.partner_id = pc.partner_id AND latest_draft.rn = 1
            WHERE pc.do_not_message = 0
            ORDER BY
                unread DESC,
                COALESCE(last_reply.logged_at, ml_latest.sent_at, ml_latest.logged_at) DESC
        """, [days] + params).fetchall()

        conversations = []
        for r in rows:
            excluded = []
            if r["excluded_campaigns"]:
                try:
                    excluded = json.loads(r["excluded_campaigns"])
                except (json.JSONDecodeError, TypeError):
                    pass
            if campaigns and excluded:
                campaign_list = [c.strip() for c in campaigns.split(",") if c.strip()]
                if all(c in excluded for c in campaign_list):
                    continue

            conversations.append({
                "partner_id": r["partner_id"],
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "phone_number": r["phone_number"],
                "market": r["market"],
                "bq_partner_id": r["bq_partner_id"],
                "current_state": r["current_state"],
                "campaign_id": r["campaign_id"],
                "last_message": (r["last_message"] or "")[:80],
                "last_message_at": r["last_message_at"],
                "last_direction": r["last_direction"],
                "unread": bool(r["unread"]),
                "draft_status": r["draft_status"],
            })

        return {"conversations": conversations, "total": len(conversations)}


@router.get("/campaigns/list")
def list_campaign_ids(days: int = Query(default=7)):
    """Get distinct campaign IDs from recent messages (for filter dropdown)."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT DISTINCT campaign_id, COUNT(*) as msg_count
            FROM message_log
            WHERE DATE(COALESCE(sent_at, logged_at)) >= DATE('now', '-' || ? || ' days')
            GROUP BY campaign_id
            ORDER BY MAX(COALESCE(sent_at, logged_at)) DESC
        """, (days,)).fetchall()
        return {"campaigns": [{"id": r["campaign_id"], "count": r["msg_count"]} for r in rows]}


@router.get("/{partner_id}")
def get_conversation(partner_id: str):
    """Get full thread for a partner — merges outbound (message_log) and inbound (reply_chain)."""
    with get_db() as conn:
        partner = conn.execute(
            "SELECT * FROM partner_conversations WHERE partner_id = ?", (partner_id,)
        ).fetchone()
        if not partner:
            return {"error": "Partner not found"}, 404

        outbound = conn.execute("""
            SELECT message_id AS id, 'outbound' AS direction, message_content AS content,
                   COALESCE(sent_at, logged_at) AS timestamp, campaign_id, NULL AS media_urls,
                   NULL AS classified_intent, NULL AS draft_status, NULL AS draft_content
            FROM message_log
            WHERE partner_id = ?
            ORDER BY timestamp
        """, (partner_id,)).fetchall()

        replies = conn.execute("""
            SELECT reply_id AS id, direction, content,
                   logged_at AS timestamp, NULL AS campaign_id, media_urls,
                   classified_intent, draft_status, draft_content
            FROM reply_chain
            WHERE partner_id = ?
            ORDER BY logged_at
        """, (partner_id,)).fetchall()

        all_messages = []
        for r in outbound:
            all_messages.append({
                "id": r["id"], "direction": r["direction"], "content": r["content"],
                "timestamp": r["timestamp"], "campaign_id": r["campaign_id"],
                "media_urls": None, "classified_intent": None,
                "draft_status": None, "draft_content": None,
            })
        for r in replies:
            media = None
            if r["media_urls"]:
                try:
                    media = json.loads(r["media_urls"])
                except (json.JSONDecodeError, TypeError):
                    pass
            all_messages.append({
                "id": r["id"], "direction": r["direction"], "content": r["content"],
                "timestamp": r["timestamp"], "campaign_id": r["campaign_id"],
                "media_urls": media, "classified_intent": r["classified_intent"],
                "draft_status": r["draft_status"], "draft_content": r["draft_content"],
            })

        all_messages.sort(key=lambda m: m["timestamp"] or "")

        campaigns = conn.execute(
            "SELECT DISTINCT campaign_id FROM message_log WHERE partner_id = ?", (partner_id,)
        ).fetchall()

        excluded = []
        if partner["excluded_campaigns"]:
            try:
                excluded = json.loads(partner["excluded_campaigns"])
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "partner": {
                "partner_id": partner["partner_id"],
                "phone_number": partner["phone_number"],
                "first_name": partner["first_name"],
                "last_name": partner["last_name"],
                "market": partner["market"],
                "bq_partner_id": partner["bq_partner_id"],
                "current_state": partner["current_state"],
                "do_not_message": partner["do_not_message"],
                "dnm_reason": partner["dnm_reason"] if partner["do_not_message"] else None,
                "excluded_campaigns": excluded,
                "campaigns": [r["campaign_id"] for r in campaigns],
            },
            "messages": all_messages,
        }
