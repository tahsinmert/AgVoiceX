from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.conversations import ConversationHistory
from app.models.customers import Customer
from app.models.reservations import Reservation
from app.models.system_errors import SystemError
from app.services.tenancy import TenantService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/today")
def today(organization_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    context = TenantService(db).resolve(organization_id)
    reservations = list(
        db.scalars(
            select(Reservation)
            .where(
                Reservation.organization_id == context.organization_id,
                Reservation.reservation_date == date.today(),
            )
            .order_by(Reservation.reservation_time)
        )
    )
    return {
        "date": date.today().isoformat(),
        "reservations": len(reservations),
        "covers": sum(reservation.people for reservation in reservations if reservation.status != "cancelled"),
    }


@router.get("/reservations")
def reservations(organization_id: int | None = None, db: Session = Depends(get_db)) -> list[dict]:
    context = TenantService(db).resolve(organization_id)
    rows = db.scalars(
        select(Reservation)
        .where(Reservation.organization_id == context.organization_id)
        .order_by(Reservation.reservation_date.desc(), Reservation.reservation_time.desc())
    )
    return [
        {
            "id": row.id,
            "customer_id": row.customer_id,
            "date": row.reservation_date.isoformat(),
            "time": row.reservation_time.isoformat(),
            "people": row.people,
            "status": row.status,
        }
        for row in rows
    ]


@router.get("/analytics")
def analytics(organization_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    context = TenantService(db).resolve(organization_id)
    total_reservations = db.scalar(
        select(func.count()).select_from(Reservation).where(Reservation.organization_id == context.organization_id)
    )
    total_customers = db.scalar(
        select(func.count()).select_from(Customer).where(Customer.organization_id == context.organization_id)
    )
    covers = db.scalar(
        select(func.coalesce(func.sum(Reservation.people), 0)).where(
            Reservation.organization_id == context.organization_id,
            Reservation.status != "cancelled",
        )
    )
    return {
        "reservations": total_reservations or 0,
        "customers": total_customers or 0,
        "covers": int(covers or 0),
    }


@router.get("/conversations")
def conversations(organization_id: int | None = None, db: Session = Depends(get_db)) -> list[dict]:
    context = TenantService(db).resolve(organization_id)
    rows = db.scalars(
        select(ConversationHistory)
        .where(ConversationHistory.organization_id == context.organization_id)
        .order_by(ConversationHistory.created_at.desc())
        .limit(100)
    )
    return [
        {
            "id": row.id,
            "organization_id": row.organization_id,
            "customer_id": row.customer_id,
            "channel": row.channel,
            "user_message": row.user_message,
            "intent": row.intent,
            "structured_output": row.structured_output,
            "assistant_reply": row.assistant_reply,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.get("/errors")
def errors(organization_id: int | None = None, db: Session = Depends(get_db)) -> list[dict]:
    context = TenantService(db).resolve(organization_id)
    rows = db.scalars(
        select(SystemError)
        .where(
            (SystemError.organization_id == context.organization_id) | (SystemError.organization_id.is_(None))
        )
        .order_by(SystemError.created_at.desc())
        .limit(100)
    )
    return [
        {
            "id": row.id,
            "source": row.source,
            "message": row.message,
            "details": row.details,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
