from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agents import Agent
from app.models.businesses import Business
from app.models.knowledge import KnowledgeItem
from app.models.prompts import Prompt
from app.models.saas import BrandProfile, BusinessTemplate, WorkflowDefinition
from app.schemas.business_settings import DEFAULT_RESTAURANT_SETTINGS
from app.schemas.saas import BrandProfilePayload, TemplateApplyRequest, WorkflowCreate
from app.services.tenancy import TenantService


DEFAULT_TEMPLATES = [
    {
        "slug": "restaurant-reservations",
        "name": "Restaurant Reservations",
        "category": "hospitality",
        "description": "Reservations, policies, menu FAQ and guest support for restaurants.",
        "default_settings": DEFAULT_RESTAURANT_SETTINGS.model_dump_for_storage(),
        "default_prompts": [
            {
                "name": "Reservation Concierge",
                "content": "You are a concise restaurant reservation concierge. Use local policies and confirm details before booking.",
            }
        ],
        "sample_knowledge": [
            {"title": "Menu FAQ", "body": "Answer menu, allergy, parking and seating questions from local knowledge only."},
            {"title": "Reservation Policy", "body": DEFAULT_RESTAURANT_SETTINGS.reservation_policy},
        ],
    },
    {
        "slug": "salon-appointments",
        "name": "Salon Appointments",
        "category": "services",
        "description": "Appointment intake, service FAQ and cancellation policy for salons and clinics.",
        "default_settings": {"slot_duration_minutes": 30, "max_capacity_per_slot": 2},
        "default_prompts": [
            {
                "name": "Appointment Assistant",
                "content": "You help clients pick services, check availability and explain appointment policies.",
            }
        ],
        "sample_knowledge": [
            {"title": "Services", "body": "Haircuts, color consultation, styling and treatment appointments are available."}
        ],
    },
    {
        "slug": "local-support-desk",
        "name": "Local Support Desk",
        "category": "support",
        "description": "FAQ, triage and escalation workflows for local customer support teams.",
        "default_settings": {"slot_duration_minutes": 15},
        "default_prompts": [
            {
                "name": "Support Agent",
                "content": "You answer from the local knowledge base and ask clarifying questions before escalating.",
            }
        ],
        "sample_knowledge": [
            {"title": "Support Policy", "body": "Use local documentation first. Escalate when confidence is low."}
        ],
    },
]


class SaaSService:
    def __init__(self, db: Session):
        self.db = db

    def ensure_templates(self) -> None:
        for template in DEFAULT_TEMPLATES:
            existing = self.db.scalar(select(BusinessTemplate).where(BusinessTemplate.slug == template["slug"]))
            if existing is None:
                self.db.add(BusinessTemplate(**template))
        self.db.flush()

    def list_templates(self) -> list[BusinessTemplate]:
        self.ensure_templates()
        return list(self.db.scalars(select(BusinessTemplate).order_by(BusinessTemplate.category, BusinessTemplate.name)))

    def apply_template(self, slug: str, payload: TemplateApplyRequest):
        template = self.db.scalar(select(BusinessTemplate).where(BusinessTemplate.slug == slug))
        if template is None:
            raise ValueError("Business template not found")
        context = TenantService(self.db).resolve(payload.organization_id, payload.business_id)
        business = self.db.get(Business, context.business_id) if context.business_id else None
        if business is None:
            business = Business(
                organization_id=context.organization_id,
                name=template.name,
                slug=template.slug,
                settings=template.default_settings,
            )
            self.db.add(business)
            self.db.flush()
            context.business_id = business.id
        else:
            business.settings = {**(business.settings or {}), **template.default_settings}

        agent = Agent(
            organization_id=context.organization_id,
            business_id=business.id,
            name=payload.agent_name or f"{template.name} Agent",
            provider=None,
            model="",
            system_prompt=template.default_prompts[0]["content"] if template.default_prompts else "You are a local business AI agent.",
            is_active=True,
        )
        self.db.add(agent)
        self.db.flush()
        for index, prompt in enumerate(template.default_prompts, start=1):
            self.db.add(
                Prompt(
                    organization_id=context.organization_id,
                    agent_id=agent.id,
                    name=prompt["name"],
                    content=prompt["content"],
                    version=index,
                    is_active=index == len(template.default_prompts),
                )
            )
        for item in template.sample_knowledge:
            self.db.add(
                KnowledgeItem(
                    organization_id=context.organization_id,
                    title=item["title"],
                    body=item["body"],
                    source=f"template:{template.slug}",
                    item_metadata={"template": template.slug},
                )
            )
        self.db.flush()
        return business, agent, len(template.default_prompts), len(template.sample_knowledge)

    def get_brand(self, organization_id: int | None = None, business_id: int | None = None) -> BrandProfile:
        context = TenantService(self.db).resolve(organization_id, business_id)
        brand = self.db.scalar(
            select(BrandProfile).where(
                BrandProfile.organization_id == context.organization_id,
                BrandProfile.business_id == context.business_id,
            )
        )
        if brand is None:
            brand = BrandProfile(organization_id=context.organization_id, business_id=context.business_id)
            self.db.add(brand)
            self.db.flush()
        return brand

    def update_brand(self, payload: BrandProfilePayload) -> BrandProfile:
        brand = self.get_brand(payload.organization_id, payload.business_id)
        for key, value in payload.model_dump(exclude={"organization_id", "business_id"}).items():
            setattr(brand, key, value)
        self.db.flush()
        return brand

    def list_workflows(self, organization_id: int | None = None) -> list[WorkflowDefinition]:
        context = TenantService(self.db).resolve(organization_id)
        return list(
            self.db.scalars(
                select(WorkflowDefinition)
                .where(WorkflowDefinition.organization_id == context.organization_id)
                .order_by(WorkflowDefinition.created_at.desc())
            )
        )

    def create_workflow(self, payload: WorkflowCreate) -> WorkflowDefinition:
        context = TenantService(self.db).resolve(payload.organization_id, payload.business_id)
        workflow = WorkflowDefinition(
            organization_id=context.organization_id,
            business_id=context.business_id,
            slug=payload.slug,
            name=payload.name,
            description=payload.description,
            enabled=payload.enabled,
            definition=payload.definition,
        )
        self.db.add(workflow)
        self.db.flush()
        return workflow
