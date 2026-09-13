"""actually add transfer payment payer

Revision ID: 19d1e8f4dc92
Revises: 09f5caf10954
Create Date: 2026-09-13 12:17:08.048106

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "19d1e8f4dc92"
down_revision: Union[str, Sequence[str], None] = "09f5caf10954"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "product_transfers",
        sa.Column(
            "payment_payer",
            sa.String(length=20),
            server_default="receiver",
            nullable=False,
        ),
    )

    op.create_check_constraint(
        "ck_product_transfers_payment_payer",
        "product_transfers",
        "payment_payer IN ('sender', 'receiver')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_product_transfers_payment_payer",
        "product_transfers",
        type_="check",
    )

    op.drop_column(
        "product_transfers",
        "payment_payer",
    )
