"""add uncertain bill review deadline

Revision ID: e67d056d4573
Revises: 1481d5579431
Create Date: 2026-09-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e67d056d4573"
down_revision: Union[str, None] = "1481d5579431"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "customer_uploaded_bills",
        sa.Column(
            "review_deadline_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_customer_uploaded_bills_review_deadline_at",
        "customer_uploaded_bills",
        ["review_deadline_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_customer_uploaded_bills_review_deadline_at",
        table_name="customer_uploaded_bills",
    )

    op.drop_column(
        "customer_uploaded_bills",
        "review_deadline_at",
    )
