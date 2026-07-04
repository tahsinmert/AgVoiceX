from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import *  # noqa: F403
from app.models.saas import BrandProfile, RAGIngestionJob, WorkflowDefinition
from app.schemas.prompts import PromptCreate, PromptUpdate
from app.schemas.saas import BrandProfilePayload, TemplateApplyRequest, WorkflowCreate
from app.services.knowledge import KnowledgeService
from app.services.prompts import PromptService
from app.services.saas import SaaSService
from app.services.tenancy import TenantService


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_business_templates_are_seeded_and_can_be_applied():
    db = make_session()
    service = SaaSService(db)

    templates = service.list_templates()
    business, agent, prompts, knowledge = service.apply_template(
        "restaurant-reservations",
        TemplateApplyRequest(),
    )

    assert templates
    assert business.id is not None
    assert agent.business_id == business.id
    assert prompts >= 1
    assert knowledge >= 1


def test_brand_profile_can_be_updated():
    db = make_session()
    brand = SaaSService(db).update_brand(
        BrandProfilePayload(name="Acme AI", primary_color="#123456", accent_color="#abcdef")
    )
    db.commit()

    stored = db.scalar(select(BrandProfile))
    assert stored is not None
    assert brand.name == "Acme AI"
    assert stored.primary_color == "#123456"


def test_workflow_definition_can_be_created():
    db = make_session()
    workflow = SaaSService(db).create_workflow(
        WorkflowCreate(slug="handoff", name="Human Handoff", definition={"nodes": [{"type": "notify"}]})
    )
    db.commit()

    stored = db.scalar(select(WorkflowDefinition))
    assert stored is not None
    assert workflow.slug == "handoff"


def test_prompt_can_be_updated_for_prompt_studio():
    db = make_session()
    prompt = PromptService(db).create(PromptCreate(name="Base", content="Hello", version=1))
    updated = PromptService(db).update(prompt.id, PromptUpdate(content="Hello v2", version=2))
    db.commit()

    assert updated is not None
    assert updated.content == "Hello v2"
    assert updated.version == 2


def test_rag_job_records_upload_pipeline_result():
    db = make_session()
    context = TenantService(db).get_or_create_default_context()
    documents = KnowledgeService(db, context).parse_upload("faq.md", "Local FAQ")
    doc_count, chunk_count, source = KnowledgeService(db, context).ingest_documents(documents, "faq.md")
    db.add(
        RAGIngestionJob(
            organization_id=context.organization_id,
            business_id=context.business_id,
            source=source,
            documents=doc_count,
            chunks=chunk_count,
        )
    )
    db.commit()

    job = db.scalar(select(RAGIngestionJob))
    assert job is not None
    assert job.chunks == 1
