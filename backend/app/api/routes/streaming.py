from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conversations import ConversationRequest
from app.services.agents import AgentService
from app.services.ai_providers import create_provider
from app.services.ai_settings import AISettingsService
from app.services.tenancy import TenantService

router = APIRouter(tags=["streaming"])


@router.post("/chat/stream")
async def stream_chat(payload: ConversationRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    tenant = TenantService(db).resolve(payload.organization_id, payload.business_id, payload.agent_id)
    agent = AgentService(db).load(tenant)
    ai_settings = AISettingsService(db, tenant)
    provider = create_provider(agent.provider) if agent and agent.provider else ai_settings.get_provider()
    model = agent.model if agent and agent.model else await ai_settings.require_model_name()
    system_prompt = AgentService(db).active_prompt_for(agent, "You are a helpful local AI agent.")

    async def chunks():
        async for token in provider.stream(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload.message},
            ],
        ):
            yield token

    return StreamingResponse(chunks(), media_type="text/plain")
