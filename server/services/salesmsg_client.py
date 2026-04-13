"""Async Salesmsg API client with rate limiting and token refresh."""

import asyncio
import logging

import httpx

from server.config import SALESMSG_API_URL, reload_token, get_token_expiry

logger = logging.getLogger("salesmsg_client")


class SalesmsgAPIError(Exception):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Salesmsg API error {status_code}: {body[:200]}")


class SalesmsgClient:
    """Async client for the Salesmsg API v2.2."""

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=30.0)

    def _headers(self) -> dict:
        """Build headers with fresh token."""
        token = reload_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(self, method: str, endpoint: str, params: dict = None, json_data: dict = None) -> dict:
        """Make an API request with rate limit handling."""
        url = f"{SALESMSG_API_URL}/{endpoint}"
        headers = self._headers()

        resp = await self._client.request(method, url, headers=headers, params=params, json=json_data)

        # Check rate limit headers
        remaining = resp.headers.get("x-ratelimit-remaining-minute")
        if remaining is not None:
            try:
                if int(remaining) < 5:
                    logger.info(f"Rate limit low ({remaining} remaining), sleeping 2s")
                    await asyncio.sleep(2)
            except ValueError:
                pass

        # Handle 429
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "10"))
            logger.warning(f"Rate limited (429). Waiting {retry_after}s...")
            await asyncio.sleep(retry_after)
            resp = await self._client.request(method, url, headers=headers, params=params, json=json_data)

        if resp.status_code == 403:
            logger.error(f"403 Forbidden — token may be expired. Endpoint: {endpoint}")
            raise SalesmsgAPIError(403, resp.text)

        if resp.status_code >= 400:
            raise SalesmsgAPIError(resp.status_code, resp.text)

        return resp.json()

    async def list_conversations(self, page: int = 1, limit: int = 50, filter_type: str = "open") -> list:
        """List conversations. Returns list of conversation dicts."""
        data = await self._request("GET", "conversations", params={
            "filter": filter_type, "limit": limit, "page": page
        })
        # API returns either {"data": [...]} or bare list
        if isinstance(data, dict):
            return data.get("data", [])
        return data if isinstance(data, list) else []

    async def get_messages(self, conversation_id: str, page: int = 1, limit: int = 50) -> list:
        """Get messages for a conversation. Returns list of message dicts."""
        data = await self._request("GET", f"messages/{conversation_id}", params={
            "limit": limit, "page": page
        })
        if isinstance(data, dict):
            return data.get("data", [])
        return data if isinstance(data, list) else []

    async def get_all_messages(self, conversation_id: str, limit: int = 50, max_pages: int = 10) -> list:
        """Paginate through all messages for a conversation. Fixes the hardcoded limit=20 bug."""
        all_messages = []
        for page in range(1, max_pages + 1):
            messages = await self.get_messages(conversation_id, page=page, limit=limit)
            all_messages.extend(messages)
            if len(messages) < limit:
                break  # Last page
            await asyncio.sleep(0.5)  # Rate limit courtesy
        return all_messages

    async def send_message(self, phone: str, message: str, team_id: int = None) -> dict:
        """Send a message via POST /messages."""
        payload = {"number": phone, "message": message}
        if team_id:
            payload["team_id"] = team_id
        return await self._request("POST", "messages", json_data=payload)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
