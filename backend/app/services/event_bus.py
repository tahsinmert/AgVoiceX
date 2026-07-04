from typing import Any

from sqlalchemy.orm import Session

from app.models.agent_runtime import RuntimeEvent
from app.services.tenancy import TenantContext


class EventBus:
    def __init__(self, db: Session, context: TenantContext):
        self.db = db
        self.context = context

    def publish(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        conversation_id: int | None = None,
    ) -> RuntimeEvent:
        event = RuntimeEvent(
            organization_id=self.context.organization_id,
            business_id=self.context.business_id,
            agent_id=self.context.agent_id,
            conversation_id=conversation_id,
            event_type=event_type,
            payload=payload or {},
        )
        self.db.add(event)
        self.db.flush()
        return event
