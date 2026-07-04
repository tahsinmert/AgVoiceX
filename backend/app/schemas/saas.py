from typing import Any

from pydantic import BaseModel, Field


class BusinessTemplateRead(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    category: str
    default_settings: dict[str, Any]
    default_prompts: list[dict[str, Any]]
    sample_knowledge: list[dict[str, Any]]

    model_config = {"from_attributes": True}


class TemplateApplyRequest(BaseModel):
    organization_id: int | None = None
    business_id: int | None = None
    agent_name: str | None = None


class TemplateApplyResponse(BaseModel):
    business_id: int
    agent_id: int
    prompts: int
    knowledge_items: int


class BrandProfilePayload(BaseModel):
    organization_id: int | None = None
    business_id: int | None = None
    name: str = "Default Brand"
    logo_url: str | None = None
    primary_color: str = Field(default="#0f766e", pattern=r"^#[0-9a-fA-F]{6}$")
    accent_color: str = Field(default="#f59e0b", pattern=r"^#[0-9a-fA-F]{6}$")
    support_email: str | None = None
    custom_domain: str | None = None


class BrandProfileRead(BrandProfilePayload):
    id: int

    model_config = {"from_attributes": True}


class RAGIngestionJobRead(BaseModel):
    id: int
    organization_id: int
    business_id: int | None
    source: str
    status: str
    documents: int
    chunks: int
    error: str | None = None

    model_config = {"from_attributes": True}


class WorkflowCreate(BaseModel):
    organization_id: int | None = None
    business_id: int | None = None
    slug: str = Field(min_length=1, max_length=128)
    name: str
    description: str = ""
    enabled: bool = True
    definition: dict[str, Any] = Field(default_factory=dict)


class WorkflowRead(WorkflowCreate):
    id: int
    organization_id: int

    model_config = {"from_attributes": True}
