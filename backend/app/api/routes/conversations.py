from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conversations import ConversationRequest, ConversationResponse
from app.schemas.intents import IntentPayload
from app.services.ai_settings import AISettingsService
from app.services.conversations import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/message", response_model=ConversationResponse)
async def create_message(payload: ConversationRequest, db: Session = Depends(get_db)) -> ConversationResponse:
    return await ConversationService(db).handle(payload)


@router.post("/intent", response_model=IntentPayload)
async def detect_intent(payload: ConversationRequest, db: Session = Depends(get_db)) -> IntentPayload:
    ai_settings = AISettingsService(db)
    provider = ai_settings.get_provider()
    model = await ai_settings.require_model_name()
    return await provider.detect_intent(model, payload.message)
