from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.businesses import Business
from app.models.organizations import Organization

DEFAULT_ORGANIZATION_SLUG = "default"
DEFAULT_BUSINESS_SLUG = "default"


class TenantContext:
    def __init__(
        self,
        organization_id: int,
        business_id: int | None = None,
        agent_id: int | None = None,
    ):
        self.organization_id = organization_id
        self.business_id = business_id
        self.agent_id = agent_id


class TenantService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_default_context(self) -> TenantContext:
        organization = self.db.scalar(
            select(Organization).where(Organization.slug == DEFAULT_ORGANIZATION_SLUG)
        )
        if organization is None:
            organization = Organization(name="Default Organization", slug=DEFAULT_ORGANIZATION_SLUG)
            self.db.add(organization)
            self.db.flush()

        business = self.db.scalar(
            select(Business).where(
                Business.organization_id == organization.id,
                Business.slug == DEFAULT_BUSINESS_SLUG,
            )
        )
        if business is None:
            business = Business(
                organization_id=organization.id,
                name="Default Business",
                slug=DEFAULT_BUSINESS_SLUG,
            )
            self.db.add(business)
            self.db.flush()
        return TenantContext(organization_id=organization.id, business_id=business.id)

    def resolve(
        self,
        organization_id: int | None = None,
        business_id: int | None = None,
        agent_id: int | None = None,
    ) -> TenantContext:
        if organization_id is None:
            context = self.get_or_create_default_context()
            context.business_id = business_id or context.business_id
            context.agent_id = agent_id
            return context
        return TenantContext(organization_id=organization_id, business_id=business_id, agent_id=agent_id)
