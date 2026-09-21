"""add customer bill validation fields

Revision ID: f4397b995886
Revises: 98fdb540f61d
Create Date: 2026-09-20 11:21:33.079649

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f4397b995886"
down_revision: Union[str, Sequence[str], None] = "98fdb540f61d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "customer_bill_extractions",
        sa.Column(
            "document_status",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.add_column(
        "customer_bill_extractions",
        sa.Column(
            "validation_score",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "customer_bill_extractions",
        sa.Column(
            "validation_reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.add_column(
        "customer_bill_extractions",
        sa.Column(
            "digibill_eligible",
            sa.Boolean(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "customer_bill_extractions",
        "digibill_eligible",
    )

    op.drop_column(
        "customer_bill_extractions",
        "validation_reasons",
    )

    op.drop_column(
        "customer_bill_extractions",
        "validation_score",
    )

    op.drop_column(
        "customer_bill_extractions",
        "document_status",
    )
