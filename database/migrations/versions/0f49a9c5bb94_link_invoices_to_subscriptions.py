"""link invoices to subscriptions

Revision ID: AUTO
Revises: 3ba4d40c4d17
"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "3ba4d40c4d17"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "invoices",
        "retailer_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )

    op.add_column(
        "invoices",
        sa.Column(
            "subscription_id",
            sa.Uuid(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_invoices_subscription_id",
        "invoices",
        "subscriptions",
        ["subscription_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_invoices_subscription_id",
        "invoices",
        ["subscription_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_invoices_subscription_id",
        table_name="invoices",
    )

    op.drop_constraint(
        "fk_invoices_subscription_id",
        "invoices",
        type_="foreignkey",
    )

    op.drop_column(
        "invoices",
        "subscription_id",
    )

    op.alter_column(
        "invoices",
        "retailer_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
