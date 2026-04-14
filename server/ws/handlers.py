"""WebSocket endpoint handler — receives client messages, manages connections."""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from server.database import get_db
from server.ws.manager import manager

logger = logging.getLogger("ws_handler")

router = APIRouter()

# Track which partners each client has marked as read (in-memory, resets on server restart)
# This is intentionally ephemeral — unread badges come back after restart so you don't miss anything
_read_partners = set()


def _get_unread_counts() -> dict:
    """Get unread message counts per partner, excluding manually read ones."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT partner_id, COUNT(*) AS cnt
            FROM reply_chain
            WHERE direction = 'inbound' AND response_approved = 0
            GROUP BY partner_id
        """).fetchall()
        by_partner = {}
        for r in rows:
            if r["partner_id"] not in _read_partners:
                by_partner[r["partner_id"]] = r["cnt"]
        return {"total_unread": sum(by_partner.values()), "by_partner": by_partner}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)

    # Send initial unread counts on connect
    counts = _get_unread_counts()
    await manager.send_to(websocket, {"type": "unread_update", **counts})

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "mark_read":
                partner_id = msg.get("partner_id")
                if partner_id:
                    _read_partners.add(partner_id)
                    counts = _get_unread_counts()
                    await manager.broadcast({"type": "unread_update", **counts})
                    logger.info(f"Marked {partner_id} as read")

            elif msg_type == "mark_unread":
                partner_id = msg.get("partner_id")
                if partner_id:
                    _read_partners.discard(partner_id)
                    counts = _get_unread_counts()
                    await manager.broadcast({"type": "unread_update", **counts})
                    logger.info(f"Marked {partner_id} as unread")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
