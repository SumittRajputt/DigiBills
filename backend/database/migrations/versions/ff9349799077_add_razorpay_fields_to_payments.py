"""add razorpay fields to payments

Revision ID: ff9349799077
Revises: 94c502211613
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ff9349799077"
down_revision: Union[str, Sequence[str], None] = "94c502211613"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column(
            "razorpay_order_id",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.add_column(
        "payments",
        sa.Column(
            "razorpay_payment_id",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_payments_razorpay_order_id",
        "payments",
        ["razorpay_order_id"],
        unique=False,
    )

    op.create_index(
        "ix_payments_razorpay_payment_id",
        "payments",
        ["razorpay_payment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payments_razorpay_payment_id",
        table_name="payments",
    )

    op.drop_index(
        "ix_payments_razorpay_order_id",
        table_name="payments",
    )

    op.drop_column(
        "payments",
        "razorpay_payment_id",
    )

    op.drop_column(
        "payments",
        "razorpay_order_id",
    )
