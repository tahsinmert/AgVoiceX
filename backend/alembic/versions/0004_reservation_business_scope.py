"""reservation business scope

Revision ID: 0004_reservation_business_scope
Revises: 0003_business_layer
Create Date: 2026-07-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_reservation_business_scope"
down_revision: Union[str, None] = "0003_business_layer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("reservations")}
    foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys("reservations")}

    if "business_id" not in columns:
        op.add_column("reservations", sa.Column("business_id", sa.Integer(), nullable=True))
    if "fk_reservations_business_id" not in foreign_keys:
        op.create_foreign_key(
            "fk_reservations_business_id",
            "reservations",
            "businesses",
            ["business_id"],
            ["id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("reservations")}
    foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys("reservations")}

    if "fk_reservations_business_id" in foreign_keys:
        op.drop_constraint("fk_reservations_business_id", "reservations", type_="foreignkey")
    if "business_id" in columns:
        op.drop_column("reservations", "business_id")
