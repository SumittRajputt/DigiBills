"""add customer bill charge to invoices

Revision ID: cbe6c6abb27a
Revises: bf210b8782eb
Create Date: 2026-09-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "cbe6c6abb27a"
down_revision: Union[str, None] = "bf210b8782eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "invoices",
        sa.Column(
            "customer_bill_charge",
            sa.Numeric(14, 2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "invoices",
        "customer_bill_charge",
    )
