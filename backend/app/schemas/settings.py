from typing import Any

from pydantic import BaseModel, Field


class BusinessSettingUpsert(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    value: dict[str, Any]


class BusinessSettingRead(BusinessSettingUpsert):
    id: int

    model_config = {"from_attributes": True}


class ModelTestRequest(BaseModel):
    organization_id: int | None = None
    message: str = "Return a short JSON health response."


class ModelTestResponse(BaseModel):
    provider: str
    model: str
    output: str
