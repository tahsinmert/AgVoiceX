from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conversations import ConversationRequest, ConversationResponse
from app.services.conversations import ConversationService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ConversationResponse)
async def chat(payload: ConversationRequest, db: Session = Depends(get_db)) -> ConversationResponse:
    return await ConversationService(db).handle(payload)
