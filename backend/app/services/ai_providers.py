import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.intents import IntentPayload
from app.services.ollama import OllamaManager


INTENT_SYSTEM_PROMPT = """You are an intent detection engine for a restaurant voice agent.
Return only valid JSON. Do not include markdown, comments, or prose.
Allowed intents: reservation_create, reservation_update, reservation_cancel,
reservation_lookup, faq, customer_lookup, admin_report, unknown.
Use empty strings for missing text fields and null for missing numbers.
Schema:
{
  "intent": "reservation_create",
  "customer_name": "",
  "phone": "",
  "email": "",
  "date": "YYYY-MM-DD or natural language if exact date is unknown",
  "time": "HH:MM or natural language if exact time is unknown",
  "people": 2,
  "reservation_id": null,
  "notes": "",
  "question": "",
  "reply": ""
}
"""


class AIProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, model: str, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def list_models(self) -> list[dict[str, str]]:
        raise NotImplementedError

    async def stream(self, model: str, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        yield await self.generate(model, messages)

    async def detect_intent(self, model: str, message: str) -> IntentPayload:
        content = await self.generate(
            model=model,
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
        )
        try:
            return IntentPayload.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValueError, TypeError):
            return IntentPayload(
                intent="unknown",
                question=message,
                reply="I could not safely understand that request. Please rephrase it with the key details.",
            )


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url.rstrip("/") if base_url else None

    async def _base_url(self) -> str:
        return self.base_url or await OllamaManager().resolve_url()

    async def generate(self, model: str, messages: list[dict[str, str]]) -> str:
        base_url = await self._base_url()
        payload = {
            "model": model,
            "stream": False,
            "format": "json",
            "messages": messages,
            "options": {"temperature": 0},
        }
        async with httpx.AsyncClient(timeout=settings.ollama_request_timeout_seconds) as client:
            response = await client.post(f"{base_url}/api/chat", json=payload)
            response.raise_for_status()
        return response.json()["message"]["content"]

    async def health(self) -> dict[str, Any]:
        status = await OllamaManager([self.base_url] if self.base_url else None).status()
        return {"ok": status["connected"], "url": status["url"], "version": status["version"]}

    async def list_models(self) -> list[dict[str, str]]:
        models = await OllamaManager([self.base_url] if self.base_url else None).list_models()
        return [{"name": model["name"]} for model in models]

    async def stream(self, model: str, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        base_url = await self._base_url()
        payload = {"model": model, "stream": True, "messages": messages}
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    content = data.get("message", {}).get("content")
                    if content:
                        yield content


class LMStudioProvider(AIProvider):
    name = "lmstudio"

    def __init__(self, base_url: str = settings.lmstudio_base_url):
        self.base_url = base_url.rstrip("/")

    async def generate(self, model: str, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=settings.ollama_request_timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/v1/chat/completions", json=payload)
            response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{self.base_url}/v1/models")
        return {"ok": response.status_code == 200, "status_code": response.status_code}

    async def list_models(self) -> list[dict[str, str]]:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{self.base_url}/v1/models")
            response.raise_for_status()
        return [{"name": model["id"]} for model in response.json().get("data", [])]

    async def stream(self, model: str, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        payload = {"model": model, "messages": messages, "temperature": 0, "stream": True}
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{self.base_url}/v1/chat/completions", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk = line.removeprefix("data: ").strip()
                    if chunk == "[DONE]":
                        break
                    data = json.loads(chunk)
                    content = data["choices"][0].get("delta", {}).get("content")
                    if content:
                        yield content


PROVIDER_REGISTRY: dict[str, type[AIProvider]] = {
    OllamaProvider.name: OllamaProvider,
    LMStudioProvider.name: LMStudioProvider,
}


def create_provider(provider_name: str) -> AIProvider:
    provider_cls = PROVIDER_REGISTRY.get(provider_name)
    if provider_cls is None:
        raise ValueError(f"Unsupported provider: {provider_name}")
    return provider_cls()
