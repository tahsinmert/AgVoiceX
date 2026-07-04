from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import RequestIdMiddleware
from app.api.routes import (
    agents,
    admin,
    ai,
    business_settings,
    chat,
    conversations,
    customers,
    health,
    knowledge,
    ollama,
    prompts,
    reports,
    reservations,
    runtime,
    saas,
    settings,
    streaming,
    tenancy,
    tools,
    voice,
)
from app.core.logging import configure_logging
from app.core.config import settings as app_settings

configure_logging()

app = FastAPI(title="AgVoiceX API", version="0.1.0")

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ai.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(streaming.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(tenancy.router, prefix="/api/v1")
app.include_router(business_settings.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")
app.include_router(tools.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(reservations.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(ollama.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(runtime.router, prefix="/api/v1")
app.include_router(saas.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1/voice")
