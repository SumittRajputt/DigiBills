"""Add brand settings

Revision ID: 4f3578f2baec
Revises: 95c5fcab5f63
Create Date: 2026-09-09 13:08:50.563045

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f3578f2baec"
down_revision: Union[str, Sequence[str], None] = "95c5fcab5f63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "brand_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "company_name",
            sa.String(length=120),
            nullable=False,
        ),
        sa.Column(
            "logo_url",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "primary_color",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "secondary_color",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "accent_color",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "login_tagline",
            sa.String(length=180),
            nullable=False,
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
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("brand_settings")
