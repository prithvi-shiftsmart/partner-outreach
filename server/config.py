"""Server configuration — reads from .env, defines paths and constants."""

import json
import os
import base64

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load .env (same logic as scripts/salesmsg_config.py)
_env_path = os.path.join(WORKSPACE, ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

# Paths
DB_PATH = os.path.join(WORKSPACE, "tracking", "outreach.db")
SCRIPTS_DIR = os.path.join(WORKSPACE, "scripts")
CONFIG_DIR = os.path.join(WORKSPACE, "_config")
STAGES_DIR = os.path.join(WORKSPACE, "stages")
BATCHES_DIR = os.path.join(WORKSPACE, "tracking", "batches")
FRONTEND_DIR = os.path.join(WORKSPACE, "frontend")

# Salesmsg
SALESMSG_API_URL = "https://api.salesmessage.com/pub/v2.2"
SALESMSG_API_TOKEN = os.getenv("SALESMSG_API_TOKEN", "")

# Claude CLI
CLAUDE_CLI_PATH = "/Users/prithvi/.local/bin/claude"
PYTHON_PATH = "/usr/bin/python3"

# Sync
DEFAULT_SYNC_INTERVAL = 20  # seconds

# Salesmsg team mapping
SALESMSG_TEAMS = {
    "Circle K - Premium (+14159149242)": 66423,
    "Circle K - Premium Growth Activation": 121503,
    "Circle K - Premium Subscale": 128734,
    "Dollar General - Marketplace": 208213,
    "PFNA/PBNA (PepsiCo)": 68534,
}


def get_token_expiry():
    """Decode JWT token and return expiry timestamp, or None if invalid."""
    token = os.getenv("SALESMSG_API_TOKEN", "")
    if not token or "." not in token:
        return None
    try:
        payload = token.split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return data.get("exp")
    except Exception:
        return None


def reload_token():
    """Re-read token from .env file and update environment."""
    if os.path.exists(_env_path):
        with open(_env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("SALESMSG_API_TOKEN="):
                    _, val = line.split("=", 1)
                    os.environ["SALESMSG_API_TOKEN"] = val.strip()
                    global SALESMSG_API_TOKEN
                    SALESMSG_API_TOKEN = val.strip()
                    return val.strip()
    return ""
