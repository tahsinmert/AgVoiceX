import pytest

from app.services.ollama import OllamaConnectionError, OllamaManager


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

    async def request(self, method: str, url: str, json: dict):
        self.requests.append((method, url, json))
        return self.responses.pop(0)


@pytest.fixture(autouse=True)
def fake_httpx(monkeypatch):
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = []
    monkeypatch.setattr("app.services.ollama.httpx.AsyncClient", FakeAsyncClient)


@pytest.mark.asyncio
async def test_resolve_url_uses_first_available_candidate():
    FakeAsyncClient.responses = [FakeResponse({}, 503), FakeResponse({"models": []}, 200)]

    url = await OllamaManager(["http://host.docker.internal:11434", "http://docker-ollama:11434"]).resolve_url()

    assert url == "http://docker-ollama:11434"


@pytest.mark.asyncio
async def test_status_returns_version_and_url():
    FakeAsyncClient.responses = [FakeResponse({"models": []}), FakeResponse({"version": "0.3.12"})]

    status = await OllamaManager(["http://ollama:11434"]).status()

    assert status == {"connected": True, "version": "0.3.12", "url": "http://ollama:11434"}


@pytest.mark.asyncio
async def test_list_models_preserves_official_metadata():
    FakeAsyncClient.responses = [
        FakeResponse({"models": []}),
        FakeResponse(
            {
                "models": [
                    {
                        "name": "llama3.1:8b",
                        "size": 123,
                        "modified_at": "2026-01-01T00:00:00Z",
                        "digest": "abc",
                        "details": {"family": "llama"},
                    }
                ]
            }
        ),
    ]

    models = await OllamaManager(["http://ollama:11434"]).list_models()

    assert models[0]["name"] == "llama3.1:8b"
    assert models[0]["size"] == 123
    assert models[0]["details"] == {"family": "llama"}


@pytest.mark.asyncio
async def test_delete_model_calls_official_delete_api():
    FakeAsyncClient.responses = [FakeResponse({"models": []}), FakeResponse({}, 200)]

    result = await OllamaManager(["http://ollama:11434"]).delete("llama3.1:8b")

    assert result == {"deleted": True, "model": "llama3.1:8b"}
    assert FakeAsyncClient.requests[-1] == (
        "DELETE",
        "http://ollama:11434/api/delete",
        {"model": "llama3.1:8b"},
    )


@pytest.mark.asyncio
async def test_resolve_url_raises_when_no_candidates_work():
    FakeAsyncClient.responses = [FakeResponse({}, 503)]

    with pytest.raises(OllamaConnectionError):
        await OllamaManager(["http://missing:11434"]).resolve_url()
