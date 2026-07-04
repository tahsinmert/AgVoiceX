from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agents import Agent
from app.models.prompts import Prompt
from app.schemas.prompts import PromptCreate, PromptUpdate
from app.services.tenancy import TenantService


class PromptService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: PromptCreate) -> Prompt:
        context = TenantService(self.db).resolve(data.organization_id)
        if data.agent_id is not None:
            agent = self.db.get(Agent, data.agent_id)
            if agent is None or agent.organization_id != context.organization_id:
                raise ValueError("Agent does not belong to the selected organization.")
        prompt = Prompt(
            organization_id=context.organization_id,
            agent_id=data.agent_id,
            name=data.name,
            content=data.content,
            version=data.version,
            is_active=data.is_active,
        )
        self.db.add(prompt)
        self.db.flush()
        return prompt

    def list(self, organization_id: int | None = None) -> list[Prompt]:
        context = TenantService(self.db).resolve(organization_id)
        return list(
            self.db.scalars(
                select(Prompt)
                .where(Prompt.organization_id == context.organization_id)
                .order_by(Prompt.created_at.desc())
            )
        )

    def update(self, prompt_id: int, data: PromptUpdate) -> Prompt | None:
        prompt = self.db.get(Prompt, prompt_id)
        if prompt is None:
            return None
        if data.organization_id is not None and prompt.organization_id != data.organization_id:
            return None
        for field, value in data.model_dump(exclude_unset=True, exclude={"organization_id"}).items():
            setattr(prompt, field, value)
        self.db.flush()
        return prompt
