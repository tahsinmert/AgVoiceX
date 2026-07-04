from pydantic import BaseModel, Field
from typing import Any


class ProviderRead(BaseModel):
    name: str
    active: bool = False


class ModelRead(BaseModel):
    name: str


class ProviderUpdate(BaseModel):
    provider: str = Field(min_length=1)
    organization_id: int | None = None


class ModelUpdate(BaseModel):
    model: str = Field(min_length=1)
    organization_id: int | None = None


class OllamaStatusRead(BaseModel):
    connected: bool
    version: str | None = None
    url: str | None = None


class OllamaModelRead(BaseModel):
    name: str
    size: int | None = None
    modified_at: str | None = None
    digest: str | None = None
    details: dict[str, Any] | None = None


class OllamaPullRequest(BaseModel):
    model: str = Field(min_length=1)
