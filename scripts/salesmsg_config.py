#!/usr/bin/env python3
"""Salesmsg API configuration."""

import os

# Try loading from .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip())

API_URL = "https://api.salesmessage.com/pub/v2.2"
API_TOKEN = os.getenv("SALESMSG_API_TOKEN", "")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'tracking', 'outreach.db')
