"""add customer bill extractions

Revision ID: 98fdb540f61d
Revises: 2a52943bbabe
Create Date: 2026-09-20 09:38:40.262076

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "98fdb540f61d"
down_revision: Union[str, Sequence[str], None] = "2a52943bbabe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "customer_bill_extractions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "uploaded_bill_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "raw_text",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "structured_data",
            postgresql.JSONB(),
            nullable=True,
        ),
        sa.Column(
            "page_count",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "extraction_engine",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "extraction_model",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_bill_id"],
            ["customer_uploaded_bills.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uploaded_bill_id"),
    )

    op.create_index(
        "ix_customer_bill_extractions_uploaded_bill_id",
        "customer_bill_extractions",
        ["uploaded_bill_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_customer_bill_extractions_uploaded_bill_id",
        table_name="customer_bill_extractions",
    )

    op.drop_table("customer_bill_extractions")
