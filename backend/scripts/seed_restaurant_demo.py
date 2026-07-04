from datetime import date, timedelta, time

from app.db.session import SessionLocal
from app.models.agents import Agent
from app.models.businesses import Business
from app.models.customers import Customer
from app.models.knowledge import KnowledgeItem
from app.models.organizations import Organization
from app.models.prompts import Prompt
from app.models.reservations import Reservation
from app.schemas.business_settings import DEFAULT_RESTAURANT_SETTINGS


def get_or_create(db, model, defaults=None, **lookup):
    instance = db.query(model).filter_by(**lookup).one_or_none()
    if instance:
        return instance
    instance = model(**lookup, **(defaults or {}))
    db.add(instance)
    db.flush()
    return instance


def main() -> None:
    db = SessionLocal()
    try:
        organization = get_or_create(
            db,
            Organization,
            name="Istanbul Table Group",
            slug="istanbul-table-group",
        )
        business = get_or_create(
            db,
            Business,
            organization_id=organization.id,
            slug="bosphorus-bistro",
            defaults={
                "name": "Bosphorus Bistro",
                "settings": DEFAULT_RESTAURANT_SETTINGS.model_dump_for_storage(),
            },
        )
        business.settings = DEFAULT_RESTAURANT_SETTINGS.model_dump_for_storage()

        agent = get_or_create(
            db,
            Agent,
            organization_id=organization.id,
            business_id=business.id,
            name="Bosphorus Reservation Agent",
            defaults={
                "provider": "ollama",
                "model": "",
                "system_prompt": "You help guests with reservations and restaurant FAQs.",
                "is_active": True,
            },
        )
        get_or_create(
            db,
            Prompt,
            organization_id=organization.id,
            agent_id=agent.id,
            name="Reservation Concierge",
            defaults={
                "content": "You are a warm restaurant reservation concierge for Bosphorus Bistro.",
                "version": 1,
                "is_active": True,
            },
        )

        faqs = [
            ("Menu Highlights", "Signature dishes include lamb shank, sea bass, lentil soup, and pistachio baklava."),
            ("Dietary Options", "Vegetarian, vegan, halal, and gluten-aware options are available."),
            ("Parking", "Valet parking is available after 18:00. Street parking is limited."),
            ("Terrace Seating", "Terrace tables are weather dependent and cannot be guaranteed."),
            ("Cancellation Policy", DEFAULT_RESTAURANT_SETTINGS.cancellation_policy),
        ]
        for title, body in faqs:
            get_or_create(
                db,
                KnowledgeItem,
                organization_id=organization.id,
                title=title,
                defaults={"body": body, "source": "restaurant-demo", "item_metadata": {"demo": True}},
            )

        customers = []
        for index in range(10):
            customers.append(
                get_or_create(
                    db,
                    Customer,
                    organization_id=organization.id,
                    phone=f"+90-555-010{index}",
                    defaults={
                        "name": f"Demo Guest {index + 1}",
                        "email": f"guest{index + 1}@example.local",
                        "notes": "Seeded restaurant demo customer.",
                    },
                )
            )

        base_date = date.today() + timedelta(days=1)
        statuses = ["pending", "confirmed", "confirmed", "completed", "no_show"]
        for index in range(20):
            reservation_date = base_date + timedelta(days=index // 4)
            reservation_time = time(hour=18 + (index % 4), minute=0)
            existing = (
                db.query(Reservation)
                .filter_by(
                    organization_id=organization.id,
                    business_id=business.id,
                    customer_id=customers[index % len(customers)].id,
                    reservation_date=reservation_date,
                    reservation_time=reservation_time,
                )
                .one_or_none()
            )
            if existing:
                continue
            db.add(
                Reservation(
                    organization_id=organization.id,
                    business_id=business.id,
                    customer_id=customers[index % len(customers)].id,
                    reservation_date=reservation_date,
                    reservation_time=reservation_time,
                    people=2 + (index % 5),
                    status=statuses[index % len(statuses)],
                    notes="Seeded restaurant demo reservation.",
                )
            )

        db.commit()
        print("Seeded restaurant demo:")
        print(f"  organization_id={organization.id}")
        print(f"  business_id={business.id}")
        print(f"  agent_id={agent.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
