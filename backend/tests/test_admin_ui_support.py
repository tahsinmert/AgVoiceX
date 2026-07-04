from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.routes.admin import conversations
from app.api.routes.knowledge import list_chunks
from app.api.routes.tools import list_plugin_manifests
from app.db.base import Base
from app.models import *  # noqa: F403
from app.models.agent_runtime import PluginManifest
from app.schemas.agents import AgentCreate, AgentUpdate
from app.schemas.knowledge import KnowledgeCreate
from app.services.agents import AgentService
from app.services.knowledge import KnowledgeService
from app.services.tenancy import TenantService


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_agent_can_be_updated_for_admin_ui():
    db = make_session()
    agent = AgentService(db).create(AgentCreate(name="Front Desk", model="local-model"))
    db.commit()

    updated = AgentService(db).update(agent.id, AgentUpdate(name="Reservation Desk", is_active=False))
    db.commit()

    assert updated is not None
    assert updated.name == "Reservation Desk"
    assert updated.is_active is False


def test_knowledge_chunks_can_be_listed_for_admin_ui():
    db = make_session()
    context = TenantService(db).get_or_create_default_context()
    item = KnowledgeService(db, context).create(KnowledgeCreate(title="FAQ", body="Local only.", source="test"))
    db.flush()
    db.add(
        KnowledgeChunk(  # noqa: F405
            organization_id=context.organization_id,
            knowledge_id=item.id,
            chunk_index=0,
            body="Local only.",
            source="test",
            chunk_metadata={},
        )
    )
    db.commit()

    chunks = list_chunks(context.organization_id, db=db)

    assert len(chunks) == 1
    assert chunks[0].body == "Local only."


def test_admin_conversations_returns_recent_history_rows():
    db = make_session()
    context = TenantService(db).get_or_create_default_context()
    db.add(
        ConversationHistory(  # noqa: F405
            organization_id=context.organization_id,
            channel="text",
            user_message="hello",
            intent="unknown",
            structured_output={},
            assistant_reply="hi",
        )
    )
    db.commit()

    rows = conversations(context.organization_id, db=db)

    assert rows[0]["user_message"] == "hello"


def test_plugin_manifests_can_be_listed_for_admin_ui():
    db = make_session()
    db.add(PluginManifest(name="demo", version="1.0.0", enabled=True, capabilities=["tool:demo"]))
    db.commit()

    payload = list_plugin_manifests(db=db)

    assert payload["plugins"][0]["name"] == "demo"


def test_upload_parser_accepts_json_lists():
    db = make_session()
    service = KnowledgeService(db)

    documents = service.parse_upload("faq.json", '[{"title":"Menu","body":"Baklava"}]')

    assert documents[0][0] == "Menu"
    assert "Baklava" in documents[0][1]
