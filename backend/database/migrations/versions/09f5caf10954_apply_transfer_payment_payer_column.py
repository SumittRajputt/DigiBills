"""apply transfer payment payer column

Revision ID: 09f5caf10954
Revises: 62f07da75d9c
Create Date: 2026-09-13 12:16:00.491618

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "09f5caf10954"
down_revision: Union[str, Sequence[str], None] = "62f07da75d9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
