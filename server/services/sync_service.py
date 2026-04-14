"""Background sync service — polls Salesmsg API, syncs messages, broadcasts via WebSocket."""

import asyncio
import json
import logging
import re
import time

from server.config import DEFAULT_SYNC_INTERVAL
from server.database import get_db

logger = logging.getLogger("sync_service")

# Opt-out keywords (exact match, case-insensitive)
OPT_OUT_KEYWORDS = {"stop", "unsubscribe", "opt out", "cancel", "quit", "end"}


class SyncService:
    """Polls Salesmsg API and syncs inbound messages to SQLite."""

    def __init__(self, salesmsg_client, ws_manager, draft_service=None):
        self._client = salesmsg_client
        self._ws = ws_manager
        self._draft = draft_service
        self._running = False
        self._task = None
        self._last_sync_at = None
        self._syncing = False

    async def start(self):
        """Start the background polling loop."""
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Sync service started")

    async def stop(self):
        """Stop the polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Sync service stopped")

    async def trigger(self, mode="quick"):
        """Trigger a one-off sync cycle (for manual sync buttons)."""
        asyncio.create_task(self._sync_cycle(mode))

    async def _loop(self):
        """Main polling loop."""
        # Initial sync on startup
        await asyncio.sleep(2)  # Let app finish starting
        while self._running:
            try:
                interval = self._get_sync_interval()
                await self._sync_cycle("quick")
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync loop error: {e}", exc_info=True)
                await asyncio.sleep(10)  # Back off on error

    def _get_sync_interval(self) -> int:
        """Read sync interval from app_settings, default to config value."""
        try:
            with get_db() as conn:
                row = conn.execute(
                    "SELECT value FROM app_settings WHERE key = 'sync_interval'"
                ).fetchone()
                if row:
                    return int(row["value"])
        except Exception:
            pass
        return DEFAULT_SYNC_INTERVAL

    async def _sync_cycle(self, mode="quick"):
        """Run one sync cycle."""
        if self._syncing:
            logger.info("Sync already in progress, skipping")
            return
        self._syncing = True
        start_time = time.time()
        conversations_synced = 0
        messages_found = 0
        pages_scanned = 0

        try:
            # Get our tracked phone numbers
            our_phones = await asyncio.to_thread(self._get_tracked_phones)
            if not our_phones:
                logger.info("No tracked phones, skipping sync")
                return

            # Get last sync time
            last_sync = await asyncio.to_thread(self._get_last_sync_time)

            # Page through conversations
            page = 1
            while True:
                try:
                    convos = await self._client.list_conversations(page=page, limit=50)
                except Exception as e:
                    logger.error(f"Failed to list conversations page {page}: {e}")
                    break

                pages_scanned += 1
                if not convos or not isinstance(convos, list):
                    break

                for conv in convos:
                    # Extract phone from conversation contact
                    contact = conv.get("contact", {}) if isinstance(conv, dict) else {}
                    phone = contact.get("number") or contact.get("phone") or ""
                    if not phone or phone not in our_phones:
                        continue

                    conv_id = str(conv.get("id", ""))
                    if not conv_id:
                        continue

                    # Sync messages for this conversation
                    new_msgs = await self._sync_conversation(conv_id, phone, last_sync, mode)
                    if new_msgs > 0:
                        conversations_synced += 1
                        messages_found += new_msgs

                # Pagination stop conditions
                if len(convos) < 50:
                    break  # Last page
                if mode == "quick" and pages_scanned >= 2:
                    break  # Quick mode: max 2 pages
                page += 1
                await asyncio.sleep(0.5)  # Rate limit courtesy

            # Log sync metrics
            duration = time.time() - start_time
            await asyncio.to_thread(
                self._log_sync, conversations_synced, messages_found, pages_scanned, mode, duration
            )
            self._last_sync_at = time.time()

            # Broadcast sync status
            await self._ws.broadcast({
                "type": "sync_status",
                "mode": mode,
                "status": "completed",
                "conversations_synced": conversations_synced,
                "messages_found": messages_found,
                "pages_scanned": pages_scanned,
                "duration_seconds": round(duration, 1),
            })

            if messages_found > 0:
                logger.info(f"Sync complete: {conversations_synced} convos, {messages_found} new messages, {pages_scanned} pages, {duration:.1f}s")

        except Exception as e:
            logger.error(f"Sync cycle error: {e}", exc_info=True)
            await self._ws.broadcast({
                "type": "sync_status", "mode": mode, "status": "error",
                "conversations_synced": conversations_synced, "messages_found": messages_found,
                "pages_scanned": pages_scanned, "duration_seconds": round(time.time() - start_time, 1),
            })
        finally:
            self._syncing = False

    async def _sync_conversation(self, conv_id: str, phone: str, last_sync: str, mode: str) -> int:
        """Sync messages for a single conversation. Returns count of new messages."""
        new_count = 0
        page = 1
        max_pages = 2 if mode == "quick" else 10

        while page <= max_pages:
            try:
                messages = await self._client.get_messages(conv_id, page=page, limit=50)
            except Exception as e:
                logger.error(f"Failed to get messages for conv {conv_id} page {page}: {e}")
                break

            if not messages:
                break

            for msg in messages:
                msg_id = str(msg.get("id", ""))
                if not msg_id:
                    continue

                reply_id = f"sm_{msg_id}"

                # Check if already synced
                exists = await asyncio.to_thread(self._message_exists, reply_id)
                if exists:
                    continue

                # Determine direction
                status = msg.get("status", "")
                msg_type = msg.get("type", "")
                body = msg.get("body_raw") or msg.get("body") or ""
                created_at = msg.get("created_at") or msg.get("send_at") or ""

                # "received" status = inbound, "sent"/"delivered" = outbound
                if status in ("received",) or msg_type == "incoming":
                    direction = "inbound"
                else:
                    direction = "outbound"

                # Extract media URLs (MMS support)
                media_urls = []
                media = msg.get("media", [])
                if isinstance(media, list):
                    for m in media:
                        if isinstance(m, dict):
                            url = m.get("url") or m.get("original_url") or m.get("link")
                            if url:
                                media_urls.append(url)
                        elif isinstance(m, str):
                            media_urls.append(m)

                # Strip HTML from body
                clean_body = re.sub(r'<[^>]+>', '', body).strip()
                if not clean_body:
                    continue

                # Get partner_id for this phone
                partner_id = await asyncio.to_thread(self._get_partner_id, phone)
                if not partner_id:
                    continue

                # Store in database
                await asyncio.to_thread(
                    self._store_message, reply_id, conv_id, partner_id, direction,
                    clean_body, created_at, media_urls, phone
                )
                new_count += 1

                if direction == "inbound":
                    # Check opt-out
                    if clean_body.strip().lower() in OPT_OUT_KEYWORDS:
                        await asyncio.to_thread(self._mark_opt_out, partner_id)
                        logger.info(f"Opt-out detected for {partner_id}")
                    else:
                        # Check auto-respond
                        await self._check_auto_respond(partner_id, clean_body, conv_id, phone)

                        # Auto-draft disabled — user clicks Draft Reply manually

                    # Get partner name for broadcast
                    name = await asyncio.to_thread(self._get_partner_name, partner_id)
                    campaign = await asyncio.to_thread(self._get_partner_campaign, partner_id)

                    # Broadcast new message
                    await self._ws.broadcast({
                        "type": "new_message",
                        "partner_id": partner_id,
                        "content": clean_body,
                        "media_urls": media_urls if media_urls else None,
                        "campaign_id": campaign,
                        "timestamp": created_at,
                        "direction": "inbound",
                        "partner_name": name,
                        "phone": phone,
                    })

                    # Broadcast updated unread counts
                    counts = await asyncio.to_thread(self._get_unread_counts)
                    await self._ws.broadcast({"type": "unread_update", **counts})

            if len(messages) < 50:
                break
            page += 1
            await asyncio.sleep(0.3)

        return new_count

    async def _check_auto_respond(self, partner_id: str, content: str, conv_id: str, phone: str):
        """Check if this message matches auto-respond patterns for the partner's campaign."""
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "_config", "auto_responses.json")
        if not os.path.exists(config_path):
            return

        try:
            with open(config_path) as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            return

        # Get campaign for this partner
        campaign = await asyncio.to_thread(self._get_partner_campaign, partner_id)
        if not campaign:
            return

        # Check if auto-respond is enabled for this campaign
        with get_db() as conn:
            row = conn.execute(
                "SELECT auto_respond_enabled FROM campaign_context WHERE campaign_id = ?",
                (campaign,)
            ).fetchone()
            if not row or not row["auto_respond_enabled"]:
                return

        # Check patterns
        patterns = config.get("simple_reply_patterns", [])
        content_lower = content.strip().lower()
        matched = any(re.match(p, content_lower, re.IGNORECASE) for p in patterns)
        if not matched:
            return

        # Get auto-response text
        campaigns_cfg = config.get("campaigns", {})
        response = campaigns_cfg.get(campaign, campaigns_cfg.get("_default", {})).get("response", "")
        if not response:
            return

        # Check if we already auto-responded
        with get_db() as conn:
            already = conn.execute(
                "SELECT 1 FROM reply_chain WHERE partner_id = ? AND classified_intent IN ('auto_simple', 'auto_response') LIMIT 1",
                (partner_id,)
            ).fetchone()
            if already:
                return

        # Send auto-response
        try:
            await self._client.send_message(phone, response)
            # Log it
            with get_db() as conn:
                from datetime import datetime
                reply_id = f"auto_{datetime.now().strftime('%Y%m%d%H%M%S')}_{partner_id[-6:]}"
                conn.execute("""
                    INSERT OR IGNORE INTO reply_chain
                    (reply_id, parent_message_id, partner_id, direction, content,
                     classified_intent, response_approved, logged_at, notes)
                    VALUES (?, ?, ?, 'outbound', ?, 'auto_response', 1, datetime('now'), ?)
                """, (reply_id, f"conv_{conv_id}", partner_id, response,
                      json.dumps({"salesmsg_conv_id": conv_id})))
                conn.commit()
            logger.info(f"Auto-responded to {partner_id}")
        except Exception as e:
            logger.error(f"Auto-respond failed for {partner_id}: {e}")

    # --- Database helper methods (run in thread) ---

    def _get_tracked_phones(self) -> set:
        """Only track phones for partners WE messaged (exist in message_log)."""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT DISTINCT pc.phone_number
                FROM partner_conversations pc
                WHERE pc.phone_number IS NOT NULL
                AND pc.partner_id IN (SELECT DISTINCT partner_id FROM message_log)
            """).fetchall()
            return {r["phone_number"] for r in rows}

    def _get_last_sync_time(self) -> str:
        with get_db() as conn:
            row = conn.execute(
                "SELECT last_sync_at FROM salesmsg_sync ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return row["last_sync_at"] if row else ""

    def _message_exists(self, reply_id: str) -> bool:
        with get_db() as conn:
            return conn.execute(
                "SELECT 1 FROM reply_chain WHERE reply_id = ?", (reply_id,)
            ).fetchone() is not None

    def _get_partner_id(self, phone: str) -> str:
        with get_db() as conn:
            row = conn.execute(
                "SELECT partner_id FROM partner_conversations WHERE phone_number = ?", (phone,)
            ).fetchone()
            return row["partner_id"] if row else ""

    def _get_partner_name(self, partner_id: str) -> str:
        with get_db() as conn:
            row = conn.execute(
                "SELECT first_name, last_name FROM partner_conversations WHERE partner_id = ?",
                (partner_id,)
            ).fetchone()
            if row:
                parts = [row["first_name"] or "", row["last_name"] or ""]
                return " ".join(p for p in parts if p).strip() or None
            return None

    def _get_partner_campaign(self, partner_id: str) -> str:
        with get_db() as conn:
            row = conn.execute(
                "SELECT campaign_id FROM message_log WHERE partner_id = ? ORDER BY COALESCE(sent_at, logged_at) DESC LIMIT 1",
                (partner_id,)
            ).fetchone()
            return row["campaign_id"] if row else ""

    def _store_message(self, reply_id, conv_id, partner_id, direction, content, timestamp, media_urls, phone):
        with get_db() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO reply_chain
                (reply_id, parent_message_id, partner_id, direction, content,
                 logged_at, media_urls, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (reply_id, f"conv_{conv_id}", partner_id, direction, content,
                  timestamp, json.dumps(media_urls) if media_urls else None,
                  json.dumps({"salesmsg_conv_id": conv_id, "phone": phone})))
            if direction == "inbound":
                conn.execute("""
                    UPDATE partner_conversations
                    SET last_message_at = ?, updated_at = datetime('now')
                    WHERE partner_id = ?
                """, (timestamp, partner_id))
            conn.commit()

    def _mark_opt_out(self, partner_id: str):
        with get_db() as conn:
            conn.execute("""
                UPDATE partner_conversations
                SET do_not_message = 1, dnm_reason = 'opt_out', dnm_at = datetime('now')
                WHERE partner_id = ?
            """, (partner_id,))
            conn.commit()

    def _get_unread_counts(self) -> dict:
        with get_db() as conn:
            rows = conn.execute("""
                SELECT partner_id, COUNT(*) AS cnt
                FROM reply_chain
                WHERE direction = 'inbound' AND response_approved = 0
                GROUP BY partner_id
            """).fetchall()
            by_partner = {r["partner_id"]: r["cnt"] for r in rows}
            return {"total_unread": sum(by_partner.values()), "by_partner": by_partner}

    def _log_sync(self, convos, msgs, pages, mode, duration):
        with get_db() as conn:
            conn.execute("""
                INSERT INTO salesmsg_sync
                (last_sync_at, conversations_synced, messages_synced, pages_scanned, mode, duration_seconds)
                VALUES (datetime('now'), ?, ?, ?, ?, ?)
            """, (convos, msgs, pages, mode, round(duration, 1)))
            conn.commit()
