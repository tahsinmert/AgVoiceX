"""multi tenant agents

Revision ID: 0002_multi_tenant_agents
Revises: 0001_initial_schema
Create Date: 2026-07-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_multi_tenant_agents"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "slug", name="uq_businesses_org_slug"),
    )

    for table_name in [
        "agents",
        "business_settings",
        "customers",
        "knowledge",
        "conversation_history",
    ]:
        op.add_column(table_name, sa.Column("organization_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            f"fk_{table_name}_organization_id",
            table_name,
            "organizations",
            ["organization_id"],
            ["id"],
        )

    op.drop_constraint("business_settings_key_key", "business_settings", type_="unique")
    op.create_unique_constraint(
        "uq_business_settings_org_key",
        "business_settings",
        ["organization_id", "key"],
    )
    op.drop_constraint("customers_phone_key", "customers", type_="unique")
    op.create_unique_constraint("uq_customers_org_phone", "customers", ["organization_id", "phone"])

    op.add_column("reservations", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_reservations_organization_id",
        "reservations",
        "organizations",
        ["organization_id"],
        ["id"],
    )
    op.add_column("agents", sa.Column("business_id", sa.Integer(), nullable=True))
    op.add_column("agents", sa.Column("provider", sa.String(length=64), nullable=True))
    op.create_foreign_key("fk_agents_business_id", "agents", "businesses", ["business_id"], ["id"])

    op.create_table(
        "prompts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_prompts_org_agent_active", "prompts", ["organization_id", "agent_id", "is_active"])

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=True),
        sa.Column("agent_id", sa.Integer(), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default="text"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("conversations")
    op.drop_index("ix_prompts_org_agent_active", table_name="prompts")
    op.drop_table("prompts")
    op.drop_constraint("uq_customers_org_phone", "customers", type_="unique")
    op.create_unique_constraint("customers_phone_key", "customers", ["phone"])
    op.drop_constraint("uq_business_settings_org_key", "business_settings", type_="unique")
    op.create_unique_constraint("business_settings_key_key", "business_settings", ["key"])
    op.drop_constraint("fk_agents_business_id", "agents", type_="foreignkey")
    op.drop_column("agents", "provider")
    op.drop_column("agents", "business_id")
    for table_name in [
        "reservations",
        "conversation_history",
        "knowledge",
        "customers",
        "business_settings",
        "agents",
    ]:
        op.drop_constraint(f"fk_{table_name}_organization_id", table_name, type_="foreignkey")
        op.drop_column(table_name, "organization_id")
    op.drop_table("businesses")
    op.drop_table("organizations")
