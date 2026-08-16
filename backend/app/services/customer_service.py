import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer


def generate_customer_id() -> str:
    return f"CUST-{uuid.uuid4().hex[:10].upper()}"


def get_customer_by_id(
    db: Session,
    customer_id: uuid.UUID,
) -> Optional[Customer]:
    statement = select(Customer).where(
        Customer.id == customer_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_customer_by_customer_id(
    db: Session,
    customer_id: str,
) -> Optional[Customer]:
    statement = select(Customer).where(
        Customer.customer_id == customer_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_all_customers(
    db: Session,
) -> list[Customer]:
    statement = (
        select(Customer)
        .order_by(Customer.created_at.desc())
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_customer_by_user_id(
    db: Session,
    user_id: uuid.UUID,
) -> Optional[Customer]:
    statement = select(Customer).where(
        Customer.user_id == user_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def create_customer(
    db: Session,
    user_id: uuid.UUID,
    full_name: str,
    phone_number: str,
    email: Optional[str] = None,
) -> Customer:

    existing_customer = get_customer_by_user_id(
        db,
        user_id,
    )

    if existing_customer:
        raise ValueError(
            "This user already has a customer profile."
        )

    customer = Customer(
        customer_id=generate_customer_id(),
        user_id=user_id,
        full_name=full_name,
        phone_number=phone_number,
        email=email,
        status="active",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer