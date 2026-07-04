from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customers import Customer
from app.services.tenancy import TenantContext, TenantService


class CustomerService:
    def __init__(self, db: Session, tenant_context: TenantContext | None = None):
        self.db = db
        self.tenant_context = tenant_context or TenantService(db).get_or_create_default_context()

    def get_or_create(self, name: str, phone: str | None = None, email: str | None = None) -> Customer:
        customer = None
        if phone:
            customer = self.db.scalar(
                select(Customer).where(
                    Customer.phone == phone,
                    Customer.organization_id == self.tenant_context.organization_id,
                )
            )
        if customer is None:
            customer = Customer(
                organization_id=self.tenant_context.organization_id,
                name=name or "Unknown customer",
                phone=phone or None,
                email=email or None,
            )
            self.db.add(customer)
            self.db.flush()
        else:
            if name and customer.name == "Unknown customer":
                customer.name = name
            if email and not customer.email:
                customer.email = email
        return customer

    def list(self) -> list[Customer]:
        return list(
            self.db.scalars(
                select(Customer)
                .where(Customer.organization_id == self.tenant_context.organization_id)
                .order_by(Customer.created_at.desc())
            )
        )
