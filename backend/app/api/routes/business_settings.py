from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.business_settings import BusinessSettingsPayload
from app.services.business_settings import BusinessSettingsService
from app.services.tenancy import TenantService

router = APIRouter(prefix="/businesses", tags=["business-settings"])


@router.get("/{business_id}/settings", response_model=BusinessSettingsPayload)
def get_business_settings(
    business_id: int, organization_id: int | None = None, db: Session = Depends(get_db)
) -> BusinessSettingsPayload:
    try:
        context = TenantService(db).resolve(organization_id, business_id)
        return BusinessSettingsService(db, context).get_settings(business_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{business_id}/settings", response_model=BusinessSettingsPayload)
def update_business_settings(
    business_id: int,
    payload: BusinessSettingsPayload,
    organization_id: int | None = None,
    db: Session = Depends(get_db),
) -> BusinessSettingsPayload:
    try:
        context = TenantService(db).resolve(organization_id, business_id)
        BusinessSettingsService(db, context).update_settings(payload, business_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return payload
