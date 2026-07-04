import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import *  # noqa: F403
from app.models.agent_runtime import AgentMemory, RuntimeEvent
from app.schemas.conversations import ConversationRequest
from app.schemas.intents import IntentPayload
from app.schemas.knowledge import KnowledgeCreate
from app.services.agent_runtime import AgentRuntime
from app.services.ai_settings import AISettingsService
from app.services.event_bus import EventBus
from app.services.knowledge import KnowledgeService
from app.services.memory import MemoryManager
from app.services.planner import InternalPlanner
from app.services.plugins import create_plugin, plugin_registry
from app.services.retrieval import HybridRetrievalService
from app.services.tenancy import TenantService
from app.services.tools import tool_registry


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_planner_maps_faq_to_knowledge_tool():
    intent = IntentPayload(intent="faq", question="Do you have baklava?")

    plan = InternalPlanner().plan(intent)

    assert plan.steps[-1].tool_name == "knowledge.search"


def test_event_bus_persists_runtime_events():
    db = make_session()
    context = TenantService(db).get_or_create_default_context()

    EventBus(db, context).publish("runtime.started", {"channel": "text"})
    db.commit()

    event = db.scalar(select(RuntimeEvent))
    assert event is not None
    assert event.event_type == "runtime.started"
    assert event.payload["channel"] == "text"


def test_memory_manager_stores_conversation_turn():
    db = make_session()
    context = TenantService(db).get_or_create_default_context()
    record = ConversationHistory(  # noqa: F405
        organization_id=context.organization_id,
        channel="text",
        user_message="hello",
        intent="unknown",
        structured_output={},
        assistant_reply="hi",
    )
    db.add(record)
    db.flush()

    MemoryManager(db, context).remember_turn(record)
    db.commit()

    memory = db.scalar(select(AgentMemory))
    assert memory is not None
    assert "User: hello" in memory.content


def test_hybrid_retrieval_searches_items_and_chunks():
    db = make_session()
    context = TenantService(db).get_or_create_default_context()
    service = KnowledgeService(db, context)
    item = service.create(KnowledgeCreate(title="Menu", body="We serve pistachio baklava.", source="test"))
    db.flush()
    db.add(
        KnowledgeChunk(  # noqa: F405
            organization_id=context.organization_id,
            knowledge_id=item.id,
            chunk_index=0,
            body="Dessert detail: baklava has pistachio.",
            source="test",
            chunk_metadata={},
        )
    )
    db.commit()

    results = HybridRetrievalService(db, context).search("baklava", limit=2)

    assert results
    assert results[0].score > 0


def test_plugin_sdk_registers_tools():
    class EchoTool:
        name = "test.echo"

        async def call(self, arguments):
            return {"echo": arguments["value"]}

    sdk = create_plugin("test-plugin", capabilities=["tool:test.echo"])
    sdk.tool(EchoTool)

    plugin_registry.register_sdk(sdk)

    assert "test.echo" in tool_registry.list()


@pytest.mark.asyncio
async def test_agent_runtime_persists_events_memory_and_conversation(monkeypatch):
    db = make_session()
    context = TenantService(db).get_or_create_default_context()
    KnowledgeService(db, context).create(KnowledgeCreate(title="Dessert", body="Baklava is available.", source="test"))
    db.commit()

    class FakeProvider:
        async def detect_intent(self, model, message):
            return IntentPayload(intent="faq", question="baklava")

    async def fake_resolve_for_agent(self, agent):
        return FakeProvider(), "fake-local-model"

    monkeypatch.setattr(AISettingsService, "resolve_for_agent", fake_resolve_for_agent)

    response = await AgentRuntime(db).run(
        ConversationRequest(organization_id=context.organization_id, business_id=context.business_id, message="Do you have baklava?")
    )

    assert "Baklava is available" in response.reply
    assert db.scalar(select(RuntimeEvent).where(RuntimeEvent.event_type == "runtime.completed")) is not None
    assert db.scalar(select(AgentMemory)) is not None
