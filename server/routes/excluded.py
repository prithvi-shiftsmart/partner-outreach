"""Excluded partners API — list, update, reinstate."""

import json

from fastapi import APIRouter, Query

from server.database import get_db
from server.models import ExcludeRequest, CampaignExcludeRequest

router = APIRouter(prefix="/api/excluded", tags=["excluded"])


@router.get("")
def list_excluded(campaign_id: str = Query(default="")):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT pc.partner_id, pc.phone_number, pc.first_name, pc.last_name,
                   pc.bq_partner_id, pc.dnm_reason, pc.dnm_at, pc.current_state, pc.excluded_campaigns
            FROM partner_conversations pc WHERE pc.do_not_message = 1 ORDER BY pc.dnm_at DESC
        """).fetchall()
        result = []
        for r in rows:
            excluded_camps = []
            if r["excluded_campaigns"]:
                try:
                    excluded_camps = json.loads(r["excluded_campaigns"])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append({**dict(r), "excluded_campaigns": excluded_camps})
        return {"excluded": result}


@router.post("/{partner_id}/exclude")
def exclude_partner(partner_id: str, req: ExcludeRequest):
    with get_db() as conn:
        conn.execute("""
            UPDATE partner_conversations
            SET do_not_message = 1, dnm_reason = ?, dnm_at = datetime('now'), updated_at = datetime('now')
            WHERE partner_id = ?
        """, (req.reason, partner_id))
        conn.commit()
    return {"success": True}


@router.post("/{partner_id}/exclude-campaign")
def exclude_from_campaign(partner_id: str, req: CampaignExcludeRequest):
    with get_db() as conn:
        row = conn.execute(
            "SELECT excluded_campaigns FROM partner_conversations WHERE partner_id = ?", (partner_id,)
        ).fetchone()
        excluded = []
        if row and row["excluded_campaigns"]:
            try:
                excluded = json.loads(row["excluded_campaigns"])
            except (json.JSONDecodeError, TypeError):
                pass
        if req.campaign_id not in excluded:
            excluded.append(req.campaign_id)
        conn.execute("""
            UPDATE partner_conversations SET excluded_campaigns = ?, updated_at = datetime('now')
            WHERE partner_id = ?
        """, (json.dumps(excluded), partner_id))
        conn.commit()
    return {"success": True, "excluded_campaigns": excluded}


@router.post("/{partner_id}/reinstate")
def reinstate_partner(partner_id: str):
    with get_db() as conn:
        conn.execute("""
            UPDATE partner_conversations
            SET do_not_message = 0, dnm_reason = NULL, dnm_at = NULL, updated_at = datetime('now')
            WHERE partner_id = ?
        """, (partner_id,))
        conn.commit()
    return {"success": True}


@router.post("/{partner_id}/reinstate-campaign")
def reinstate_from_campaign(partner_id: str, req: CampaignExcludeRequest):
    with get_db() as conn:
        row = conn.execute(
            "SELECT excluded_campaigns FROM partner_conversations WHERE partner_id = ?", (partner_id,)
        ).fetchone()
        excluded = []
        if row and row["excluded_campaigns"]:
            try:
                excluded = json.loads(row["excluded_campaigns"])
            except (json.JSONDecodeError, TypeError):
                pass
        if req.campaign_id in excluded:
            excluded.remove(req.campaign_id)
        conn.execute("""
            UPDATE partner_conversations SET excluded_campaigns = ?, updated_at = datetime('now')
            WHERE partner_id = ?
        """, (json.dumps(excluded) if excluded else None, partner_id))
        conn.commit()
    return {"success": True, "excluded_campaigns": excluded}
