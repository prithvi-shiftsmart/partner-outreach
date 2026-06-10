"""Campaigns API — query partners, list templates, list saved queries."""

import json
import os
import re
import subprocess

from fastapi import APIRouter

from server.config import SCRIPTS_DIR, PYTHON_PATH, CONFIG_DIR, AGENTS_DIR, STAGES_DIR, SALESMSG_TEAMS, WORKSPACE
from server.database import get_db
from server.models import QueryRequest, WindowCheckRequest
from server.zone_timezones import evaluate_window

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("/templates")
def list_templates():
    template_dirs = [
        os.path.join(AGENTS_DIR, "new_download", "message_templates"),
        os.path.join(AGENTS_DIR, "orientation_passed", "message_templates"),
    ]
    templates = []
    for templates_dir in template_dirs:
      if not os.path.exists(templates_dir):
          continue
      for f in sorted(os.listdir(templates_dir)):
            if f.endswith(".md"):
                path = os.path.join(templates_dir, f)
                with open(path) as fh:
                    content = fh.read()
                msg_section = ""
                in_section = False
                for line in content.split("\n"):
                    if line.strip().startswith("## Message"):
                        in_section = True
                        continue
                    elif line.strip().startswith("## ") and in_section:
                        break
                    elif in_section:
                        msg_section += line + "\n"
                templates.append({"name": f.replace(".md", ""), "filename": f,
                                  "content": msg_section.strip() or content})
    return {"templates": templates}


@router.get("/queries")
def list_saved_queries():
    queries_dir = os.path.join(STAGES_DIR, "01_identify", "queries")
    queries = []
    if os.path.exists(queries_dir):
        for f in sorted(os.listdir(queries_dir)):
            if f.endswith(".sql"):
                path = os.path.join(queries_dir, f)
                with open(path) as fh:
                    sql = fh.read()
                queries.append({"name": f.replace(".sql", ""), "filename": f, "sql": sql})
    return {"queries": queries}


@router.post("/query")
def run_query(req: QueryRequest):
    if req.campaign:
        cmd = [PYTHON_PATH, os.path.join(SCRIPTS_DIR, "run_query.py"), "--campaign", req.campaign]
        if req.force_refresh:
            cmd.append("--force-refresh")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=WORKSPACE, timeout=120)
        if result.returncode != 0:
            return {"error": result.stderr[:500]}
        cache_file = result.stdout.strip()
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                return {"rows": json.load(f), "source": "run_query.py", "cache_file": cache_file}
        return {"error": f"Cache file not found: {cache_file}"}
    elif req.sql:
        sql = req.sql.strip()
        declares = re.findall(r"DECLARE\s+(\w+)\s+\w+\s+DEFAULT\s+(.+?);", sql, re.IGNORECASE)
        for var_name, var_value in declares:
            sql = re.sub(rf"DECLARE\s+{var_name}\s+\w+\s+DEFAULT\s+.+?;", "", sql, flags=re.IGNORECASE)
            sql = re.sub(rf"\b{re.escape(var_name)}\b", var_value.strip(), sql)
        cmd = ["bq", "query", "--use_legacy_sql=false", "--format=json"]
        try:
            result = subprocess.run(cmd, input=sql, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            return {"error": "bq query timed out after 600s"}
        if result.returncode != 0:
            # bq spams progress lines like "Waiting on bqjob_... RUNNING" — strip those.
            # Errors go to stdout when SQL is piped via stdin, stderr otherwise — combine both.
            combined = (result.stderr or "") + "\n" + (result.stdout or "")
            err_lines = [ln for ln in combined.splitlines()
                         if ln.strip() and not ln.lstrip().startswith("Waiting on bqjob_")]
            err = "\n".join(err_lines).strip() or combined.strip() or "bq query failed with no output"
            return {"error": err[-2000:]}
        try:
            rows = json.loads(result.stdout)
            return {"rows": rows, "source": "bq_direct"}
        except json.JSONDecodeError:
            return {"error": f"Failed to parse BQ output: {result.stdout[:200]}"}
    else:
        return {"error": "Provide either 'sql' or 'campaign'"}


@router.get("/teams")
def list_teams():
    return {"teams": [{"name": k, "id": v} for k, v in SALESMSG_TEAMS.items()]}


@router.get("/context/{campaign_id}")
def get_campaign_context(campaign_id: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM campaign_context WHERE campaign_id = ?", (campaign_id,)
        ).fetchone()
        if row:
            return {"campaign_id": row["campaign_id"], "context": row["context"],
                    "auto_respond_enabled": bool(row["auto_respond_enabled"]) if "auto_respond_enabled" in row.keys() else False}
        return {"campaign_id": campaign_id, "context": "", "auto_respond_enabled": False}


@router.post("/check-window")
def check_window(req: WindowCheckRequest):
    """Split partners into ok / blocked (outside 8AM-9PM local) / unmapped buckets.

    Frontend calls this after building drafts so the operator can see how many
    recipients are currently in their quiet-hours window before clicking Send.
    """
    ok, blocked, unmapped = [], [], []
    for p in req.partners:
        result = evaluate_window(p.zone_description)
        if result["status"] == "ok":
            ok.append(p.partner_id)
        elif result["status"] == "outside_quiet_hours":
            blocked.append({"partner_id": p.partner_id, "zone_description": p.zone_description,
                            "timezone": result["timezone"], "local_time": result["local_time"],
                            "opens_at": result["opens_at"]})
        else:
            unmapped.append({"partner_id": p.partner_id, "zone_description": p.zone_description})
    return {"ok": ok, "blocked": blocked, "unmapped": unmapped,
            "total": len(req.partners), "ok_count": len(ok),
            "blocked_count": len(blocked), "unmapped_count": len(unmapped)}


@router.post("/context/{campaign_id}")
def set_campaign_context(campaign_id: str, context: str = "", auto_respond_enabled: bool = False):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO campaign_context (campaign_id, context, auto_respond_enabled) VALUES (?, ?, ?)",
            (campaign_id, context, 1 if auto_respond_enabled else 0))
        conn.commit()
    return {"success": True}
