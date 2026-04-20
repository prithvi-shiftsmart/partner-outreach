"""Settings API — token management, app settings, gcloud auth."""

import os
import shutil
import subprocess
from datetime import datetime

from fastapi import APIRouter

from server.config import WORKSPACE, get_token_expiry, reload_token
from server.database import get_db
from server.models import TokenUpdateRequest, SettingUpdateRequest

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _gcloud_path():
    return shutil.which("gcloud") or "/usr/local/bin/gcloud"


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


@router.get("/bq-status")
def bq_status():
    """Check bq CLI user credentials (what the dashboard actually uses, not ADC)."""
    gcloud = _gcloud_path()
    try:
        r = subprocess.run(
            [gcloud, "auth", "print-access-token"],
            capture_output=True, text=True, timeout=10)
        if r.returncode != 0 or not r.stdout.strip():
            msg = (r.stderr or "No token").strip().splitlines()[-1][:200]
            return {"valid": False, "message": msg}

        # Verify Drive scope — some tables are Drive-backed external tables.
        s = subprocess.run(
            [gcloud, "auth", "list", "--format=value(account)", "--filter=status:ACTIVE"],
            capture_output=True, text=True, timeout=10)
        account = s.stdout.strip()
        return {"valid": True, "message": f"Signed in as {account or 'unknown'}"}
    except FileNotFoundError:
        return {"valid": False, "message": "gcloud CLI not found in PATH"}
    except subprocess.TimeoutExpired:
        return {"valid": False, "message": "gcloud timed out"}


@router.post("/gcloud-auth")
def gcloud_auth():
    """Spawn `gcloud auth login --enable-gdrive-access` detached.

    `bq` CLI uses user credentials (not ADC). The `--enable-gdrive-access` flag
    adds the Drive scope needed to query Sheet-backed external BigQuery tables
    (e.g. supply_model_daily_position).
    """
    gcloud = _gcloud_path()
    if not os.path.exists(gcloud) and not shutil.which("gcloud"):
        return {"success": False, "message": "gcloud CLI not found"}
    subprocess.Popen(
        [gcloud, "auth", "login", "--enable-gdrive-access", "--update-adc"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True)
    return {"success": True, "message": "Browser opened. Complete sign-in (with Drive access), then click Check BQ auth."}
