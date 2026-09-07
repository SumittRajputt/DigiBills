"""add taxable amount to invoice items

Revision ID: bcc997e84d5e
Revises: cfb84e21cfed
Create Date: 2026-09-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bcc997e84d5e"
down_revision: Union[str, None] = "cfb84e21cfed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "invoice_items",
        sa.Column(
            "taxable_amount",
            sa.Numeric(14, 2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
    )

    # Existing invoice items were created using the previous
    # GST-exclusive calculation. Preserve their existing values
    # by deriving the taxable amount from the stored line total
    # and stored GST amount.
    op.execute(
        """
        UPDATE invoice_items
        SET taxable_amount = ROUND(
            line_total - tax_amount,
            2
        )
        """
    )

    op.alter_column(
        "invoice_items",
        "taxable_amount",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column(
        "invoice_items",
        "taxable_amount",
    )
