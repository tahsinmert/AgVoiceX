from typing import Any

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str
    slug: str = Field(min_length=1, max_length=128)


class OrganizationRead(OrganizationCreate):
    id: int

    model_config = {"from_attributes": True}


class BusinessCreate(BaseModel):
    organization_id: int
    name: str
    slug: str = Field(min_length=1, max_length=128)
    settings: dict[str, Any] = Field(default_factory=dict)


class BusinessRead(BusinessCreate):
    id: int

    model_config = {"from_attributes": True}
