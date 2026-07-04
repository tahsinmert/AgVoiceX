from typing import Any

from pydantic import BaseModel, Field

from app.schemas.intents import IntentPayload


class ConversationRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    channel: str = "text"
    customer_id: int | None = None
    organization_id: int | None = None
    business_id: int | None = None
    agent_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    reply: str
    intent: IntentPayload
    conversation_id: int
    customer_id: int | None = None
