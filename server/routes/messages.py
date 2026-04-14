"""Messages API — send replies, trigger drafts, batch send."""

import json
import os
import subprocess
import sys
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Request

from server.config import SCRIPTS_DIR, PYTHON_PATH, BATCHES_DIR, SALESMSG_TEAMS
from server.database import get_db
from server.models import SendRequest, BatchSendRequest, DraftRequest

router = APIRouter(prefix="/api/messages", tags=["messages"])


def _get_phone_for_partner(conn, partner_id):
    row = conn.execute(
        "SELECT phone_number FROM partner_conversations WHERE partner_id = ?",
        (partner_id,)
    ).fetchone()
    return row["phone_number"] if row else None


def _send_via_salesmsg(phone, message, team_id=66423):
    sys.path.insert(0, SCRIPTS_DIR)
    from salesmsg_config import API_URL, HEADERS
    import requests
    payload = {"number": phone, "message": message}
    if team_id:
        payload["team_id"] = team_id
    resp = requests.post(f"{API_URL}/messages", headers=HEADERS, json=payload)
    if resp.status_code in (200, 201):
        return True, resp.json()
    return False, f"HTTP {resp.status_code}: {resp.text[:200]}"


@router.post("/send")
def send_reply(req: SendRequest):
    with get_db() as conn:
        phone = _get_phone_for_partner(conn, req.conversation_id)
        if not phone:
            row = conn.execute(
                "SELECT notes FROM reply_chain WHERE partner_id = ? AND notes LIKE '%phone%' LIMIT 1",
                (req.conversation_id,)
            ).fetchone()
            if row and row["notes"]:
                try:
                    phone = json.loads(row["notes"]).get("phone")
                except (json.JSONDecodeError, TypeError):
                    pass
        if not phone:
            return {"error": "Could not find phone number for this partner"}

        success, output = _send_via_salesmsg(phone, req.message, req.team_id)

        if success:
            reply_id = f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            note_row = conn.execute(
                "SELECT notes FROM reply_chain WHERE partner_id = ? AND notes LIKE '%salesmsg_conv_id%' ORDER BY logged_at DESC LIMIT 1",
                (req.conversation_id,)
            ).fetchone()
            conv_id = ""
            if note_row and note_row["notes"]:
                try:
                    conv_id = json.loads(note_row["notes"]).get("salesmsg_conv_id", "")
                except (json.JSONDecodeError, TypeError):
                    pass

            conn.execute("""
                INSERT INTO reply_chain
                (reply_id, parent_message_id, partner_id, direction, content,
                 response_approved, logged_at, notes)
                VALUES (?, ?, ?, 'outbound', ?, 1, datetime('now'), ?)
            """, (reply_id, f"conv_{conv_id}", req.conversation_id, req.message,
                  json.dumps({"salesmsg_conv_id": conv_id})))

            conn.execute("""
                UPDATE reply_chain SET response_approved = 1, response_content = ?
                WHERE partner_id = ? AND direction = 'inbound' AND response_approved = 0
            """, (req.message, req.conversation_id))

            conn.execute("""
                UPDATE partner_conversations
                SET last_message_at = datetime('now'), total_message_count = total_message_count + 1
                WHERE partner_id = ?
            """, (req.conversation_id,))

            conn.commit()
            return {"success": True, "reply_id": reply_id}
        else:
            return {"success": False, "error": str(output)}


def _run_batch_send(batch_file):
    subprocess.run(
        [PYTHON_PATH, os.path.join(SCRIPTS_DIR, "send_batch.py"), batch_file],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(SCRIPTS_DIR))
    )


@router.post("/batch")
def start_batch_send(req: BatchSendRequest, background_tasks: BackgroundTasks):
    os.makedirs(BATCHES_DIR, exist_ok=True)
    safe_name = req.campaign_name.replace("/", "_").replace("\\", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_file = os.path.join(BATCHES_DIR, f"{safe_name}_{timestamp}.json")

    if req.campaign_context:
        with get_db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO campaign_context (campaign_id, context, auto_respond_enabled) VALUES (?, ?, ?)",
                (req.campaign_name, req.campaign_context, 1 if req.auto_respond_enabled else 0)
            )
            conn.commit()

    batch_data = []
    for d in req.drafts:
        batch_data.append({
            "phone": d["phone"], "message": d["message"],
            "partner_id": d.get("partner_id", f"sm_{d['phone']}"),
            "campaign": req.campaign_name, "market": d.get("market", ""),
            "company": d.get("company", ""), "first_name": d.get("first_name", ""),
            "last_name": d.get("last_name", ""), "team_id": req.team_id,
        })

    with open(batch_file, "w") as f:
        json.dump(batch_data, f)

    background_tasks.add_task(_run_batch_send, batch_file)
    return {"success": True, "batch_file": batch_file, "total": len(batch_data),
            "status_file": batch_file.replace(".json", "_status.json")}


@router.get("/batches/active")
def list_active_batches():
    """List recent batch sends with their status (last 10)."""
    if not os.path.exists(BATCHES_DIR):
        return {"batches": []}
    status_files = sorted(
        [f for f in os.listdir(BATCHES_DIR) if f.endswith("_status.json")],
        key=lambda f: os.path.getmtime(os.path.join(BATCHES_DIR, f)),
        reverse=True,
    )[:10]
    batches = []
    for sf in status_files:
        try:
            with open(os.path.join(BATCHES_DIR, sf)) as f:
                data = json.load(f)
            name = sf.replace("_status.json", "")
            # Strip timestamp suffix (last 16 chars: _YYYYMMDD_HHMMSS)
            display_name = name[:-16] if len(name) > 16 else name
            batches.append({
                "name": display_name,
                "filename": sf,
                **data,
            })
        except (json.JSONDecodeError, IOError):
            continue
    return {"batches": batches}


@router.get("/batch/{batch_id}/status")
def get_batch_status(batch_id: str):
    status_file = os.path.join(BATCHES_DIR, f"{batch_id}_status.json")
    if not os.path.exists(status_file):
        return {"error": "Batch not found"}
    with open(status_file) as f:
        return json.load(f)


@router.post("/draft")
async def trigger_draft(req: DraftRequest, request: Request):
    """Manually trigger a draft for a partner."""
    draft_svc = request.app.state.draft_service
    reply_id = req.reply_id
    if not reply_id:
        with get_db() as conn:
            row = conn.execute("""
                SELECT reply_id FROM reply_chain
                WHERE partner_id = ? AND direction = 'inbound' AND response_approved = 0
                ORDER BY logged_at DESC LIMIT 1
            """, (req.partner_id,)).fetchone()
            reply_id = row["reply_id"] if row else None
    if not reply_id:
        return {"error": "No pending inbound message to draft a reply for"}
    await draft_svc.queue_draft(req.partner_id, reply_id)
    return {"success": True, "partner_id": req.partner_id, "reply_id": reply_id}
