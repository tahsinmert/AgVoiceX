from typing import Any

from pydantic import BaseModel, Field


class BusinessSettingsPayload(BaseModel):
    timezone: str = "UTC"
    working_hours: dict[str, list[dict[str, str]]] = Field(default_factory=dict)
    closed_days: list[str] = Field(default_factory=list)
    slot_duration_minutes: int = Field(default=30, ge=5, le=240)
    max_capacity_per_slot: int = Field(default=20, ge=1, le=500)
    max_party_size: int = Field(default=12, ge=1, le=500)
    reservation_policy: str = ""
    cancellation_policy: str = ""

    def model_dump_for_storage(self) -> dict[str, Any]:
        return self.model_dump()


DEFAULT_RESTAURANT_SETTINGS = BusinessSettingsPayload(
    timezone="Europe/Istanbul",
    working_hours={
        "monday": [{"open": "11:00", "close": "22:00"}],
        "tuesday": [{"open": "11:00", "close": "22:00"}],
        "wednesday": [{"open": "11:00", "close": "22:00"}],
        "thursday": [{"open": "11:00", "close": "22:00"}],
        "friday": [{"open": "11:00", "close": "23:00"}],
        "saturday": [{"open": "10:00", "close": "23:00"}],
        "sunday": [{"open": "10:00", "close": "21:00"}],
    },
    closed_days=[],
    slot_duration_minutes=30,
    max_capacity_per_slot=20,
    max_party_size=12,
    reservation_policy="Reservations are confirmed when capacity is available.",
    cancellation_policy="Guests can cancel up to two hours before the reservation.",
)
