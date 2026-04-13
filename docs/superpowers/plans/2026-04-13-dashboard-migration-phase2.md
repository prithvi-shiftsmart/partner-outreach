# Dashboard Migration Phase 2: WebSocket + Sync + Auto-Draft

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real-time updates via WebSocket — background sync polls Salesmsg, pushes new messages to browser, auto-drafts replies via Claude CLI.

**Architecture:** Async sync service polls Salesmsg every 20s → stores new messages → triggers auto-draft → broadcasts to WebSocket clients. All async to avoid blocking the event loop.

**Tech Stack:** FastAPI WebSocket, httpx (async HTTP), asyncio, Claude CLI subprocess

**Depends on:** Phase 1 complete (server/, database, REST endpoints)

---

## Tasks

### Task 1: Add httpx dependency and WS protocol models

- Add `httpx>=0.27.0` to requirements.txt, install
- Add WebSocket message models to server/models.py (WSNewMessage, WSDraftReady, WSSyncStatus, WSUnreadUpdate, WSBatchProgress)

### Task 2: Salesmsg API Client

- Create `server/services/salesmsg_client.py`
- Async httpx client with methods: list_conversations, get_messages, send_message
- Re-reads token on each call for hot-reload
- Rate limit handling (read x-ratelimit-remaining-minute, sleep on 429)

### Task 3: WebSocket Connection Manager

- Create `server/ws/manager.py`
- ConnectionManager class: connect, disconnect, broadcast, send_to
- Module-level singleton

### Task 4: WebSocket Endpoint

- Create `server/ws/handlers.py`
- /ws endpoint, handles mark_read messages
- Wire into main.py

### Task 5: Sync Service

- Create `server/services/sync_service.py`
- Background async task polling every 20s
- Fixed pagination (not hardcoded limit=20)
- Opt-out detection, auto-respond check
- Broadcasts new_message and unread_update via WebSocket
- Logs sync metrics

### Task 6: Draft Service

- Create `server/services/draft_service.py`
- Response cache check → Claude CLI subprocess fallback
- Max 2 concurrent drafts via semaphore
- Broadcasts draft_ready via WebSocket

### Task 7: Wire everything into main.py

- Convert to lifespan pattern
- Start sync + draft services on startup
- Store on app.state
- Update sync routes to use sync service instead of subprocess

### Task 8: End-to-end verification

- Start server, verify sync runs, verify WebSocket broadcasts, verify draft pipeline
