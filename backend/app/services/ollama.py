from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import settings


class OllamaConnectionError(RuntimeError):
    pass


class OllamaManager:
    def __init__(self, urls: list[str] | None = None):
        self.urls = urls or settings.ollama_urls

    async def resolve_url(self) -> str:
        for url in self.urls:
            if await self._is_available(url):
                return url
        raise OllamaConnectionError("Ollama is not reachable at any configured URL.")

    async def status(self) -> dict[str, Any]:
        try:
            url = await self.resolve_url()
        except OllamaConnectionError:
            return {"connected": False, "version": None, "url": None}
        version = None
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{url}/api/version")
            if response.status_code == 200:
                version = response.json().get("version")
        return {"connected": True, "version": version, "url": url}

    async def list_models(self) -> list[dict[str, Any]]:
        url = await self.resolve_url()
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{url}/api/tags")
            response.raise_for_status()
        models = response.json().get("models", [])
        return [
            {
                "name": model.get("name", ""),
                "size": model.get("size"),
                "modified_at": model.get("modified_at"),
                "digest": model.get("digest"),
                "details": model.get("details"),
            }
            for model in models
        ]

    async def pull(self, model: str) -> AsyncIterator[str]:
        url = await self.resolve_url()
        payload = {"model": model, "stream": True}
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{url}/api/pull", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield f"{line}\n"

    async def delete(self, model: str) -> dict[str, Any]:
        url = await self.resolve_url()
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request("DELETE", f"{url}/api/delete", json={"model": model})
            response.raise_for_status()
        return {"deleted": True, "model": model}

    async def _is_available(self, url: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.get(f"{url}/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False
