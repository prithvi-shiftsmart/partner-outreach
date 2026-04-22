"""Auto-draft service — generates reply drafts via Claude CLI subprocess."""

import asyncio
import json
import logging
import os
import re

from server.config import CLAUDE_CLI_PATH, CONFIG_DIR, WORKSPACE
from server.database import get_db

logger = logging.getLogger("draft_service")

# Keywords to knowledge base file mapping
KB_KEYWORDS = {
    "orientation": ["orientation_logistics", "orientation_process", "in_app_orientation_walkthrough"],
    "pay": ["pay_rates", "pay_and_bonuses", "payment_issues", "shift_discovery_and_bonuses"],
    "shift": ["shift_info", "how_shifts_work", "shift_discovery_and_bonuses"],
    "trust": ["trust_and_identity"],
    "app": ["app_issues"],
    "food": ["food_prep_guide", "food_prep_shift"],
    "account": ["account_and_reliability", "platform_policies"],
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

        # Load tone rules
        tone = ""
        tone_path = os.path.join(CONFIG_DIR, "tone_and_voice.md")
        if os.path.exists(tone_path):
            with open(tone_path) as f:
                tone = f.read()

        # Load relevant knowledge base files
        kb_content = ""
        latest_inbound = messages[-1]["content"] if messages else ""
        kb_dir = os.path.join(CONFIG_DIR, "knowledge_base")
        if os.path.exists(kb_dir):
            loaded = set()
            # Always load orientation basics
            for base in ["orientation_logistics", "orientation_process"]:
                path = os.path.join(kb_dir, f"{base}.md")
                if os.path.exists(path) and base not in loaded:
                    with open(path) as f:
                        kb_content += f"\n\n--- {base} ---\n{f.read()}"
                    loaded.add(base)

            # Keyword-matched files
            for keyword, files in KB_KEYWORDS.items():
                if keyword.lower() in latest_inbound.lower():
                    for fname in files:
                        path = os.path.join(kb_dir, f"{fname}.md")
                        if os.path.exists(path) and fname not in loaded:
                            with open(path) as f:
                                kb_content += f"\n\n--- {fname} ---\n{f.read()}"
                            loaded.add(fname)

        # Build conversation string
        thread = ""
        for m in messages[-12:]:  # Last 12 messages
            role = "Partner" if m["direction"] == "inbound" else "Us"
            thread += f"{role}: {m['content']}\n\n"

        prompt = f"""You are a friendly SMS concierge for Shiftsmart, helping partners get oriented and start working shifts.

{f"Tone and voice guidelines:{chr(10)}{tone}" if tone else ""}

{f"Campaign context:{chr(10)}{campaign_context}" if campaign_context else ""}

{f"Knowledge base:{chr(10)}{kb_content}" if kb_content else ""}

Rules:
- Keep responses under 160 characters when possible (SMS)
- Never use "gig" — say "shift"
- Never use "employee" or "training" — say "partner" and "orientation"
- Never promise specific pay rates
- Never offer to submit support tickets — tell them to use the app
- Use their name sparingly (1 in 3 messages)
- Don't repeat information already shared in the conversation
- Be direct and helpful, not corporate-cheery

Conversation so far:
{thread}

{f"The partner's name is {first_name}." if first_name else ""}

Draft a reply to the partner's latest message. Just the message text, no quotes or formatting."""

        return prompt
