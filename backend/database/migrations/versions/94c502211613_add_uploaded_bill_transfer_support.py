"""add uploaded bill transfer support

Revision ID: 94c502211613
Revises: e67d056d4573
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "94c502211613"
down_revision: Union[str, Sequence[str], None] = "e67d056d4573"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "customer_digibills",
        sa.Column(
            "verified_serial_number",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "customer_digibills",
        sa.Column(
            "serial_verification_status",
            sa.String(length=30),
            nullable=False,
            server_default="not_required",
        ),
    )

    op.add_column(
        "customer_digibills",
        sa.Column(
            "serial_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_customer_digibills_verified_serial_number",
        "customer_digibills",
        ["verified_serial_number"],
        unique=False,
    )

    op.add_column(
        "product_transfers",
        sa.Column(
            "digibill_id",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.add_column(
        "product_transfers",
        sa.Column(
            "verified_serial_number",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "product_transfers",
        sa.Column(
            "transfer_source",
            sa.String(length=30),
            nullable=False,
            server_default="registered_product",
        ),
    )

    op.alter_column(
        "product_transfers",
        "product_unit_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )

    op.create_foreign_key(
        "fk_product_transfers_digibill",
        "product_transfers",
        "customer_digibills",
        ["digibill_id"],
        ["digibill_id"],
        ondelete="RESTRICT",
    )

    op.create_index(
        "ix_product_transfers_digibill_id",
        "product_transfers",
        ["digibill_id"],
        unique=False,
    )

    op.create_check_constraint(
        "ck_product_transfers_source_reference",
        "product_transfers",
        """
        (
            transfer_source = 'registered_product'
            AND product_unit_id IS NOT NULL
            AND digibill_id IS NULL
        )
        OR
        (
            transfer_source = 'uploaded_bill'
            AND product_unit_id IS NULL
            AND digibill_id IS NOT NULL
            AND verified_serial_number IS NOT NULL
        )
        """,
    )

    op.create_check_constraint(
        "ck_customer_digibills_serial_verification_status",
        "customer_digibills",
        """
        serial_verification_status IN (
            'not_required',
            'pending',
            'verified',
            'blocked'
        )
        """,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_customer_digibills_serial_verification_status",
        "customer_digibills",
        type_="check",
    )

    op.drop_constraint(
        "ck_product_transfers_source_reference",
        "product_transfers",
        type_="check",
    )

    op.drop_index(
        "ix_product_transfers_digibill_id",
        table_name="product_transfers",
    )

    op.drop_constraint(
        "fk_product_transfers_digibill",
        "product_transfers",
        type_="foreignkey",
    )

    op.alter_column(
        "product_transfers",
        "product_unit_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )

    op.drop_column(
        "product_transfers",
        "transfer_source",
    )

    op.drop_column(
        "product_transfers",
        "verified_serial_number",
    )

    op.drop_column(
        "product_transfers",
        "digibill_id",
    )

    op.drop_index(
        "ix_customer_digibills_verified_serial_number",
        table_name="customer_digibills",
    )

    op.drop_column(
        "customer_digibills",
        "serial_verified_at",
    )

    op.drop_column(
        "customer_digibills",
        "serial_verification_status",
    )

    op.drop_column(
        "customer_digibills",
        "verified_serial_number",
    )
