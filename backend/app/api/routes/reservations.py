from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reservations import (
    AvailabilityRequest,
    AvailabilityResponse,
    ReservationCreate,
    ReservationRead,
    ReservationUpdate,
)
from app.services.reservations import ReservationService

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("", response_model=list[ReservationRead])
def list_reservations(db: Session = Depends(get_db)) -> list[ReservationRead]:
    return ReservationService(db).list_for_day()


@router.post("/availability", response_model=AvailabilityResponse)
def check_availability(payload: AvailabilityRequest, db: Session = Depends(get_db)) -> AvailabilityResponse:
    return ReservationService(db).check_availability(payload)


@router.post("", response_model=ReservationRead, status_code=201)
def create_reservation(payload: ReservationCreate, db: Session = Depends(get_db)) -> ReservationRead:
    try:
        reservation = ReservationService(db).create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(reservation)
    return reservation


@router.patch("/{reservation_id}", response_model=ReservationRead)
def update_reservation(
    reservation_id: int, payload: ReservationUpdate, db: Session = Depends(get_db)
) -> ReservationRead:
    try:
        reservation = ReservationService(db).update(reservation_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    db.commit()
    db.refresh(reservation)
    return reservation


@router.delete("/{reservation_id}", response_model=ReservationRead)
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db)) -> ReservationRead:
    reservation = ReservationService(db).cancel(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    db.commit()
    db.refresh(reservation)
    return reservation
