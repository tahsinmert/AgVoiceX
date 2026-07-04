from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field

ReservationStatus = Literal["pending", "confirmed", "cancelled", "completed", "no_show"]


class ReservationCreate(BaseModel):
    organization_id: int | None = None
    business_id: int | None = None
    customer_name: str
    phone: str | None = None
    email: str | None = None
    reservation_date: date
    reservation_time: time
    people: int = Field(ge=1, le=50)
    status: ReservationStatus = "confirmed"
    notes: str | None = None


class ReservationUpdate(BaseModel):
    business_id: int | None = None
    reservation_date: date | None = None
    reservation_time: time | None = None
    people: int | None = Field(default=None, ge=1, le=50)
    status: ReservationStatus | None = None
    notes: str | None = None


class AvailabilityRequest(BaseModel):
    organization_id: int | None = None
    business_id: int | None = None
    reservation_date: date
    reservation_time: time
    people: int = Field(ge=1, le=50)


class AvailabilityResponse(BaseModel):
    available: bool
    reason: str | None = None
    capacity: int
    booked: int
    remaining: int


class ReservationRead(BaseModel):
    id: int
    organization_id: int | None = None
    business_id: int | None = None
    customer_id: int
    reservation_date: date
    reservation_time: time
    people: int
    status: str
    notes: str | None = None

    model_config = {"from_attributes": True}
