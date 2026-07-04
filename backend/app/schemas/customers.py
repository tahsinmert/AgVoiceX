from pydantic import BaseModel, EmailStr


class CustomerCreate(BaseModel):
    name: str
    phone: str | None = None
    email: EmailStr | None = None
    notes: str | None = None


class CustomerRead(CustomerCreate):
    id: int

    model_config = {"from_attributes": True}
