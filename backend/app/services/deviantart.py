from __future__ import annotations
import time
import httpx
from app.config import settings


class DeviantArtClient:
    TOKEN_URL = "https://www.deviantart.com/oauth2/token"
    API_BASE = "https://www.deviantart.com/api/v1/oauth2"

    def __init__(self):
        self._token: str | None = None
        self._token_expiry: float = 0

    async def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 60:
            return self._token

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.deviantart_client_id,
                    "client_secret": settings.deviantart_client_secret,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expiry = time.time() + data.get("expires_in", 3600)
            return self._token

    async def search(self, keywords: str, limit: int = 5) -> list[dict]:
        if not settings.deviantart_client_id or not settings.deviantart_client_secret:
            return []

        try:
            token = await self._get_token()
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.API_BASE}/browse/tags",
                    params={"tag": keywords, "limit": limit, "mature_content": "false"},
                    headers={"Authorization": f"Bearer {token}"},
                )
                resp.raise_for_status()
                data = resp.json()
                results = []
                for item in data.get("results", []):
                    content = item.get("content", {})
                    if content:
                        results.append(
                            {
                                "url": content.get("src", ""),
                                "title": item.get("title", ""),
                                "author": item.get("author", {}).get("username", ""),
                                "page_url": item.get("url", ""),
                            }
                        )
                return results
        except Exception:
            return []


deviantart_client = DeviantArtClient()
