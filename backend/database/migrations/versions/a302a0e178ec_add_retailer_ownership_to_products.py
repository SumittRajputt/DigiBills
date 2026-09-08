"""add retailer ownership to products

Revision ID: a302a0e178ec
Revises: f08eaa40c0d6
Create Date: 2026-08-18 19:29:02.384002

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a302a0e178ec"
down_revision: Union[str, Sequence[str], None] = "f08eaa40c0d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "retailer_id",
            sa.Uuid(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_products_retailer_id",
        "products",
        "retailers",
        ["retailer_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_products_retailer_id",
        "products",
        ["retailer_id"],
    )

    op.execute(
        """
        UPDATE products
        SET retailer_id = 'c6527203-7f81-4fc3-8207-9140011cb026'
        WHERE id = 'cb7d190b-9e3f-4fc4-834e-ef12c8650f36'
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_products_retailer_id",
        table_name="products",
    )

    op.drop_constraint(
        "fk_products_retailer_id",
        "products",
        type_="foreignkey",
    )

    op.drop_column(
        "products",
        "retailer_id",
    )
