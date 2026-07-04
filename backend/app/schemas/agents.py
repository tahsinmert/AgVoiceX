from pydantic import BaseModel


class AgentCreate(BaseModel):
    organization_id: int | None = None
    business_id: int | None = None
    name: str
    provider: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    is_active: bool = True


class AgentUpdate(BaseModel):
    organization_id: int | None = None
    business_id: int | None = None
    name: str | None = None
    provider: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    is_active: bool | None = None


class AgentRead(BaseModel):
    id: int
    organization_id: int | None
    business_id: int | None
    name: str
    provider: str | None
    model: str
    system_prompt: str
    is_active: bool

    model_config = {"from_attributes": True}
