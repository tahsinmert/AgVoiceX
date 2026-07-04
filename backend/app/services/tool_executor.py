from datetime import date, time
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.intents import IntentPayload
from app.schemas.reservations import ReservationCreate, ReservationUpdate
from app.services.customers import CustomerService
from app.services.reservations import ReservationService
from app.services.retrieval import HybridRetrievalService
from app.services.tenancy import TenantContext


class ToolExecutionResult(dict):
    @property
    def reply(self) -> str:
        return str(self.get("reply", ""))

    @property
    def customer_id(self) -> int | None:
        value = self.get("customer_id")
        return int(value) if value is not None else None


class ToolExecutor:
    def __init__(self, db: Session, context: TenantContext):
        self.db = db
        self.context = context

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> ToolExecutionResult:
        intent = IntentPayload.model_validate(arguments)
        if tool_name == "reservation.create":
            return self._create_reservation(intent)
        if tool_name == "reservation.update":
            return self._update_reservation(intent)
        if tool_name == "reservation.cancel":
            return self._cancel_reservation(intent)
        if tool_name == "reservation.lookup":
            return self._lookup_reservations()
        if tool_name == "knowledge.search":
            return self._answer_faq(intent)
        if tool_name == "customer.lookup":
            return self._lookup_customers()
        if tool_name == "admin.report":
            return self._admin_report()
        raise ValueError(f"Unknown runtime tool: {tool_name}")

    def _create_reservation(self, intent: IntentPayload) -> ToolExecutionResult:
        if not all([intent.customer_name, intent.date, intent.time, intent.people]):
            missing = []
            if not intent.customer_name:
                missing.append("name")
            if not intent.date:
                missing.append("date")
            if not intent.time:
                missing.append("time")
            if not intent.people:
                missing.append("guest count")
            return ToolExecutionResult(
                reply=intent.reply
                or f"To complete the {self._type_label(intent)} reservation, please provide: {', '.join(missing)}."
            )
        if intent.reservation_type == "hotel" and not intent.checkout_date and not intent.nights:
            return ToolExecutionResult(
                reply=intent.reply
                or "To complete the hotel reservation, please provide the check-out date or the number of nights."
            )
        parsed_date = self._parse_date(intent.date)
        parsed_time = self._parse_time(intent.time)
        if parsed_date is None or parsed_time is None:
            return ToolExecutionResult(reply="Please provide the reservation date as YYYY-MM-DD and the time as HH:MM.")
        reservation = ReservationService(self.db, self.context).create(
            ReservationCreate(
                customer_name=intent.customer_name,
                phone=intent.phone or None,
                email=intent.email or None,
                reservation_date=parsed_date,
                reservation_time=parsed_time,
                people=intent.people,
                notes=self._reservation_notes(intent),
            )
        )
        return ToolExecutionResult(
            reply=(
                f"{self._type_label(intent).title()} reservation confirmed for {intent.customer_name} on "
                f"{reservation.reservation_date} at {reservation.reservation_time.strftime('%H:%M')} "
                f"for {reservation.people} people. Confirmation number: {reservation.id}."
            ),
            customer_id=reservation.customer_id,
            reservation_id=reservation.id,
        )

    def _update_reservation(self, intent: IntentPayload) -> ToolExecutionResult:
        if not intent.reservation_id:
            return ToolExecutionResult(reply="Please provide the reservation confirmation number to update it.")
        parsed_date = self._parse_date(intent.date) if intent.date else None
        parsed_time = self._parse_time(intent.time) if intent.time else None
        if (intent.date and parsed_date is None) or (intent.time and parsed_time is None):
            return ToolExecutionResult(reply="Please provide the new date as YYYY-MM-DD and the new time as HH:MM.")
        reservation = ReservationService(self.db, self.context).update(
            intent.reservation_id,
            ReservationUpdate(
                reservation_date=parsed_date,
                reservation_time=parsed_time,
                people=intent.people,
                notes=intent.notes or None,
            ),
        )
        if reservation is None:
            return ToolExecutionResult(reply="I could not find that reservation.")
        return ToolExecutionResult(reply=f"Reservation {reservation.id} has been updated.", customer_id=reservation.customer_id)

    def _cancel_reservation(self, intent: IntentPayload) -> ToolExecutionResult:
        if not intent.reservation_id:
            return ToolExecutionResult(reply="Please provide the reservation confirmation number to cancel it.")
        reservation = ReservationService(self.db, self.context).cancel(intent.reservation_id)
        if reservation is None:
            return ToolExecutionResult(reply="I could not find that reservation.")
        return ToolExecutionResult(reply=f"Reservation {reservation.id} has been cancelled.", customer_id=reservation.customer_id)

    def _lookup_reservations(self) -> ToolExecutionResult:
        reservations = ReservationService(self.db, self.context).list_for_day()
        return ToolExecutionResult(reply=f"I found {len(reservations)} reservations for the selected business.")

    def _answer_faq(self, intent: IntentPayload) -> ToolExecutionResult:
        query = intent.question or intent.notes
        matches = HybridRetrievalService(self.db, self.context).search(query, limit=3) if query else []
        if not matches:
            return ToolExecutionResult(reply=intent.reply or "I do not have that answer in the local knowledge base yet.")
        first = matches[0]
        return ToolExecutionResult(reply=f"{first.title}: {first.body}", retrieval=[first.__dict__])

    def _lookup_customers(self) -> ToolExecutionResult:
        customers = CustomerService(self.db, self.context).list()
        return ToolExecutionResult(reply=f"I found {len(customers)} customers in the database.")

    def _admin_report(self) -> ToolExecutionResult:
        reservations = ReservationService(self.db, self.context).list_for_day()
        return ToolExecutionResult(reply=f"There are {len(reservations)} total reservations in the system.")

    @staticmethod
    def _type_label(intent: IntentPayload) -> str:
        labels = {
            "hotel": "hotel",
            "restaurant": "restaurant",
            "clinic": "clinic appointment",
            "beauty": "beauty appointment",
            "wellness": "wellness appointment",
            "automotive": "service appointment",
            "event": "event",
            "travel": "travel",
            "property": "property viewing",
            "meeting_room": "meeting room",
            "appointment": "appointment",
            "generic": "reservation",
        }
        return labels.get(intent.reservation_type or "generic", "reservation")

    @staticmethod
    def _reservation_notes(intent: IntentPayload) -> str | None:
        details = []
        if intent.reservation_type:
            details.append(f"type={intent.reservation_type}")
        if intent.service:
            details.append(f"service={intent.service}")
        if intent.room_type:
            details.append(f"room_type={intent.room_type}")
        if intent.checkout_date:
            details.append(f"checkout_date={intent.checkout_date}")
        if intent.nights:
            details.append(f"nights={intent.nights}")
        if intent.duration_minutes:
            details.append(f"duration_minutes={intent.duration_minutes}")
        if intent.location:
            details.append(f"location={intent.location}")
        if intent.notes:
            details.append(intent.notes)
        return " | ".join(details) or None

    @staticmethod
    def _parse_date(value: str) -> date | None:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_time(value: str) -> time | None:
        try:
            return time.fromisoformat(value)
        except ValueError:
            return None
