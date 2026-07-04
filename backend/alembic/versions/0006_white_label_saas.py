"""white label saas

Revision ID: 0006_white_label_saas
Revises: 0005_agent_runtime
Create Date: 2026-07-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_white_label_saas"
down_revision: Union[str, None] = "0005_agent_runtime"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "business_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=128), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=96), nullable=False, server_default="general"),
        sa.Column("default_settings", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("default_prompts", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("sample_knowledge", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "brand_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False, server_default="Default Brand"),
        sa.Column("logo_url", sa.String(length=512), nullable=True),
        sa.Column("primary_color", sa.String(length=32), nullable=False, server_default="#0f766e"),
        sa.Column("accent_color", sa.String(length=32), nullable=False, server_default="#f59e0b"),
        sa.Column("support_email", sa.String(length=255), nullable=True),
        sa.Column("custom_domain", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "business_id", name="uq_brand_profiles_scope"),
    )
    op.create_table(
        "rag_ingestion_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("documents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rag_ingestion_jobs_org_created", "rag_ingestion_jobs", ["organization_id", "created_at"])
    op.create_table(
        "workflow_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=True),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("definition", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "slug", name="uq_workflow_definitions_org_slug"),
    )


def downgrade() -> None:
    op.drop_table("workflow_definitions")
    op.drop_index("ix_rag_ingestion_jobs_org_created", table_name="rag_ingestion_jobs")
    op.drop_table("rag_ingestion_jobs")
    op.drop_table("brand_profiles")
    op.drop_table("business_templates")
