"""hardening indexes

Revision ID: 0007_hardening_indexes
Revises: 0006_white_label_saas
Create Date: 2026-07-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0007_hardening_indexes"
down_revision: Union[str, None] = "0006_white_label_saas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_reservations_tenant_slot_status",
        "reservations",
        ["organization_id", "business_id", "reservation_date", "reservation_time", "status"],
    )
    op.create_index(
        "ix_conversation_history_org_created",
        "conversation_history",
        ["organization_id", "created_at"],
    )
    op.create_index("ix_knowledge_org_source", "knowledge", ["organization_id", "source"])
    op.create_index("ix_agents_org_business_active", "agents", ["organization_id", "business_id", "is_active"])
    op.create_index("ix_customers_org_created", "customers", ["organization_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_customers_org_created", table_name="customers")
    op.drop_index("ix_agents_org_business_active", table_name="agents")
    op.drop_index("ix_knowledge_org_source", table_name="knowledge")
    op.drop_index("ix_conversation_history_org_created", table_name="conversation_history")
    op.drop_index("ix_reservations_tenant_slot_status", table_name="reservations")
