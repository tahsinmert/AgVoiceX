from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.reservations import Reservation
from app.schemas.reservations import AvailabilityRequest, AvailabilityResponse, ReservationCreate, ReservationUpdate
from app.services.business_settings import BusinessSettingsService
from app.services.customers import CustomerService
from app.services.tenancy import TenantContext, TenantService


class ReservationService:
    def __init__(self, db: Session, tenant_context: TenantContext | None = None):
        self.db = db
        self.tenant_context = tenant_context or TenantService(db).get_or_create_default_context()

    def create(self, data: ReservationCreate) -> Reservation:
        if data.organization_id or data.business_id:
            self.tenant_context = TenantService(self.db).resolve(data.organization_id, data.business_id)
        availability = self.check_availability(
            AvailabilityRequest(
                organization_id=self.tenant_context.organization_id,
                business_id=data.business_id or self.tenant_context.business_id,
                reservation_date=data.reservation_date,
                reservation_time=data.reservation_time,
                people=data.people,
            )
        )
        if not availability.available:
            raise ValueError(availability.reason or "Reservation is not available.")
        customer = CustomerService(self.db, self.tenant_context).get_or_create(
            data.customer_name, data.phone, data.email
        )
        reservation = Reservation(
            organization_id=self.tenant_context.organization_id,
            business_id=data.business_id or self.tenant_context.business_id,
            customer_id=customer.id,
            reservation_date=data.reservation_date,
            reservation_time=data.reservation_time,
            people=data.people,
            status=data.status,
            notes=data.notes,
        )
        self.db.add(reservation)
        self.db.flush()
        return reservation

    def update(self, reservation_id: int, data: ReservationUpdate) -> Reservation | None:
        reservation = self.db.get(Reservation, reservation_id)
        if reservation is None:
            return None
        if reservation.organization_id != self.tenant_context.organization_id:
            return None
        if self.tenant_context.business_id is not None and reservation.business_id != self.tenant_context.business_id:
            return None
        if data.business_id:
            self.tenant_context.business_id = data.business_id
            if reservation.business_id != data.business_id:
                return None
        target_date = data.reservation_date or reservation.reservation_date
        target_time = data.reservation_time or reservation.reservation_time
        target_people = data.people or reservation.people
        if any([data.reservation_date, data.reservation_time, data.people]):
            availability = self.check_availability(
                AvailabilityRequest(
                    organization_id=self.tenant_context.organization_id,
                    business_id=self.tenant_context.business_id,
                    reservation_date=target_date,
                    reservation_time=target_time,
                    people=target_people,
                ),
                exclude_reservation_id=reservation_id,
            )
            if not availability.available:
                raise ValueError(availability.reason or "Reservation is not available.")
        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "business_id":
                continue
            setattr(reservation, field, value)
        self.db.flush()
        return reservation

    def cancel(self, reservation_id: int) -> Reservation | None:
        return self.update(reservation_id, ReservationUpdate(status="cancelled"))

    def list_for_day(self, target_date: date | None = None) -> list[Reservation]:
        statement = select(Reservation).order_by(Reservation.reservation_date, Reservation.reservation_time)
        statement = statement.where(Reservation.organization_id == self.tenant_context.organization_id)
        statement = statement.where(Reservation.business_id == self.tenant_context.business_id)
        if target_date:
            statement = statement.where(Reservation.reservation_date == target_date)
        return list(self.db.scalars(statement))

    def find_slot(self, reservation_date: date, reservation_time: time) -> list[Reservation]:
        return list(
            self.db.scalars(
                select(Reservation).where(
                    Reservation.organization_id == self.tenant_context.organization_id,
                    Reservation.business_id == self.tenant_context.business_id,
                    Reservation.reservation_date == reservation_date,
                    Reservation.reservation_time == reservation_time,
                    Reservation.status != "cancelled",
                )
            )
        )

    def check_availability(
        self, request: AvailabilityRequest, exclude_reservation_id: int | None = None
    ) -> AvailabilityResponse:
        context = TenantService(self.db).resolve(request.organization_id, request.business_id)
        business_settings = BusinessSettingsService(self.db, context).get_settings(request.business_id)
        capacity = business_settings.max_capacity_per_slot

        if request.people > business_settings.max_party_size:
            return AvailabilityResponse(
                available=False,
                reason="Party size exceeds the reservation policy.",
                capacity=capacity,
                booked=0,
                remaining=capacity,
            )

        day_key = request.reservation_date.strftime("%A").lower()
        if request.reservation_date.isoformat() in business_settings.closed_days or day_key in business_settings.closed_days:
            return AvailabilityResponse(
                available=False,
                reason="Business is closed on that day.",
                capacity=capacity,
                booked=0,
                remaining=capacity,
            )

        if not self._within_working_hours(
            request.reservation_time,
            business_settings.working_hours.get(day_key, []),
            business_settings.slot_duration_minutes,
        ):
            return AvailabilityResponse(
                available=False,
                reason="Requested time is outside working hours.",
                capacity=capacity,
                booked=0,
                remaining=capacity,
            )

        statement = select(func.coalesce(func.sum(Reservation.people), 0)).where(
            Reservation.organization_id == context.organization_id,
            Reservation.business_id == context.business_id,
            Reservation.reservation_date == request.reservation_date,
            Reservation.reservation_time == request.reservation_time,
            Reservation.status.in_(["pending", "confirmed"]),
        )
        if exclude_reservation_id:
            statement = statement.where(Reservation.id != exclude_reservation_id)
        booked = int(self.db.scalar(statement) or 0)
        remaining = max(capacity - booked, 0)
        if request.people > remaining:
            return AvailabilityResponse(
                available=False,
                reason="Not enough capacity remains for that time slot.",
                capacity=capacity,
                booked=booked,
                remaining=remaining,
            )
        return AvailabilityResponse(
            available=True,
            capacity=capacity,
            booked=booked,
            remaining=remaining - request.people,
        )

    @staticmethod
    def _within_working_hours(
        reservation_time: time, windows: list[dict[str, str]], slot_duration_minutes: int
    ) -> bool:
        requested = datetime.combine(date.today(), reservation_time)
        for window in windows:
            opens = datetime.combine(date.today(), time.fromisoformat(window["open"]))
            closes = datetime.combine(date.today(), time.fromisoformat(window["close"]))
            latest_start = closes - timedelta(minutes=slot_duration_minutes)
            if opens <= requested <= latest_start:
                return True
        return False
