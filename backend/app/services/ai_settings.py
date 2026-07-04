from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agents import Agent
from app.models.business_settings import BusinessSetting
from app.services.ai_providers import AIProvider, PROVIDER_REGISTRY, create_provider
from app.services.tenancy import TenantContext, TenantService

PROVIDER_SETTING_KEY = "ai.provider"
MODEL_SETTING_KEY = "ai.model"


class AISettingsService:
    def __init__(self, db: Session, tenant_context: TenantContext | None = None):
        self.db = db
        self.tenant_context = tenant_context or TenantService(db).get_or_create_default_context()

    def get_provider_name(self) -> str:
        setting = self._get(PROVIDER_SETTING_KEY)
        if setting and isinstance(setting.value.get("name"), str):
            return setting.value["name"]
        return settings.default_provider

    def set_provider_name(self, provider_name: str) -> BusinessSetting:
        if provider_name not in PROVIDER_REGISTRY:
            raise ValueError(f"Unsupported provider: {provider_name}")
        return self._upsert(PROVIDER_SETTING_KEY, {"name": provider_name})

    def get_model_name(self) -> str | None:
        setting = self._get(MODEL_SETTING_KEY)
        if setting and isinstance(setting.value.get("name"), str):
            return setting.value["name"]
        return None

    def set_model_name(self, model_name: str) -> BusinessSetting:
        return self._upsert(MODEL_SETTING_KEY, {"name": model_name})

    def get_provider(self) -> AIProvider:
        provider_name = self.get_provider_name()
        return create_provider(provider_name)

    async def require_model_name(self, provider: AIProvider | None = None) -> str:
        model_name = self.get_model_name()
        if model_name:
            return model_name
        active_provider = provider or self.get_provider()
        models = await active_provider.list_models()
        if not models:
            raise ValueError("No AI model is selected and the active provider has no installed models.")
        model_name = models[0]["name"]
        self.set_model_name(model_name)
        self.db.commit()
        return model_name

    async def resolve_for_agent(self, agent: Agent | None) -> tuple[AIProvider, str]:
        provider_name = agent.provider if agent and agent.provider else self.get_provider_name()
        provider = create_provider(provider_name)
        model_name = agent.model if agent and agent.model else await self.require_model_name(provider)
        return provider, model_name

    def _get(self, key: str) -> BusinessSetting | None:
        scoped = self.db.scalar(
            select(BusinessSetting).where(
                BusinessSetting.key == key,
                BusinessSetting.organization_id == self.tenant_context.organization_id,
            )
        )
        if scoped is not None:
            return scoped
        return self.db.scalar(
            select(BusinessSetting).where(
                BusinessSetting.key == key,
                BusinessSetting.organization_id.is_(None),
            )
        )

    def _upsert(self, key: str, value: dict[str, str]) -> BusinessSetting:
        setting = self.db.scalar(
            select(BusinessSetting).where(
                BusinessSetting.key == key,
                BusinessSetting.organization_id == self.tenant_context.organization_id,
            )
        )
        if setting is None:
            setting = BusinessSetting(
                organization_id=self.tenant_context.organization_id,
                key=key,
                value=value,
            )
            self.db.add(setting)
        else:
            setting.value = value
        self.db.flush()
        return setting
