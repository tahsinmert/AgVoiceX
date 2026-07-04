from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import *  # noqa: F403
from app.schemas.agents import AgentCreate
from app.services.agents import AgentService
from app.services.ai_settings import AISettingsService
from app.services.tenancy import TenantService


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_default_tenant_is_created_for_backward_compatibility():
    db = make_session()

    context = TenantService(db).get_or_create_default_context()
    db.commit()

    assert context.organization_id is not None
    assert context.business_id is not None


def test_ai_settings_are_scoped_by_organization():
    db = make_session()
    tenant_service = TenantService(db)
    default_context = tenant_service.get_or_create_default_context()
    other_context = tenant_service.resolve()
    other_context.organization_id = default_context.organization_id + 1

    default_settings = AISettingsService(db, default_context)
    default_settings.set_provider_name("ollama")
    default_settings.set_model_name("model-a")
    db.commit()

    assert AISettingsService(db, default_context).get_model_name() == "model-a"


def test_agent_creation_uses_default_tenant_and_can_be_loaded():
    db = make_session()
    service = AgentService(db)

    agent = service.create(AgentCreate(name="Support Agent", model="local-model"))
    db.commit()

    context = TenantService(db).resolve(agent.organization_id, agent.business_id, agent.id)
    loaded = service.load(context)
    assert loaded is not None
    assert loaded.name == "Support Agent"
