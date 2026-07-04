from typing import Literal

from pydantic import BaseModel, Field


IntentName = Literal[
    "reservation_create",
    "reservation_update",
    "reservation_cancel",
    "reservation_lookup",
    "faq",
    "customer_lookup",
    "admin_report",
    "unknown",
]


class IntentPayload(BaseModel):
    intent: IntentName = "unknown"
    reservation_type: str = ""
    customer_name: str = ""
    phone: str = ""
    email: str = ""
    date: str = ""
    time: str = ""
    people: int | None = Field(default=None, ge=1, le=50)
    reservation_id: int | None = None
    service: str = ""
    room_type: str = ""
    checkout_date: str = ""
    nights: int | None = Field(default=None, ge=1, le=365)
    duration_minutes: int | None = Field(default=None, ge=15, le=10080)
    location: str = ""
    notes: str = ""
    question: str = ""
    reply: str = ""
