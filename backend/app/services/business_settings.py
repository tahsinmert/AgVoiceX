from sqlalchemy.orm import Session

from app.models.businesses import Business
from app.schemas.business_settings import BusinessSettingsPayload, DEFAULT_RESTAURANT_SETTINGS
from app.services.tenancy import TenantContext, TenantService


class BusinessSettingsService:
    def __init__(self, db: Session, tenant_context: TenantContext | None = None):
        self.db = db
        self.tenant_context = tenant_context or TenantService(db).get_or_create_default_context()

    def get_business(self, business_id: int | None = None) -> Business:
        resolved_business_id = business_id or self.tenant_context.business_id
        if resolved_business_id is None:
            raise ValueError("Business is required.")
        business = self.db.get(Business, resolved_business_id)
        if business is None or business.organization_id != self.tenant_context.organization_id:
            raise ValueError("Business does not belong to the selected organization.")
        return business

    def get_settings(self, business_id: int | None = None) -> BusinessSettingsPayload:
        business = self.get_business(business_id)
        settings = {**DEFAULT_RESTAURANT_SETTINGS.model_dump(), **(business.settings or {})}
        return BusinessSettingsPayload.model_validate(settings)

    def update_settings(
        self, payload: BusinessSettingsPayload, business_id: int | None = None
    ) -> Business:
        business = self.get_business(business_id)
        business.settings = payload.model_dump_for_storage()
        self.db.flush()
        return business
