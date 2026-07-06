"""Auto-draft service — generates reply drafts via Claude CLI subprocess."""

import asyncio
import json
import logging
import os
import re

from server.config import CLAUDE_CLI_PATH, CONFIG_DIR, COMMON_DIR, AGENTS_DIR, WORKSPACE
from server.database import get_db

logger = logging.getLogger("draft_service")

# Response-playbook keyword routing. Loading ONLY the relevant playbook(s) keeps the
# prompt lean and preserves HARD RULE precedence (loading all playbooks lets verbose
# canonical replies override rules like "bare yes -> no response"). Mirrors the
# monorepo, which injects the single intent-matched playbook.
PLAYBOOK_KEYWORDS = {
    "orientation-logistics": ["orientation", "start learning", "modules", "get started", "in-app", "in app", "where do i", "how do i start", "shadow", "certification"],
    "app-issues": ["app", "log in", "login", "password", "locked out", "can't get in", "cant get in", "stuck", "won't let me", "wont let me", "error", "crash", "froze", "frozen", "check in", "checkin", "geofence", "turned away", "work experience", "employer", "job experience", "banned", "deactivated", "suspended", "shadow", "no one showed", "nobody showed"],
    "payment-issues": ["pay", "paid", "$10", "10 dollars", "deposit", "stripe", "bank", "debit", "card", "cash app", "cashapp", "apple pay", "paypal", "zelle", "itin", "ssn", "verified", "payout", "earnings", "money", "direct deposit"],
    "pay-and-bonuses": ["bonus", "rate", "how much", "per hour", "hourly"],
    "account-and-reliability": ["address", "moved", "relocat", "new location", "traveling", "travelling", "visiting", "i'm in", "im in", "reliability", "on time rate", "cancel"],
    "referral-program": ["refer", "referral", "invite", "promo code", "referred"],
    "shift-discovery-and-bonuses": ["only see", "only seeing", "other types", "distance", "too far", "not worth", "miles", "closer", "transportation", "commute", "bus"],
    "shift-info": ["backup", "floater", "extend", "running late", "late", "adjust", "shift time", "first shift", "what to bring", "what to wear"],
    "food-prep-shift": ["food prep", "cook", "oven", "hairnet", "gloves", "menu", "bin prep"],
    "image-intent": ["picture", "photo", "screenshot", "pic", "image", "see this", "see the"],
    "trust-and-identity": ["scam", "legit", "real person", "is this real", "who is this", "fake"],
    "keyword-replies": [],
}

# Knowledge base keyword routing — paths are relative to common/concierge/knowledge-base/.
# Nothing is always-on: system-base.md already carries orientation/pay basics, and
# always-loading orientation/platform KB pulled the model off-topic (e.g. answering a
# bare "yes" with orientation steps, or pivoting a transit question to address-change).
KB_ALWAYS = []
KB_KEYWORDS = {
    "orientation": ["orientation-process"],
    "module": ["orientation-process"],
    "background check": ["orientation-process"],
    "bgc": ["orientation-process"],
    "company": ["platform-policies"],
    "companies": ["platform-policies"],
    "pay": ["pay-rates", "getting-paid"],
    "paid": ["getting-paid", "payments"],
    "$10": ["getting-paid", "payments"],
    "earnings": ["getting-paid"],
    "payout": ["getting-paid", "payments"],
    "deposit": ["payments"],
    "stripe": ["payments"],
    "bank": ["payments"],
    "debit": ["payments"],
    "card": ["payments"],
    "cash app": ["payments"],
    "cashapp": ["payments"],
    "apple pay": ["payments"],
    "paypal": ["payments"],
    "zelle": ["payments"],
    "itin": ["payments"],
    "ssn": ["payments"],
    "verified": ["payments"],
    "backup": ["backup-floater-shifts"],
    "floater": ["backup-floater-shifts"],
    "food prep": ["ckp/ckp-food-prep-guide"],
    "circle k": ["ckp/ckp-food-prep-guide"],
    "ckp": ["ckp/ckp-food-prep-guide"],
    "dollar general": ["platform-policies", "orientation-process", "dg/dg-shift-guide"],
    "dg": ["platform-policies", "orientation-process", "dg/dg-shift-guide"],
}

class DraftService:
    """Manages auto-draft queue and Claude CLI subprocess calls."""

    def __init__(self, ws_manager):
        self._ws = ws_manager
        self._semaphore = asyncio.Semaphore(2)  # Max 2 concurrent drafts
        self._queue = asyncio.Queue()
        self._running = False
        self._task = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._worker())
        logger.info("Draft service started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Draft service stopped")

    async def queue_draft(self, partner_id: str, reply_id: str):
        """Queue a draft request for an inbound message."""
        # Set status to pending
        await asyncio.to_thread(self._set_draft_status, reply_id, "pending")
        await self._queue.put((partner_id, reply_id))
        logger.info(f"Queued draft for {partner_id}")

    async def _worker(self):
        """Process draft queue."""
        while self._running:
            try:
                partner_id, reply_id = await asyncio.wait_for(
                    self._queue.get(), timeout=5.0
                )
                asyncio.create_task(self._generate_with_semaphore(partner_id, reply_id))
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Draft worker error: {e}")

    async def _generate_with_semaphore(self, partner_id: str, reply_id: str):
        """Acquire semaphore then generate draft."""
        async with self._semaphore:
            await self._generate_draft(partner_id, reply_id)

    async def _generate_draft(self, partner_id: str, reply_id: str):
        """Generate a draft reply for an inbound message."""
        try:
            # 1. Check response cache
            cached = await asyncio.to_thread(self._check_cache, partner_id)
            if cached:
                await asyncio.to_thread(self._set_draft_content, reply_id, cached, "cached")
                await self._ws.broadcast({
                    "type": "draft_ready",
                    "partner_id": partner_id,
                    "draft_content": cached,
                    "reply_id": reply_id,
                    "cached": True,
                })
                logger.info(f"Cache hit for {partner_id}")
                return

            # 2. Build prompt
            await asyncio.to_thread(self._set_draft_status, reply_id, "drafting")
            prompt = await asyncio.to_thread(self._build_prompt, partner_id)
            if not prompt:
                await asyncio.to_thread(self._set_draft_status, reply_id, "error")
                return

            # 3. Call Claude CLI
            try:
                proc = await asyncio.create_subprocess_exec(
                    CLAUDE_CLI_PATH, "-p", "--model", "sonnet",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=prompt.encode()),
                    timeout=120
                )
                draft = stdout.decode().strip()

                # Clean output (remove quotes, backticks)
                draft = draft.strip('"\'`')
                draft = re.sub(r'^```\w*\n?', '', draft)
                draft = re.sub(r'\n?```$', '', draft)
                draft = draft.strip()

                if not draft:
                    logger.warning(f"Empty draft for {partner_id}")
                    await asyncio.to_thread(self._set_draft_status, reply_id, "error")
                    return

            except asyncio.TimeoutError:
                logger.error(f"Draft timed out for {partner_id}")
                await asyncio.to_thread(self._set_draft_status, reply_id, "error")
                return

            # 4. Store and broadcast
            await asyncio.to_thread(self._set_draft_content, reply_id, draft, "ready")
            await self._ws.broadcast({
                "type": "draft_ready",
                "partner_id": partner_id,
                "draft_content": draft,
                "reply_id": reply_id,
                "cached": False,
            })
            logger.info(f"Draft ready for {partner_id}")

        except Exception as e:
            logger.error(f"Draft generation failed for {partner_id}: {e}", exc_info=True)
            await asyncio.to_thread(self._set_draft_status, reply_id, "error")

    # --- Database helpers (run in thread) ---

    def _check_cache(self, partner_id: str) -> str:
        """Check for a cached response from similar messages in the same campaign."""
        with get_db() as conn:
            # Get the latest inbound message content
            inbound = conn.execute("""
                SELECT content FROM reply_chain
                WHERE partner_id = ? AND direction = 'inbound'
                ORDER BY logged_at DESC LIMIT 1
            """, (partner_id,)).fetchone()
            if not inbound:
                return ""

            content = inbound["content"].strip().lower()

            # Get campaign
            campaign = conn.execute("""
                SELECT campaign_id FROM message_log
                WHERE partner_id = ? ORDER BY COALESCE(sent_at, logged_at) DESC LIMIT 1
            """, (partner_id,)).fetchone()
            if not campaign:
                return ""

            # Look for approved responses to similar messages in same campaign
            cached = conn.execute("""
                SELECT rc2.response_content
                FROM reply_chain rc1
                JOIN message_log ml ON ml.partner_id = rc1.partner_id
                JOIN reply_chain rc2 ON rc2.partner_id = rc1.partner_id
                    AND rc2.direction = 'outbound' AND rc2.response_approved = 1
                WHERE rc1.direction = 'inbound'
                AND rc1.response_approved = 1
                AND ml.campaign_id = ?
                AND LOWER(TRIM(rc1.content)) = ?
                AND rc2.response_content IS NOT NULL
                AND rc2.response_content != ''
                LIMIT 1
            """, (campaign["campaign_id"], content)).fetchone()

            return cached["response_content"] if cached else ""

    def _set_draft_status(self, reply_id: str, status: str):
        with get_db() as conn:
            conn.execute(
                "UPDATE reply_chain SET draft_status = ? WHERE reply_id = ?",
                (status, reply_id)
            )
            conn.commit()

    def _set_draft_content(self, reply_id: str, content: str, status: str):
        with get_db() as conn:
            conn.execute(
                "UPDATE reply_chain SET draft_content = ?, draft_status = ? WHERE reply_id = ?",
                (content, status, reply_id)
            )
            conn.commit()

    def _build_prompt(self, partner_id: str) -> str:
        """Build the Claude prompt with conversation context and knowledge base."""
        with get_db() as conn:
            # Get conversation thread
            outbound = conn.execute("""
                SELECT 'outbound' AS direction, message_content AS content,
                       COALESCE(sent_at, logged_at) AS timestamp
                FROM message_log WHERE partner_id = ?
            """, (partner_id,)).fetchall()

            inbound = conn.execute("""
                SELECT direction, content, logged_at AS timestamp
                FROM reply_chain WHERE partner_id = ?
            """, (partner_id,)).fetchall()

            messages = []
            for r in outbound:
                messages.append({"direction": "outbound", "content": r["content"], "ts": r["timestamp"]})
            for r in inbound:
                messages.append({"direction": r["direction"], "content": r["content"], "ts": r["timestamp"]})
            messages.sort(key=lambda m: m["ts"] or "")

            if not messages:
                return ""

            # Get partner info
            partner = conn.execute(
                "SELECT first_name, market FROM partner_conversations WHERE partner_id = ?",
                (partner_id,)
            ).fetchone()
            first_name = partner["first_name"] if partner else ""

            # Get campaign context
            campaign = conn.execute("""
                SELECT campaign_id FROM message_log
                WHERE partner_id = ? ORDER BY COALESCE(sent_at, logged_at) DESC LIMIT 1
            """, (partner_id,)).fetchone()
            campaign_context = ""
            if campaign:
                ctx_row = conn.execute(
                    "SELECT context FROM campaign_context WHERE campaign_id = ?",
                    (campaign["campaign_id"],)
                ).fetchone()
                if ctx_row:
                    campaign_context = ctx_row["context"]

        return assemble_prompt(messages, first_name, campaign_context)


def assemble_prompt(messages, first_name: str, campaign_context: str = "") -> str:
    """Assemble the concierge prompt from the migrated source-of-truth files under
    common/concierge/ + modules/concierge-new-download/. The replay harness now
    tests the same prompts that port to the monorepo (no duplicated inline copy).
    The JSON Response Format section of system-base.md is stripped because the
    local replay consumes plain-text output."""
    if not messages:
        return ""

    concierge_dir = os.path.join(COMMON_DIR, "concierge")

    def _read(path):
        return open(path).read() if os.path.exists(path) else ""

    # System base = HARD RULES + canonical intent registry. Drop the JSON Response
    # Format section; the local replay expects plain-text output.
    system_base = _read(os.path.join(concierge_dir, "system-base.md"))
    system_base = re.split(r"\n## Response Format", system_base)[0].rstrip()

    guardrails = _read(os.path.join(concierge_dir, "guardrails.md"))
    tone = _read(os.path.join(concierge_dir, "tone-and-voice.md"))

    # Canonical replies live in the new-download response playbooks. Load ONLY the
    # keyword-matched playbook(s) over the last 6 inbound messages — loading all of
    # them buries the HARD RULES and lets verbose canonical replies override them.
    recent_inbound = " \n ".join(
        m["content"] for m in messages[-6:] if m["direction"] == "inbound"
    ).lower()
    matched_playbooks = [
        name for name, kws in PLAYBOOK_KEYWORDS.items()
        if kws and any(kw in recent_inbound for kw in kws)
    ]
    playbooks = ""
    pb_dir = os.path.join(
        WORKSPACE, "modules", "concierge-new-download", "prompts", "response-playbook"
    )
    for name in matched_playbooks:
        path = os.path.join(pb_dir, name + ".md")
        if os.path.exists(path):
            playbooks += f"\n\n--- Playbook: {name} ---\n{_read(path)}"

    # Knowledge base: small always-on core + keyword matches over last 6 inbound.
    kb_dir = os.path.join(concierge_dir, "knowledge-base")
    recent_inbound = " \n ".join(
        m["content"] for m in messages[-6:] if m["direction"] == "inbound"
    ).lower()
    kb_files = list(KB_ALWAYS)
    for keyword, files in KB_KEYWORDS.items():
        if keyword in recent_inbound:
            kb_files.extend(files)
    kb_content = ""
    seen = set()
    for rel in kb_files:
        if rel in seen:
            continue
        seen.add(rel)
        path = os.path.join(kb_dir, rel + ".md")
        if os.path.exists(path):
            kb_content += f"\n\n--- KB: {rel} ---\n{_read(path)}"

    # Conversation thread (last 12 messages)
    thread = ""
    for m in messages[-12:]:
        role = "Partner" if m["direction"] == "inbound" else "Us"
        thread += f"{role}: {m['content']}\n\n"

    playbook_directive = (
        "When a Playbook above provides a \"Canonical reply\", use that reply's wording "
        "as your response (you may adapt the partner's name and obvious context). Do NOT "
        "improvise a different answer, do NOT add a cross-sell or another company unless a "
        "HARD RULE explicitly calls for it, and follow any 'Do NOT' / 'CRITICAL' notes in "
        "that playbook."
        if playbooks else ""
    )

    prompt = f"""{system_base}

{guardrails}
{playbooks}

{playbook_directive}

{f"Tone and voice:{chr(10)}{tone}" if tone else ""}

{f"Campaign context:{chr(10)}{campaign_context}" if campaign_context else ""}

{f"Knowledge base:{chr(10)}{kb_content}" if kb_content else ""}

## Conversation so far
{thread}
{f"The partner's name is {first_name}." if first_name else ""}

Draft a reply to the partner's latest message. Output ONLY the message text: no quotes, no formatting, no JSON, and no explanation of your reasoning. Never narrate what you are doing or which rule applies. If a HARD RULE says to send nothing (closing acknowledgement or tapback), output an empty response: no text at all, not even a note that you are staying silent."""

    return prompt
