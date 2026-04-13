"""Settings API — token management, app settings."""

import os
from datetime import datetime

from fastapi import APIRouter

from server.config import WORKSPACE, get_token_expiry, reload_token
from server.database import get_db
from server.models import TokenUpdateRequest, SettingUpdateRequest

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings():
    exp = get_token_expiry()
    token_info = {}
    if exp:
        exp_dt = datetime.fromtimestamp(int(exp))
        token_info = {"expires_at": exp_dt.isoformat(), "expired": datetime.now() > exp_dt,
                      "expires_display": exp_dt.strftime("%b %d, %I:%M %p")}
    else:
        token_info = {"expires_at": None, "expired": True, "expires_display": "Unknown"}

    with get_db() as conn:
        settings = {}
        rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        for r in rows:
            settings[r["key"]] = r["value"]

    return {"token": token_info, "settings": settings}


@router.post("/token")
def update_token(req: TokenUpdateRequest):
    env_path = os.path.join(WORKSPACE, ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path) as f:
            lines = f.readlines()
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith("SALESMSG_API_TOKEN="):
            lines[i] = f"SALESMSG_API_TOKEN={req.token.strip()}\n"
            found = True
            break
    if not found:
        lines.append(f"SALESMSG_API_TOKEN={req.token.strip()}\n")
    with open(env_path, "w") as f:
        f.writelines(lines)
    reload_token()
    exp = get_token_expiry()
    if exp:
        exp_dt = datetime.fromtimestamp(int(exp))
        return {"success": True, "expires_at": exp_dt.isoformat(), "expires_display": exp_dt.strftime("%b %d, %I:%M %p")}
    return {"success": True, "expires_at": None}


@router.post("/update")
def update_setting(req: SettingUpdateRequest):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (req.key, req.value))
        conn.commit()
    return {"success": True}
