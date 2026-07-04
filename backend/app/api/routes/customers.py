from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.customers import CustomerCreate, CustomerRead
from app.services.customers import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerRead])
def list_customers(db: Session = Depends(get_db)) -> list[CustomerRead]:
    return CustomerService(db).list()


@router.post("", response_model=CustomerRead, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> CustomerRead:
    customer = CustomerService(db).get_or_create(payload.name, payload.phone, payload.email)
    customer.notes = payload.notes
    db.commit()
    db.refresh(customer)
    return customer
