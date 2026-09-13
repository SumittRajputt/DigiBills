"""Add product unit to warranties

Revision ID: 3382877cfa93
Revises: e4a5d8a3b846
Create Date: 2026-09-13 09:42:54.247374

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3382877cfa93"
down_revision: Union[str, Sequence[str], None] = "e4a5d8a3b846"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "warranties",
        sa.Column("product_unit_id", sa.Uuid(), nullable=True),
    )

    op.create_index(
        op.f("ix_warranties_product_unit_id"),
        "warranties",
        ["product_unit_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_warranties_product_unit_id_product_units",
        "warranties",
        "product_units",
        ["product_unit_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_warranties_product_unit_id_product_units",
        "warranties",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_warranties_product_unit_id"),
        table_name="warranties",
    )

    op.drop_column(
        "warranties",
        "product_unit_id",
    )
