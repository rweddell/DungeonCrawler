from __future__ import annotations
import asyncio
import time
import requests
from app.config import settings
from logging import getLogger

logger = getLogger(__name__)

# Keywords to exclude from image searches (proper names, specific references, inappropriate terms)
EXCLUDED_KEYWORDS = {
    "child",
    "children",
    "baby",
    "infant",
    "toddler",
    "weeping",
}


def filter_keywords(keywords: list[str]) -> list[str]:
    """
    Filter out proper names, specific references, and excluded terms from keyword list.
    Returns only generic, usable keywords for image searches.
    """
    filtered = ['scene']
    for keyword in keywords:
        keyword_lower = keyword.lower().strip()
        
        # Skip empty keywords
        if not keyword_lower:
            continue
        
        # Skip if keyword is in the exclusion list
        if keyword_lower in EXCLUDED_KEYWORDS:
            continue
        
        # Skip multi-word phrases that start with capital letters (likely proper names)
        # e.g., "Weeping Child", "Dark Forest" (but keep lowercase or single words)
        if " " in keyword and keyword[0].isupper():
            # This is a multi-word phrase starting with capital letter — likely a proper name
            continue
        
        filtered.append(keyword)
    
    return filtered


class DeviantArtClient:
    TOKEN_URL = "https://www.deviantart.com/oauth2/token"
    API_BASE = "https://www.deviantart.com/api/v1/oauth2"

    def __init__(self):
        self._token: str | None = None
        self._token_expiry: float = 0

    def _fetch_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 60:
            return self._token

        resp = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.deviantart_client_id,
                "client_secret": settings.deviantart_client_secret,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        token: str = data["access_token"]
        self._token = token
        self._token_expiry = time.time() + data.get("expires_in", 3600)
        return token

    def _search_sync(self, keywords: str, limit: int) -> list[dict]:
        keyword_list = [k.strip() for k in keywords.split(",")]
        filtered_keywords = filter_keywords(keyword_list)

        if not filtered_keywords:
            logger.info(f"All keywords filtered out from: {keywords}")
            return []

        # browse/tags takes a single tag — pick the most specific keyword.
        # filter_keywords always prepends 'scene', so prefer index 1+ when available.
        tag = filtered_keywords[1] if len(filtered_keywords) > 1 else filtered_keywords[0]
        token = self._fetch_token()

        resp = requests.get(
            f"{self.API_BASE}/browse/tags",
            params={"tag": tag, "limit": limit, "mature_content": "false"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
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

    async def search(self, keywords: str, limit: int = 5) -> list[dict]:
        if not settings.deviantart_client_id or not settings.deviantart_client_secret:
            return []

        try:
            return await asyncio.to_thread(self._search_sync, keywords, limit)
        except Exception as ex:
            logger.exception(f"Error occurred while searching DeviantArt: {ex}")
            return []


deviantart_client = DeviantArtClient()
