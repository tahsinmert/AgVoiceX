from pydantic import BaseModel


class PromptCreate(BaseModel):
    organization_id: int | None = None
    agent_id: int | None = None
    name: str
    content: str
    version: int = 1
    is_active: bool = True


class PromptUpdate(BaseModel):
    organization_id: int | None = None
    name: str | None = None
    content: str | None = None
    version: int | None = None
    is_active: bool | None = None


class PromptRead(PromptCreate):
    id: int
    organization_id: int

    model_config = {"from_attributes": True}
