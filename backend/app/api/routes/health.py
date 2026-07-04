from typing import Any

import httpx
import redis
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.ai_settings import AISettingsService

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> JSONResponse:
    checks: dict[str, dict[str, Any]] = {
        "api": {"ok": True},
        "postgres": {"ok": False},
        "redis": {"ok": False},
        "qdrant": {"ok": False},
        "ai_provider": {"ok": False},
    }

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        checks["postgres"] = {"ok": True}
    except Exception as exc:
        checks["postgres"] = {"ok": False, "error": str(exc)}

    try:
        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
        checks["redis"] = {"ok": bool(client.ping())}
    except Exception as exc:
        checks["redis"] = {"ok": False, "error": str(exc)}

    async with httpx.AsyncClient(timeout=3) as client:
        try:
            response = await client.get(f"{settings.qdrant_url.rstrip('/')}/")
            checks["qdrant"] = {"ok": response.status_code < 500, "status_code": response.status_code}
        except Exception as exc:
            checks["qdrant"] = {"ok": False, "error": str(exc)}

    try:
        with SessionLocal() as db:
            provider_name = AISettingsService(db).get_provider_name()
            provider = AISettingsService(db).get_provider()
        provider_health = await provider.health()
        checks["ai_provider"] = {"provider": provider_name, **provider_health}
    except Exception as exc:
        checks["ai_provider"] = {"ok": False, "error": str(exc)}

    is_healthy = all(check["ok"] for check in checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ok" if is_healthy else "degraded", "checks": checks},
    )
