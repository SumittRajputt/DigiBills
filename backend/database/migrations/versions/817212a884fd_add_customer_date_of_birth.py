"""add customer date of birth

Revision ID: 817212a884fd
Revises: 2c2486657c6f
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "817212a884fd"
down_revision = "2c2486657c6f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "customers",
        sa.Column(
            "date_of_birth",
            sa.Date(),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column(
        "customers",
        "date_of_birth",
    )
