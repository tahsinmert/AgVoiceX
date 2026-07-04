from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.saas import RAGIngestionJob
from app.schemas.saas import (
    BrandProfilePayload,
    BrandProfileRead,
    BusinessTemplateRead,
    RAGIngestionJobRead,
    TemplateApplyRequest,
    TemplateApplyResponse,
    WorkflowCreate,
    WorkflowRead,
)
from app.services.saas import SaaSService
from app.services.tenancy import TenantService

router = APIRouter(tags=["white-label-saas"])


@router.get("/business-templates", response_model=list[BusinessTemplateRead])
def list_business_templates(db: Session = Depends(get_db)) -> list[BusinessTemplateRead]:
    service = SaaSService(db)
    templates = service.list_templates()
    db.commit()
    return templates


@router.post("/business-templates/{slug}/apply", response_model=TemplateApplyResponse)
def apply_business_template(
    slug: str,
    payload: TemplateApplyRequest,
    db: Session = Depends(get_db),
) -> TemplateApplyResponse:
    try:
        business, agent, prompts, knowledge_items = SaaSService(db).apply_template(slug, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return TemplateApplyResponse(
        business_id=business.id,
        agent_id=agent.id,
        prompts=prompts,
        knowledge_items=knowledge_items,
    )


@router.get("/branding", response_model=BrandProfileRead)
def get_branding(
    organization_id: int | None = None,
    business_id: int | None = None,
    db: Session = Depends(get_db),
) -> BrandProfileRead:
    brand = SaaSService(db).get_brand(organization_id, business_id)
    db.commit()
    return brand


@router.put("/branding", response_model=BrandProfileRead)
def update_branding(payload: BrandProfilePayload, db: Session = Depends(get_db)) -> BrandProfileRead:
    brand = SaaSService(db).update_brand(payload)
    db.commit()
    db.refresh(brand)
    return brand


@router.get("/rag/jobs", response_model=list[RAGIngestionJobRead])
def list_rag_jobs(
    organization_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[RAGIngestionJobRead]:
    context = TenantService(db).resolve(organization_id)
    return list(
        db.scalars(
            select(RAGIngestionJob)
            .where(RAGIngestionJob.organization_id == context.organization_id)
            .order_by(RAGIngestionJob.created_at.desc())
            .limit(100)
        )
    )


@router.get("/workflows", response_model=list[WorkflowRead])
def list_workflows(organization_id: int | None = None, db: Session = Depends(get_db)) -> list[WorkflowRead]:
    return SaaSService(db).list_workflows(organization_id)


@router.post("/workflows", response_model=WorkflowRead, status_code=201)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)) -> WorkflowRead:
    workflow = SaaSService(db).create_workflow(payload)
    db.commit()
    db.refresh(workflow)
    return workflow
