import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import *  # noqa: F403
from app.schemas.agents import AgentCreate, AgentUpdate
from app.schemas.prompts import PromptCreate, PromptUpdate
from app.schemas.reservations import ReservationCreate, ReservationUpdate
from app.services.agents import AgentService
from app.services.ai_providers import AIProvider
from app.services.knowledge import KnowledgeService
from app.services.prompts import PromptService
from app.services.reservations import ReservationService
from app.services.tenancy import TenantService


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_ingest_path_rejects_files_outside_allowed_roots():
    db = make_session()

    with pytest.raises(ValueError, match="Ingestion path must be under"):
        KnowledgeService(db).ingest_path("/etc/passwd")


@pytest.mark.asyncio
async def test_malformed_intent_json_returns_unknown_intent():
    class BrokenProvider(AIProvider):
        name = "broken"

        async def generate(self, model, messages):
            return "not-json"

        async def health(self):
            return {"ok": True}

        async def list_models(self):
            return [{"name": "broken"}]

    intent = await BrokenProvider().detect_intent("broken", "hello")

    assert intent.intent == "unknown"
    assert "reservations" in intent.reply


def test_agent_update_respects_optional_tenant_scope():
    db = make_session()
    agent = AgentService(db).create(AgentCreate(name="Scoped", model="local"))
    db.commit()

    blocked = AgentService(db).update(agent.id, AgentUpdate(organization_id=agent.organization_id + 1, name="Wrong"))
    allowed = AgentService(db).update(agent.id, AgentUpdate(organization_id=agent.organization_id, name="Right"))

    assert blocked is None
    assert allowed is not None
    assert allowed.name == "Right"


def test_prompt_update_respects_optional_tenant_scope():
    db = make_session()
    prompt = PromptService(db).create(PromptCreate(name="Scoped", content="hello"))
    db.commit()

    blocked = PromptService(db).update(prompt.id, PromptUpdate(organization_id=prompt.organization_id + 1, content="bad"))
    allowed = PromptService(db).update(prompt.id, PromptUpdate(organization_id=prompt.organization_id, content="good"))

    assert blocked is None
    assert allowed is not None
    assert allowed.content == "good"


def test_reservation_update_is_scoped_to_service_tenant():
    db = make_session()
    context = TenantService(db).get_or_create_default_context()
    reservation = ReservationService(db, context).create(
        ReservationCreate(
            customer_name="Ada",
            phone="555",
            reservation_date="2026-07-06",
            reservation_time="18:00",
            people=2,
        )
    )
    other_context = TenantService(db).resolve(context.organization_id + 1, context.business_id)

    blocked = ReservationService(db, other_context).update(reservation.id, ReservationUpdate(notes="bad"))

    assert blocked is None
