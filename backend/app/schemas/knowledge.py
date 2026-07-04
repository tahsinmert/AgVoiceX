from typing import Any

from pydantic import AliasChoices, BaseModel, Field


class KnowledgeCreate(BaseModel):
    title: str
    body: str
    source: str | None = None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("metadata", "item_metadata"),
        serialization_alias="metadata",
    )


class KnowledgeRead(KnowledgeCreate):
    id: int

    model_config = {"from_attributes": True}


class KnowledgeSearchRequest(BaseModel):
    organization_id: int | None = None
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=25)


class KnowledgeIngestRequest(BaseModel):
    organization_id: int | None = None
    path: str
    source: str | None = None


class KnowledgeIngestResponse(BaseModel):
    source: str
    documents: int
    chunks: int


class KnowledgeChunkRead(BaseModel):
    id: int
    organization_id: int
    knowledge_id: int | None
    chunk_index: int
    body: str
    source: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}
