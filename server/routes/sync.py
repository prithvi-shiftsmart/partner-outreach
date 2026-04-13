"""Sync API — trigger manual sync, get sync status."""

import asyncio

from fastapi import APIRouter, Request

from server.database import get_db

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/quick")
async def trigger_quick_sync(request: Request):
    """Trigger a quick sync via the sync service."""
    sync_svc = request.app.state.sync_service
    await sync_svc.trigger(mode="quick")
    return {"success": True, "mode": "quick"}


@router.post("/full")
async def trigger_full_sync(request: Request):
    """Trigger a full sync via the sync service."""
    sync_svc = request.app.state.sync_service
    await sync_svc.trigger(mode="full")
    return {"success": True, "mode": "full"}


@router.get("/status")
def get_sync_status():
    """Get last sync info."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM salesmsg_sync ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            result = {
                "last_sync_at": row["last_sync_at"],
                "conversations_synced": row["conversations_synced"],
                "messages_synced": row["messages_synced"],
            }
            # Include new columns if available
            if "pages_scanned" in row.keys():
                result["pages_scanned"] = row["pages_scanned"]
            if "mode" in row.keys():
                result["mode"] = row["mode"]
            if "duration_seconds" in row.keys():
                result["duration_seconds"] = row["duration_seconds"]
            return result
        return {"last_sync_at": None, "conversations_synced": 0, "messages_synced": 0}
