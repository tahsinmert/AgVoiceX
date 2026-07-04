from sqlalchemy.orm import Session

from app.schemas.conversations import ConversationRequest, ConversationResponse
from app.services.agent_runtime import AgentRuntime


class ConversationService:
    def __init__(self, db: Session):
        self.runtime = AgentRuntime(db)

    async def handle(self, request: ConversationRequest) -> ConversationResponse:
        return await self.runtime.run(request)
