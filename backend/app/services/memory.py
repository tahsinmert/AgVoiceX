from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_runtime import AgentMemory
from app.models.conversations import ConversationHistory
from app.services.tenancy import TenantContext


class MemoryManager:
    def __init__(self, db: Session, context: TenantContext):
        self.db = db
        self.context = context

    def load(self, customer_id: int | None = None, limit: int = 5) -> list[str]:
        statement = (
            select(AgentMemory)
            .where(AgentMemory.organization_id == self.context.organization_id)
            .order_by(AgentMemory.updated_at.desc(), AgentMemory.created_at.desc())
            .limit(limit)
        )
        if self.context.business_id is not None:
            statement = statement.where(AgentMemory.business_id == self.context.business_id)
        if self.context.agent_id is not None:
            statement = statement.where(AgentMemory.agent_id == self.context.agent_id)
        if customer_id is not None:
            statement = statement.where(AgentMemory.customer_id == customer_id)
        return [memory.content for memory in self.db.scalars(statement)]

    def remember_turn(self, record: ConversationHistory) -> AgentMemory:
        content = f"User: {record.user_message}\nAssistant: {record.assistant_reply}"
        memory = AgentMemory(
            organization_id=self.context.organization_id,
            business_id=self.context.business_id,
            agent_id=self.context.agent_id,
            customer_id=record.customer_id,
            memory_type="conversation_turn",
            content=content,
            memory_metadata={"conversation_id": record.id, "intent": record.intent},
        )
        self.db.add(memory)
        self.db.flush()
        return memory
