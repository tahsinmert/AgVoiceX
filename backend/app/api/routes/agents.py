from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.agents import AgentCreate, AgentRead, AgentUpdate
from app.services.agents import AgentService

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentRead])
def list_agents(organization_id: int | None = None, db: Session = Depends(get_db)) -> list[AgentRead]:
    return AgentService(db).list(organization_id)


@router.post("", response_model=AgentRead, status_code=201)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)) -> AgentRead:
    try:
        agent = AgentService(db).create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(agent)
    return agent


@router.patch("/{agent_id}", response_model=AgentRead)
def update_agent(agent_id: int, payload: AgentUpdate, db: Session = Depends(get_db)) -> AgentRead:
    agent = AgentService(db).update(agent_id, payload)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.commit()
    db.refresh(agent)
    return agent
