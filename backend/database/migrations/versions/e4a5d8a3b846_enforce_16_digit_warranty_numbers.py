"""enforce 16 digit warranty numbers

Revision ID: e4a5d8a3b846
Revises: 817212a884fd
Create Date: 2026-09-13 00:46:01.193081

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e4a5d8a3b846"
down_revision: Union[str, Sequence[str], None] = "817212a884fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "warranties",
        "warranty_id",
        existing_type=sa.String(length=30),
        type_=sa.String(length=16),
        existing_nullable=False,
    )

    op.create_check_constraint(
        "ck_warranties_warranty_id_16_digits",
        "warranties",
        "warranty_id ~ '^[0-9]{16}$'",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_warranties_warranty_id_16_digits",
        "warranties",
        type_="check",
    )

    op.alter_column(
        "warranties",
        "warranty_id",
        existing_type=sa.String(length=16),
        type_=sa.String(length=30),
        existing_nullable=False,
    )
