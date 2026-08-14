"""add product units and update product ownership

Revision ID: df95ce98256e
Revises: 514754f68c54
Create Date: 2026-08-13 11:41:25.565639

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "df95ce98256e"
down_revision: Union[str, Sequence[str], None] = "514754f68c54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "product_units",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "product_variant_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "serial_number",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
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
        sa.ForeignKeyConstraint(
            ["product_variant_id"],
            ["product_variants.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_product_units_serial_number",
        "product_units",
        ["serial_number"],
        unique=True,
    )

    op.add_column(
        "product_ownerships",
        sa.Column(
            "product_unit_id",
            sa.Uuid(),
            nullable=False,
        ),
    )

    op.drop_constraint(
        "product_ownerships_product_variant_id_fkey",
        "product_ownerships",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "product_ownerships_product_unit_id_fkey",
        "product_ownerships",
        "product_units",
        ["product_unit_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_column(
        "product_ownerships",
        "product_variant_id",
    )


def downgrade() -> None:
    """Downgrade schema."""

    # This migration is only reversible while product_ownerships
    # contains no records. Existing ownership records cannot be
    # safely converted back from product_unit_id to product_variant_id
    # without data migration.
    connection = op.get_bind()

    ownership_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM product_ownerships")
    ).scalar_one()

    if ownership_count != 0:
        raise RuntimeError(
            "Cannot downgrade product ownership migration while "
            "product_ownerships contains records."
        )

    op.add_column(
        "product_ownerships",
        sa.Column(
            "product_variant_id",
            sa.Uuid(),
            nullable=False,
        ),
    )

    op.drop_constraint(
        "product_ownerships_product_unit_id_fkey",
        "product_ownerships",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "product_ownerships_product_variant_id_fkey",
        "product_ownerships",
        "product_variants",
        ["product_variant_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_column(
        "product_ownerships",
        "product_unit_id",
    )

    op.drop_index(
        "ix_product_units_serial_number",
        table_name="product_units",
    )

    op.drop_table("product_units")
