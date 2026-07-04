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
