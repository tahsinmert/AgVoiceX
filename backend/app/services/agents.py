from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agents import Agent
from app.models.businesses import Business
from app.models.prompts import Prompt
from app.schemas.agents import AgentCreate, AgentUpdate
from app.services.ai_settings import AISettingsService
from app.services.tenancy import TenantContext, TenantService


class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: AgentCreate) -> Agent:
        context = TenantService(self.db).resolve(data.organization_id, data.business_id)
        if context.business_id is not None:
            business = self.db.get(Business, context.business_id)
            if business is None or business.organization_id != context.organization_id:
                raise ValueError("Business does not belong to the selected organization.")
        ai_settings = AISettingsService(self.db, context)
        provider = data.provider or ai_settings.get_provider_name()
        model = data.model or ai_settings.get_model_name() or ""
        system_prompt = data.system_prompt or "You are a local business AI agent."
        agent = Agent(
            organization_id=context.organization_id,
            business_id=context.business_id,
            name=data.name,
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            is_active=data.is_active,
        )
        self.db.add(agent)
        self.db.flush()
        return agent

    def list(self, organization_id: int | None = None) -> list[Agent]:
        context = TenantService(self.db).resolve(organization_id)
        return list(
            self.db.scalars(
                select(Agent)
                .where(Agent.organization_id == context.organization_id)
                .order_by(Agent.created_at.desc())
            )
        )

    def load(self, context: TenantContext) -> Agent | None:
        statement = select(Agent).where(
            Agent.organization_id == context.organization_id,
            Agent.is_active.is_(True),
        )
        if context.agent_id:
            statement = statement.where(Agent.id == context.agent_id)
        elif context.business_id:
            statement = statement.where(Agent.business_id == context.business_id)
        return self.db.scalar(statement.order_by(Agent.created_at.desc()))

    def update(self, agent_id: int, data: AgentUpdate) -> Agent | None:
        agent = self.db.get(Agent, agent_id)
        if agent is None:
            return None
        if data.organization_id is not None and agent.organization_id != data.organization_id:
            return None
        if data.business_id is not None and agent.business_id != data.business_id:
            return None
        updates = data.model_dump(exclude_unset=True, exclude={"organization_id", "business_id"})
        for field, value in updates.items():
            setattr(agent, field, value)
        self.db.flush()
        return agent

    def active_prompt_for(self, agent: Agent | None, fallback: str) -> str:
        if agent is None:
            return fallback
        prompt = self.db.scalar(
            select(Prompt)
            .where(
                Prompt.organization_id == agent.organization_id,
                Prompt.agent_id == agent.id,
                Prompt.is_active.is_(True),
            )
            .order_by(Prompt.version.desc(), Prompt.created_at.desc())
        )
        return prompt.content if prompt else agent.system_prompt
