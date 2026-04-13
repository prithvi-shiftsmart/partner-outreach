"""Sync API — trigger manual sync, get sync status."""

import os
import subprocess

from fastapi import APIRouter, BackgroundTasks

from server.config import SCRIPTS_DIR, PYTHON_PATH, WORKSPACE
from server.database import get_db

router = APIRouter(prefix="/api/sync", tags=["sync"])


def _run_sync(mode="quick"):
    cmd = [PYTHON_PATH, os.path.join(SCRIPTS_DIR, "salesmsg_sync.py")]
    if mode == "full":
        cmd.append("--full")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=WORKSPACE, timeout=300)
    return result.stdout + result.stderr


@router.post("/quick")
def trigger_quick_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_sync, "quick")
    return {"success": True, "mode": "quick"}


@router.post("/full")
def trigger_full_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_sync, "full")
    return {"success": True, "mode": "full"}


@router.get("/status")
def get_sync_status():
    with get_db() as conn:
        row = conn.execute("SELECT * FROM salesmsg_sync ORDER BY id DESC LIMIT 1").fetchone()
        if row:
            return {"last_sync_at": row["last_sync_at"],
                    "conversations_synced": row["conversations_synced"],
                    "messages_synced": row["messages_synced"]}
        return {"last_sync_at": None, "conversations_synced": 0, "messages_synced": 0}
