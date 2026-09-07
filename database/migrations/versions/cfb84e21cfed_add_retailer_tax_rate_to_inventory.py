"""add retailer tax rate to inventory

Revision ID: cfb84e21cfed
Revises: cbe6c6abb27a
Create Date: 2026-09-06 13:34:51.876260

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cfb84e21cfed"
down_revision: Union[str, Sequence[str], None] = "cbe6c6abb27a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add retailer-controlled GST rate to inventory items."""

    op.add_column(
        "inventory_items",
        sa.Column(
            "tax_rate",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
    )

    # Preserve the existing GST configuration for inventory already created.
    # New inventory can override this with the retailer's chosen tax rate.
    op.execute(
        """
        UPDATE inventory_items AS i
        SET tax_rate = COALESCE(pv.tax_rate, 0)
        FROM product_variants AS pv
        WHERE i.product_variant_id = pv.id
        """
    )

    # From this point onward, the application controls the actual value.
    op.alter_column(
        "inventory_items",
        "tax_rate",
        server_default=None,
    )


def downgrade() -> None:
    """Remove retailer-controlled GST rate from inventory items."""

    op.drop_column("inventory_items", "tax_rate")
