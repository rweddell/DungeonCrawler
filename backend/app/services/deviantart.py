from __future__ import annotations
import time
import httpx
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
    "barovia",
    "strahd",
    "weeping",
}


def filter_keywords(keywords: list[str]) -> list[str]:
    """
    Filter out proper names, specific references, and excluded terms from keyword list.
    Returns only generic, usable keywords for image searches.
    """
    filtered = []
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
            # Parse and filter keywords
            keyword_list = [k.strip() for k in keywords.split(",")]
            filtered_keywords = filter_keywords(keyword_list)
            
            # If no keywords remain after filtering, return empty
            if not filtered_keywords:
                logger.info(f"All keywords filtered out from: {keywords}")
                return []
            
            # Rejoin filtered keywords for the API call
            clean_keywords = ",".join(filtered_keywords)
            
            token = await self._get_token()
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.API_BASE}/browse/tags",
                    params={"tag": clean_keywords, "limit": limit, "mature_content": "false"},
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
        except Exception as ex:
            logger.exception(f"Error occurred while searching DeviantArt: {ex}")
            return []


deviantart_client = DeviantArtClient()
