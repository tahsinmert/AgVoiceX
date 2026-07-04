from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.customers import Customer
from app.models.reservations import Reservation

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/admin")
def admin_report(db: Session = Depends(get_db)) -> dict[str, int | str]:
    reservation_count = db.scalar(select(func.count()).select_from(Reservation)) or 0
    customer_count = db.scalar(select(func.count()).select_from(Customer)) or 0
    today_count = (
        db.scalar(
            select(func.count()).select_from(Reservation).where(Reservation.reservation_date == date.today())
        )
        or 0
    )
    return {
        "date": date.today().isoformat(),
        "customers": customer_count,
        "reservations": reservation_count,
        "reservations_today": today_count,
    }
