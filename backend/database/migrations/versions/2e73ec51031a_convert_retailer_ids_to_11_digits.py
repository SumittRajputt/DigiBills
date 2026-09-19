"""convert retailer ids to 11 digits

Revision ID: 2e73ec51031a
Revises: 19d1e8f4dc92
Create Date: 2026-09-13
"""

from alembic import op
import sqlalchemy as sa
import secrets


revision = "2e73ec51031a"
down_revision = "19d1e8f4dc92"
branch_labels = None
depends_on = None


def _generate_retailer_id(existing_ids: set[str]) -> str:
    while True:
        retailer_id = str(
            secrets.randbelow(90_000_000_000)
            + 10_000_000_000
        )

        if retailer_id not in existing_ids:
            existing_ids.add(retailer_id)
            return retailer_id


def upgrade() -> None:
    connection = op.get_bind()

    rows = connection.execute(
        sa.text(
            "SELECT id, retailer_id "
            "FROM retailers "
            "ORDER BY created_at ASC, id ASC"
        )
    ).fetchall()

    existing_ids: set[str] = set()

    # Generate the new permanent 11-digit IDs first.
    replacements = []

    for row in rows:
        new_id = _generate_retailer_id(existing_ids)
        replacements.append((row.id, new_id))

    # Temporarily expand the column so existing RET-... values
    # can safely coexist while the replacement values are written.
    op.alter_column(
        "retailers",
        "retailer_id",
        existing_type=sa.String(length=30),
        type_=sa.String(length=30),
        existing_nullable=False,
    )

    for retailer_uuid, new_id in replacements:
        connection.execute(
            sa.text(
                "UPDATE retailers "
                "SET retailer_id = :retailer_id "
                "WHERE id = :id"
            ),
            {
                "retailer_id": new_id,
                "id": retailer_uuid,
            },
        )

    # Enforce the permanent 11-digit format at database level.
    op.alter_column(
        "retailers",
        "retailer_id",
        existing_type=sa.String(length=30),
        type_=sa.String(length=11),
        existing_nullable=False,
    )

    op.create_check_constraint(
        "ck_retailers_retailer_id_11_digits",
        "retailers",
        "retailer_id ~ '^[0-9]{11}$'",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_retailers_retailer_id_11_digits",
        "retailers",
        type_="check",
    )

    op.alter_column(
        "retailers",
        "retailer_id",
        existing_type=sa.String(length=11),
        type_=sa.String(length=30),
        existing_nullable=False,
    )
