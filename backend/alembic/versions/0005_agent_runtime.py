"""agent runtime

Revision ID: 0005_agent_runtime
Revises: 0004_reservation_business_scope
Create Date: 2026-07-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_agent_runtime"
down_revision: Union[str, None] = "0004_reservation_business_scope"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "runtime_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=True),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversation_history.id"), nullable=True),
        sa.Column("event_type", sa.String(length=96), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_runtime_events_org_created", "runtime_events", ["organization_id", "created_at"])
    op.create_index("ix_runtime_events_type", "runtime_events", ["event_type"])

    op.create_table(
        "agent_memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=True),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("memory_type", sa.String(length=64), nullable=False, server_default="conversation"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_memories_scope", "agent_memories", ["organization_id", "business_id", "agent_id"])
    op.create_index("ix_agent_memories_customer", "agent_memories", ["customer_id"])

    op.create_table(
        "plugin_manifests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False, server_default="0.1.0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("capabilities", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("config_schema", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "name", name="uq_plugin_manifests_org_name"),
    )


def downgrade() -> None:
    op.drop_table("plugin_manifests")
    op.drop_index("ix_agent_memories_customer", table_name="agent_memories")
    op.drop_index("ix_agent_memories_scope", table_name="agent_memories")
    op.drop_table("agent_memories")
    op.drop_index("ix_runtime_events_type", table_name="runtime_events")
    op.drop_index("ix_runtime_events_org_created", table_name="runtime_events")
    op.drop_table("runtime_events")
