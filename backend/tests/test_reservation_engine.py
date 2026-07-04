from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import *  # noqa: F403
from app.schemas.business_settings import BusinessSettingsPayload
from app.schemas.knowledge import KnowledgeCreate
from app.schemas.reservations import AvailabilityRequest, ReservationCreate
from app.services.business_settings import BusinessSettingsService
from app.services.knowledge import KnowledgeService
from app.services.reservations import ReservationService
from app.services.tenancy import TenantService


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def configure_business(db: Session, capacity: int = 6, closed_days: list[str] | None = None):
    context = TenantService(db).get_or_create_default_context()
    settings = BusinessSettingsPayload(
        timezone="UTC",
        working_hours={"monday": [{"open": "10:00", "close": "22:00"}]},
        closed_days=closed_days or [],
        slot_duration_minutes=30,
        max_capacity_per_slot=capacity,
        max_party_size=8,
        reservation_policy="Demo policy",
        cancellation_policy="Demo cancellation",
    )
    BusinessSettingsService(db, context).update_settings(settings, context.business_id)
    db.commit()
    return context


def test_availability_conflict_after_capacity_is_consumed():
    db = make_session()
    context = configure_business(db, capacity=4)
    service = ReservationService(db, context)
    target_date = date(2026, 7, 6)

    service.create(
        ReservationCreate(
            reservation_date=target_date,
            reservation_time=time(18, 0),
            people=4,
            customer_name="Ada",
            phone="1",
        )
    )

    availability = service.check_availability(
        AvailabilityRequest(
            reservation_date=target_date,
            reservation_time=time(18, 0),
            people=1,
        )
    )
    assert availability.available is False
    assert availability.reason == "Not enough capacity remains for that time slot."


def test_closed_day_is_unavailable():
    db = make_session()
    context = configure_business(db, closed_days=["monday"])

    availability = ReservationService(db, context).check_availability(
        AvailabilityRequest(
            reservation_date=date(2026, 7, 6),
            reservation_time=time(18, 0),
            people=2,
        )
    )
    assert availability.available is False
    assert availability.reason == "Business is closed on that day."


def test_capacity_limit_blocks_large_party():
    db = make_session()
    context = configure_business(db, capacity=4)

    availability = ReservationService(db, context).check_availability(
        AvailabilityRequest(
            reservation_date=date(2026, 7, 6),
            reservation_time=time(18, 0),
            people=5,
        )
    )
    assert availability.available is False


def test_create_reservation():
    db = make_session()
    context = configure_business(db, capacity=6)

    reservation = ReservationService(db, context).create(
        ReservationCreate(
            reservation_date=date(2026, 7, 6),
            reservation_time=time(18, 0),
            people=2,
            customer_name="Grace",
            phone="2",
        )
    )
    assert reservation.id is not None
    assert reservation.status == "confirmed"


def test_cancel_reservation():
    db = make_session()
    context = configure_business(db, capacity=6)
    service = ReservationService(db, context)
    reservation = service.create(
        ReservationCreate(
            reservation_date=date(2026, 7, 6),
            reservation_time=time(18, 0),
            people=2,
            customer_name="Linus",
            phone="3",
        )
    )

    cancelled = service.cancel(reservation.id)

    assert cancelled is not None
    assert cancelled.status == "cancelled"


def test_faq_fallback_search():
    db = make_session()
    context = configure_business(db)
    service = KnowledgeService(db, context)
    service.create(
        KnowledgeCreate(
            title="Terrace",
            body="Terrace seating is available when the weather is suitable.",
            source="test",
        )
    )

    results = service.search("Terrace", limit=5)

    assert len(results) == 1
    assert results[0].title == "Terrace"
