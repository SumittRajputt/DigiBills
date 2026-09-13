"""Add customer profile image

Revision ID: e975ae39c7e3
Revises: 014c8df640ae
Create Date: 2026-09-12 17:36:30.967083

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e975ae39c7e3"
down_revision: Union[str, Sequence[str], None] = "014c8df640ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "customers",
        sa.Column("profile_image_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("customers", "profile_image_url")
