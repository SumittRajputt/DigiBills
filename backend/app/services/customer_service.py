import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.access_control import user_roles
from app.models.user import User
from app.models.role import Role


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

    try:
        db.add(customer)

        # User + role + customer profile are committed together.
        db.commit()
        db.refresh(customer)

        return customer

    except Exception:
        db.rollback()
        raise

def create_customer_for_retailer(
    db: Session,
    full_name: str,
    phone_number: str,
    email: Optional[str] = None,
) -> Customer:
    """
    Create a customer from the retailer invoice flow.

    The retailer is creating the customer, so the retailer's
    authenticated user must NOT be used as the customer's user_id.

    A separate User record is created for the customer.
    The customer initially has no password because their profile
    is being created by the retailer.
    """

    phone_number = phone_number.strip()

    if not phone_number:
        raise ValueError(
            "Phone number is required."
        )

    # Find an existing CUSTOMER account for this phone.
    # The same phone number may also belong to a retailer account.
    customer_role = db.execute(
        select(Role).where(
            Role.name == "customer"
        )
    ).scalar_one_or_none()

    if customer_role is None:
        raise ValueError(
            "Customer role is not configured. Customer creation is unavailable."
        )

    existing_user = db.execute(
        select(User)
        .join(
            user_roles,
            user_roles.c.user_id == User.id,
        )
        .where(
            User.phone_number == phone_number,
            user_roles.c.role_id == customer_role.id,
        )
    ).scalar_one_or_none()

    if existing_user is not None:

        # If that user already has a customer profile,
        # return that profile instead of creating a duplicate.
        existing_customer = get_customer_by_user_id(
            db,
            existing_user.id,
        )

        if existing_customer is not None:
            raise ValueError(
                "A customer with this phone number already exists."
            )

        # Existing user but no customer profile:
        # attach a new customer profile to that user.
        user = existing_user

        if email:
            existing_email_user = get_user_by_email(
                db,
                email,
            )

            if (
                existing_email_user is not None
                and existing_email_user.id != user.id
            ):
                raise ValueError(
                    "A user with this email already exists."
                )

            if not user.email:
                user.email = email

    else:
        # Email must also be unique.
        if email:
            existing_email_user = get_user_by_email(
                db,
                email,
            )

            if existing_email_user is not None:
                raise ValueError(
                    "A user with this email already exists."
                )

        # A customer role must exist before a new user can be created.
        customer_role = db.execute(
            select(Role).where(
                Role.name == "customer"
            )
        ).scalar_one_or_none()

        if customer_role is None:
            raise ValueError(
                "Customer role is not configured. Customer creation is unavailable."
            )

        # Customer-created user:
        # no password yet because registration was performed
        # by the retailer.
        user = User(
            phone_number=phone_number,
            email=email,
            password_hash=None,
            is_phone_verified=False,
            status="active",
        )

        db.add(user)
        db.flush()

        # Assign the mandatory customer role.
        db.execute(
            user_roles.insert().values(
                user_id=user.id,
                role_id=customer_role.id,
            )
        )

    customer = Customer(
        customer_id=generate_customer_id(),
        user_id=user.id,
        full_name=full_name.strip(),
        phone_number=phone_number,
        email=email or user.email,
        status="active",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer
