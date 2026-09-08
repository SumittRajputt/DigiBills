"""separate customer bill and transfer fees

Revision ID: bf210b8782eb
Revises: d958148ffa16
"""

from alembic import op
import sqlalchemy as sa


revision = "bf210b8782eb"
down_revision = "d958148ffa16"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "payment_configurations",
        sa.Column(
            "customer_bill_charge",
            sa.Numeric(14, 2),
            nullable=False,
            server_default=sa.text("5.00"),
        ),
    )

    op.add_column(
        "payment_configurations",
        sa.Column(
            "customer_transfer_fee",
            sa.Numeric(14, 2),
            nullable=False,
            server_default=sa.text("9.00"),
        ),
    )


def downgrade():
    op.drop_column(
        "payment_configurations",
        "customer_transfer_fee",
    )

    op.drop_column(
        "payment_configurations",
        "customer_bill_charge",
    )
