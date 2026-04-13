"""WebSocket connection manager — tracks clients and broadcasts messages."""

import json
import logging
from fastapi import WebSocket

logger = logging.getLogger("ws_manager")


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        self._connections.add(websocket)
        logger.info(f"WebSocket connected. Total clients: {len(self._connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self._connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total clients: {len(self._connections)}")

    async def broadcast(self, message: dict):
        """Send a message to all connected clients. Removes stale connections."""
        if not self._connections:
            return
        data = json.dumps(message)
        stale = set()
        for ws in self._connections:
            try:
                await ws.send_text(data)
            except Exception:
                stale.add(ws)
        for ws in stale:
            self._connections.discard(ws)
            logger.info(f"Removed stale WebSocket. Total clients: {len(self._connections)}")

    async def send_to(self, websocket: WebSocket, message: dict):
        """Send a message to a specific client."""
        await websocket.send_text(json.dumps(message))

    @property
    def client_count(self) -> int:
        return len(self._connections)


# Module-level singleton
manager = ConnectionManager()
