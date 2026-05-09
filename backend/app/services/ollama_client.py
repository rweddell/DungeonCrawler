from __future__ import annotations
import json
from collections.abc import AsyncGenerator
import httpx
from app.config import settings


class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_base_url

    async def list_models(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return data.get("models", [])

    async def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        stream: bool = False,
        options: dict | None = None,
    ) -> str:
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")

    async def chat(
        self,
        model: str,
        messages: list[dict],
        stream: bool = False,
        options: dict | None = None,
    ) -> str:
        payload: dict = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if options:
            payload["options"] = options

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")


    async def chat_stream(
        self,
        model: str,
        messages: list[dict],
        options: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        payload: dict = {"model": model, "messages": messages, "stream": True}
        if options:
            payload["options"] = options

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        chunk: str = data.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue


ollama_client = OllamaClient()
