import json
import re
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import date, timedelta
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
        parsed = self._parse_intent_json(content)
        if parsed is not None:
            return self._normalize_intent(parsed)
        heuristic = self._infer_intent(message)
        if heuristic.intent != "unknown":
            return self._normalize_intent(heuristic)
        return IntentPayload(
            intent="unknown",
            question=message,
            reply="I can help with reservations, availability, customer lookup, and business questions. Please share the request details.",
        )

    @staticmethod
    def _parse_intent_json(content: str) -> IntentPayload | None:
        candidates = [content.strip()]
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            candidates.append(fenced.group(1).strip())
        object_match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if object_match:
            candidates.append(object_match.group(0).strip())

        for candidate in candidates:
            try:
                return IntentPayload.model_validate(json.loads(candidate))
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        return None

    @staticmethod
    def _normalize_intent(intent: IntentPayload) -> IntentPayload:
        data = intent.model_dump()
        lower_date = (intent.date or "").strip().lower()
        if lower_date in {"tomorrow", "yarın", "yarin"}:
            data["date"] = (date.today() + timedelta(days=1)).isoformat()
        elif lower_date in {"today", "bugün", "bugun"}:
            data["date"] = date.today().isoformat()

        raw_time = (intent.time or "").strip().lower()
        time_match = re.fullmatch(r"([01]?\d|2[0-3])[:.]([0-5]\d)(?:\s*(am|pm))?", raw_time)
        if time_match:
            hour = int(time_match.group(1))
            suffix = time_match.group(3)
            if suffix == "pm" and hour < 12:
                hour += 12
            elif suffix == "am" and hour == 12:
                hour = 0
            data["time"] = f"{hour:02d}:{time_match.group(2)}"
        else:
            hour_match = re.fullmatch(r"(\d{1,2})(?:\s*(?:pm|am))?", raw_time)
            if hour_match:
                hour = int(hour_match.group(1))
                if "pm" in raw_time and hour < 12:
                    hour += 12
                elif "am" not in raw_time and 1 <= hour <= 11:
                    hour += 12
                if 0 <= hour <= 23:
                    data["time"] = f"{hour:02d}:00"

        return IntentPayload.model_validate(data)

    @staticmethod
    def _infer_intent(message: str) -> IntentPayload:
        text = message.strip()
        lower = text.lower()
        reservation_terms = (
            "reservation",
            "reserve",
            "book",
            "table",
            "rezervasyon",
            "masa",
            "yer ayırt",
            "ayırt",
        )
        if not any(term in lower for term in reservation_terms):
            return IntentPayload(intent="unknown", question=text)

        customer_name = ""
        name_match = re.search(
            r"(?:my name is|name is|adım|adim|ismim|isim)\s+([A-Za-zÇĞİÖŞÜçğıöşü\s]{2,40}?)(?:\s+(?:and|ve)\s+|[.,!]|$)",
            text,
            flags=re.IGNORECASE,
        )
        if name_match:
            customer_name = name_match.group(1).strip(" .,!").title()

        phone = ""
        phone_match = re.search(r"(\+?\d[\d\s().-]{6,}\d)", text)
        if phone_match:
            phone = phone_match.group(1).strip()

        people = None
        people_match = re.search(
            r"(\d{1,2})\s*(?:people|person|guests|guest|kişilik|kisi|kişi|kisis?i|pax)",
            lower,
        )
        if people_match is None:
            people_match = re.search(r"(?:for|party of|table for)\s+(\d{1,2})\b", lower)
        if people_match:
            people = int(people_match.group(1))
        elif re.search(r"\b(two|iki)\b", lower):
            people = 2
        elif re.search(r"\b(three|üç|uc)\b", lower):
            people = 3
        elif re.search(r"\b(four|dört|dort)\b", lower):
            people = 4

        reservation_date = ""
        iso_date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        if iso_date_match:
            reservation_date = iso_date_match.group(1)
        elif any(term in lower for term in ("tomorrow", "yarın", "yarin")):
            reservation_date = (date.today() + timedelta(days=1)).isoformat()
        elif any(term in lower for term in ("today", "bugün", "bugun")):
            reservation_date = date.today().isoformat()

        reservation_time = ""
        time_match = re.search(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b", text)
        if time_match:
            reservation_time = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
        else:
            hour_match = re.search(r"(?:at|saat)\s*(\d{1,2})(?:'?(?:de|da|te|ta))?\b", lower)
            if hour_match is None:
                hour_match = re.search(r"\b(\d{1,2})(?:'?(?:de|da|te|ta))\b", lower)
            if hour_match:
                hour = int(hour_match.group(1))
                if 1 <= hour <= 11:
                    hour += 12
                if 0 <= hour <= 23:
                    reservation_time = f"{hour:02d}:00"

        try:
            return IntentPayload(
                intent="reservation_create",
                customer_name=customer_name,
                phone=phone,
                date=reservation_date,
                time=reservation_time,
                people=people,
                notes=text,
            )
        except ValueError:
            return IntentPayload(intent="reservation_create", notes=text)


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
