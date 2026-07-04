from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.businesses import Business
from app.models.organizations import Organization
from app.schemas.tenancy import BusinessCreate, BusinessRead, OrganizationCreate, OrganizationRead

router = APIRouter(tags=["tenancy"])


@router.get("/organizations", response_model=list[OrganizationRead])
def list_organizations(db: Session = Depends(get_db)) -> list[OrganizationRead]:
    return list(db.scalars(select(Organization).order_by(Organization.created_at.desc())))


@router.post("/organizations", response_model=OrganizationRead, status_code=201)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db)) -> OrganizationRead:
    organization = Organization(name=payload.name, slug=payload.slug)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


@router.get("/businesses", response_model=list[BusinessRead])
def list_businesses(
    organization_id: int | None = None, db: Session = Depends(get_db)
) -> list[BusinessRead]:
    statement = select(Business).order_by(Business.created_at.desc())
    if organization_id:
        statement = statement.where(Business.organization_id == organization_id)
    return list(db.scalars(statement))


@router.post("/businesses", response_model=BusinessRead, status_code=201)
def create_business(payload: BusinessCreate, db: Session = Depends(get_db)) -> BusinessRead:
    business = Business(
        organization_id=payload.organization_id,
        name=payload.name,
        slug=payload.slug,
        settings=payload.settings,
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business
