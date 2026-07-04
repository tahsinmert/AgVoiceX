from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ai import ModelRead, ProviderRead
from app.services.ai_providers import PROVIDER_REGISTRY
from app.services.ai_settings import AISettingsService
from app.services.tenancy import TenantService

router = APIRouter(tags=["ai"])


@router.get("/providers", response_model=list[ProviderRead])
def list_providers(
    organization_id: int | None = None, db: Session = Depends(get_db)
) -> list[ProviderRead]:
    tenant = TenantService(db).resolve(organization_id)
    active_provider = AISettingsService(db, tenant).get_provider_name()
    return [
        ProviderRead(name=provider_name, active=provider_name == active_provider)
        for provider_name in PROVIDER_REGISTRY
    ]


@router.get("/models", response_model=list[ModelRead])
async def list_models(
    organization_id: int | None = None, db: Session = Depends(get_db)
) -> list[ModelRead]:
    tenant = TenantService(db).resolve(organization_id)
    ai_settings = AISettingsService(db, tenant)
    models = await ai_settings.get_provider().list_models()
    return [ModelRead(name=model["name"]) for model in models]
