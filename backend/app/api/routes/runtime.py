from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.agent_runtime import AgentMemory, RuntimeEvent
from app.services.tenancy import TenantService

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/events")
def list_runtime_events(
    organization_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> dict[str, list[dict]]:
    context = TenantService(db).resolve(organization_id)
    statement = (
        select(RuntimeEvent)
        .where(RuntimeEvent.organization_id == context.organization_id)
        .order_by(RuntimeEvent.created_at.desc())
        .limit(min(limit, 200))
    )
    return {
        "events": [
            {
                "id": event.id,
                "type": event.event_type,
                "conversation_id": event.conversation_id,
                "payload": event.payload,
                "created_at": event.created_at,
            }
            for event in db.scalars(statement)
        ]
    }


@router.get("/memories")
def list_memories(
    organization_id: int | None = None,
    customer_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> dict[str, list[dict]]:
    context = TenantService(db).resolve(organization_id)
    statement = (
        select(AgentMemory)
        .where(AgentMemory.organization_id == context.organization_id)
        .order_by(AgentMemory.updated_at.desc(), AgentMemory.created_at.desc())
        .limit(min(limit, 200))
    )
    if customer_id is not None:
        statement = statement.where(AgentMemory.customer_id == customer_id)
    return {
        "memories": [
            {
                "id": memory.id,
                "customer_id": memory.customer_id,
                "type": memory.memory_type,
                "content": memory.content,
                "metadata": memory.memory_metadata,
                "updated_at": memory.updated_at,
            }
            for memory in db.scalars(statement)
        ]
    }
