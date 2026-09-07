"""Allow phone numbers across retailer and customer accounts.

Revision ID: allow_phone_account_types
Revises: bcc997e84d5e
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "allow_phone_account_types"
down_revision: Union[str, None] = "bcc997e84d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        "ix_users_phone_number",
        table_name="users",
    )

    op.create_index(
        "ix_users_phone_number",
        "users",
        ["phone_number"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_users_phone_number",
        table_name="users",
    )

    op.create_index(
        "ix_users_phone_number",
        "users",
        ["phone_number"],
        unique=True,
    )
