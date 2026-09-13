"""add transfer payment payer

Revision ID: 62f07da75d9c
Revises: 3382877cfa93
Create Date: 2026-09-13 12:13:59.181085

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "62f07da75d9c"
down_revision: Union[str, Sequence[str], None] = "3382877cfa93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
