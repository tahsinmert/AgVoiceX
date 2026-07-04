from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.business_settings import BusinessSetting
from app.schemas.ai import ModelUpdate, ProviderUpdate
from app.schemas.settings import BusinessSettingRead, BusinessSettingUpsert, ModelTestRequest, ModelTestResponse
from app.services.ai_settings import AISettingsService
from app.services.tenancy import TenantService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=list[BusinessSettingRead])
def list_settings(db: Session = Depends(get_db)) -> list[BusinessSettingRead]:
    return list(db.scalars(select(BusinessSetting).order_by(BusinessSetting.key)))


@router.put("/model", response_model=BusinessSettingRead)
def update_model(payload: ModelUpdate, db: Session = Depends(get_db)) -> BusinessSettingRead:
    tenant = TenantService(db).resolve(payload.organization_id)
    setting = AISettingsService(db, tenant).set_model_name(payload.model)
    db.commit()
    db.refresh(setting)
    return setting


@router.put("/provider", response_model=BusinessSettingRead)
def update_provider(payload: ProviderUpdate, db: Session = Depends(get_db)) -> BusinessSettingRead:
    try:
        tenant = TenantService(db).resolve(payload.organization_id)
        setting = AISettingsService(db, tenant).set_provider_name(payload.provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(setting)
    return setting


@router.post("/model/test", response_model=ModelTestResponse)
async def test_model(payload: ModelTestRequest, db: Session = Depends(get_db)) -> ModelTestResponse:
    tenant = TenantService(db).resolve(payload.organization_id)
    ai_settings = AISettingsService(db, tenant)
    provider = ai_settings.get_provider()
    model = await ai_settings.require_model_name(provider)
    output = await provider.generate(
        model,
        [
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": payload.message},
        ],
    )
    return ModelTestResponse(provider=ai_settings.get_provider_name(), model=model, output=output)


@router.put("/{key}", response_model=BusinessSettingRead)
def upsert_setting(key: str, payload: BusinessSettingUpsert, db: Session = Depends(get_db)) -> BusinessSettingRead:
    setting = db.scalar(select(BusinessSetting).where(BusinessSetting.key == key))
    if setting is None:
        setting = BusinessSetting(key=key, value=payload.value)
        db.add(setting)
    else:
        setting.value = payload.value
    db.commit()
    db.refresh(setting)
    return setting
