from __future__ import annotations
import hashlib
import httpx
from pathlib import Path
from app.config import settings

SCENE_AUDIO_MAP: dict[str, str] = {
    "tavern": "tavern ambience medieval",
    "forest": "forest ambience birds",
    "cave": "cave dripping water ambience",
    "dungeon": "dungeon ambience torch",
    "combat": "battle drums tense",
    "ocean": "ocean waves sea",
    "city": "medieval city market ambience",
    "rain": "rain storm ambience",
    "castle": "castle hall medieval ambience",
    "graveyard": "graveyard night ambient",
}


def _match_scene(keywords: list[str]) -> str:
    for kw in keywords:
        for scene_key, query in SCENE_AUDIO_MAP.items():
            if scene_key in kw.lower():
                return query
    return "fantasy ambient music"


class FreesoundClient:
    API_BASE = "https://freesound.org/apiv2"

    async def search(self, query: str) -> dict | None:
        if not settings.freesound_api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.API_BASE}/search/text/",
                    params={
                        "query": query,
                        "filter": "duration:[30 TO 300] type:mp3",
                        "fields": "id,name,previews,username,license",
                        "page_size": 5,
                        "token": settings.freesound_api_key,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if results:
                    return results[0]
                return None
        except Exception:
            return None

    async def get_audio_for_scene(self, keywords: list[str]) -> dict | None:
        query = _match_scene(keywords)
        return await self.search(query)

    async def download_preview(self, preview_url: str, sound_id: int) -> str | None:
        filename = f"sound_{sound_id}.mp3"
        dest = settings.audio_cache_dir / filename
        if dest.exists():
            return filename

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(preview_url)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
                return filename
        except Exception:
            return None


freesound_client = FreesoundClient()
