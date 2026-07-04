from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RuntimeEvent(Base):
    __tablename__ = "runtime_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id"))
    agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"))
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversation_history.id"))
    event_type: Mapped[str] = mapped_column(String(96))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id"))
    agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    memory_type: Mapped[str] = mapped_column(String(64), default="conversation")
    content: Mapped[str] = mapped_column(Text)
    memory_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PluginManifest(Base):
    __tablename__ = "plugin_manifests"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(128))
    version: Mapped[str] = mapped_column(String(64), default="0.1.0")
    enabled: Mapped[bool] = mapped_column(default=True)
    capabilities: Mapped[list[str]] = mapped_column(JSON, default=list)
    config_schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
