"""update transfer workflow

Revision ID: d958148ffa16
Revises: 842e26e70b37
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d958148ffa16"
down_revision: Union[str, Sequence[str], None] = "842e26e70b37"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "product_transfers",
        sa.Column(
            "transfer_fee",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0.00",
        ),
    )

    op.add_column(
        "product_transfers",
        sa.Column(
            "payment_status",
            sa.String(30),
            nullable=False,
            server_default="not_required",
        ),
    )

    op.add_column(
        "product_transfers",
        sa.Column(
            "payment_invoice_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.add_column(
        "product_transfers",
        sa.Column(
            "payment_reference",
            sa.String(30),
            nullable=True,
        ),
    )

    op.add_column(
        "product_transfers",
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_product_transfers_payment_invoice",
        "product_transfers",
        "invoices",
        ["payment_invoice_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Existing pending records become receiver-acceptance records.
    op.execute(
        """
        UPDATE product_transfers
        SET status = 'pending_acceptance'
        WHERE status = 'pending'
        """
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_product_transfers_payment_invoice",
        "product_transfers",
        type_="foreignkey",
    )

    op.drop_column(
        "product_transfers",
        "accepted_at",
    )

    op.drop_column(
        "product_transfers",
        "payment_reference",
    )

    op.drop_column(
        "product_transfers",
        "payment_invoice_id",
    )

    op.drop_column(
        "product_transfers",
        "payment_status",
    )

    op.drop_column(
        "product_transfers",
        "transfer_fee",
    )
