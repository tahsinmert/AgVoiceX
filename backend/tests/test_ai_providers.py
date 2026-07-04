import json

import pytest

from app.services.ai_providers import LMStudioProvider, OllamaProvider


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeAsyncClient:
    requests: list[tuple[str, str, dict | None]] = []
    responses: list[FakeResponse] = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def get(self, url: str):
        self.requests.append(("GET", url, None))
        return self.responses.pop(0)

    async def post(self, url: str, json: dict):
        self.requests.append(("POST", url, json))
        return self.responses.pop(0)


@pytest.fixture(autouse=True)
def fake_httpx(monkeypatch):
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = []
    monkeypatch.setattr("app.services.ai_providers.httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr("app.services.ollama.httpx.AsyncClient", FakeAsyncClient)


@pytest.mark.asyncio
async def test_ollama_provider_lists_models():
    FakeAsyncClient.responses = [
        FakeResponse({"models": []}),
        FakeResponse({"models": [{"name": "local-model-a"}, {"name": "local-model-b"}]})
    ]

    models = await OllamaProvider(base_url="http://ollama:11434").list_models()

    assert models == [{"name": "local-model-a"}, {"name": "local-model-b"}]
    assert FakeAsyncClient.requests == [
        ("GET", "http://ollama:11434/api/tags", None),
        ("GET", "http://ollama:11434/api/tags", None),
    ]


@pytest.mark.asyncio
async def test_lmstudio_provider_lists_models():
    FakeAsyncClient.responses = [
        FakeResponse({"data": [{"id": "lmstudio-model-a"}, {"id": "lmstudio-model-b"}]})
    ]

    models = await LMStudioProvider(base_url="http://localhost:1234").list_models()

    assert models == [{"name": "lmstudio-model-a"}, {"name": "lmstudio-model-b"}]
    assert FakeAsyncClient.requests == [("GET", "http://localhost:1234/v1/models", None)]


@pytest.mark.asyncio
async def test_ollama_generate_uses_selected_model():
    FakeAsyncClient.responses = [
        FakeResponse({"message": {"content": json.dumps({"intent": "unknown"})}}),
    ]

    content = await OllamaProvider(base_url="http://ollama:11434").generate(
        model="selected-local-model",
        messages=[{"role": "user", "content": "hello"}],
    )

    assert json.loads(content) == {"intent": "unknown"}
    method, url, payload = FakeAsyncClient.requests[0]
    assert method == "POST"
    assert url == "http://ollama:11434/api/chat"
    assert payload["model"] == "selected-local-model"


@pytest.mark.asyncio
async def test_lmstudio_generate_uses_selected_model():
    FakeAsyncClient.responses = [
        FakeResponse({"choices": [{"message": {"content": json.dumps({"intent": "unknown"})}}]})
    ]

    content = await LMStudioProvider(base_url="http://localhost:1234").generate(
        model="selected-openai-compatible-model",
        messages=[{"role": "user", "content": "hello"}],
    )

    assert json.loads(content) == {"intent": "unknown"}
    method, url, payload = FakeAsyncClient.requests[0]
    assert method == "POST"
    assert url == "http://localhost:1234/v1/chat/completions"
    assert payload["model"] == "selected-openai-compatible-model"


def test_intent_parser_accepts_fenced_json():
    intent = OllamaProvider._parse_intent_json(
        """```json
        {"intent":"reservation_create","customer_name":"Ada","phone":"5550101","date":"2026-07-10","time":"19:00","people":2}
        ```"""
    )

    assert intent is not None
    assert intent.intent == "reservation_create"
    assert intent.customer_name == "Ada"


def test_intent_normalizer_converts_natural_date_and_time():
    intent = OllamaProvider._parse_intent_json(
        """{"intent":"reservation_create","customer_name":"Ada","phone":"5550101","date":"tomorrow","time":"7","people":2}"""
    )

    assert intent is not None
    normalized = OllamaProvider._normalize_intent(intent)
    assert normalized.date != "tomorrow"
    assert normalized.time == "19:00"

    intent_pm = OllamaProvider._parse_intent_json(
        """{"intent":"reservation_create","date":"tomorrow","time":"7:00 PM","people":2}"""
    )
    assert intent_pm is not None
    assert OllamaProvider._normalize_intent(intent_pm).time == "19:00"


def test_intent_parser_infers_reservation_when_model_output_is_invalid():
    intent = OllamaProvider._infer_intent(
        "Book a table for 2 tomorrow at 7. My name is Ada Lovelace and my phone is 555-0101."
    )

    assert intent.intent == "reservation_create"
    assert intent.customer_name == "Ada Lovelace"
    assert intent.phone == "555-0101"
    assert intent.people == 2
    assert intent.time == "19:00"


def test_intent_parser_infers_hotel_reservation_details():
    intent = OllamaProvider._infer_intent(
        "Book a deluxe room for 2 guests tomorrow at 6 pm. My name is Ada Lovelace and phone is 555-0101."
    )

    assert intent.intent == "reservation_create"
    assert intent.reservation_type == "hotel"
    assert intent.room_type == "deluxe"
    assert intent.customer_name == "Ada Lovelace"
    assert intent.phone == "555-0101"
    assert intent.people == 2
    assert intent.time == "18:00"
