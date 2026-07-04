import json

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.ai import OllamaModelRead, OllamaPullRequest, OllamaStatusRead
from app.services.ollama import OllamaConnectionError, OllamaManager

router = APIRouter(prefix="/ollama", tags=["ollama"])


@router.get("/status", response_model=OllamaStatusRead)
async def ollama_status() -> OllamaStatusRead:
    return OllamaStatusRead(**await OllamaManager().status())


@router.get("/models", response_model=list[OllamaModelRead])
async def ollama_models() -> list[OllamaModelRead]:
    try:
        return [OllamaModelRead(**model) for model in await OllamaManager().list_models()]
    except OllamaConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Ollama model listing failed.") from exc


@router.post("/pull")
async def pull_model(payload: OllamaPullRequest) -> StreamingResponse:
    async def stream():
        try:
            async for line in OllamaManager().pull(payload.model):
                yield line
        except OllamaConnectionError as exc:
            yield f"{json.dumps({'error': str(exc)})}\n"
        except httpx.HTTPError:
            yield f"{json.dumps({'error': 'Ollama model pull failed.'})}\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@router.delete("/models/{name:path}")
async def delete_model(name: str, confirm: bool = False) -> dict[str, str | bool]:
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to delete an Ollama model.")
    try:
        return await OllamaManager().delete(name)
    except OllamaConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Ollama model delete failed.") from exc
