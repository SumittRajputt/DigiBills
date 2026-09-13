"""convert customer IDs to 11 digits

Revision ID: 2c2486657c6f
Revises:
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa
import secrets


# revision identifiers, used by Alembic.
revision = "2c2486657c6f"
down_revision = "e975ae39c7e3"
branch_labels = None
depends_on = None


def generate_customer_id(existing_ids):
    while True:
        customer_id = str(
            secrets.randbelow(90_000_000_000)
            + 10_000_000_000
        )

        if customer_id not in existing_ids:
            return customer_id


def upgrade():
    connection = op.get_bind()

    customers = connection.execute(
        sa.text(
            """
            SELECT id, customer_id
            FROM customers
            ORDER BY id
            """
        )
    ).fetchall()

    existing_ids = set()

    for customer in customers:
        new_customer_id = generate_customer_id(existing_ids)

        connection.execute(
            sa.text(
                """
                UPDATE customers
                SET customer_id = :customer_id
                WHERE id = :id
                """
            ),
            {
                "customer_id": new_customer_id,
                "id": customer.id,
            },
        )

        existing_ids.add(new_customer_id)

    op.alter_column(
        "customers",
        "customer_id",
        existing_type=sa.String(length=30),
        type_=sa.String(length=11),
        existing_nullable=False,
    )

    op.create_check_constraint(
        "ck_customers_customer_id_11_digits",
        "customers",
        "customer_id ~ '^[0-9]{11}$'",
    )


def downgrade():
    raise NotImplementedError(
        "Customer ID migration is intentionally irreversible because "
        "customer IDs are permanent system-generated identifiers."
    )
