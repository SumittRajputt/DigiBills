from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.models.role import Role
from app.models.employee import Employee
from app.models.access_control import user_roles


def get_user_by_phone(
    db: Session,
    phone_number: str,
) -> Optional[User]:
    statement = select(User).where(
        User.phone_number == phone_number
    )

    return db.execute(statement).scalar_one_or_none()


def get_user_by_email(
    db: Session,
    email: str,
) -> Optional[User]:
    statement = select(User).where(
        User.email == email
    )

    return db.execute(statement).scalar_one_or_none()


def phone_has_role(
    db: Session,
    phone_number: str,
    role_name: str,
) -> bool:
    statement = (
        select(user_roles.c.user_id)
        .join(
            User,
            User.id == user_roles.c.user_id,
        )
        .join(
            Role,
            Role.id == user_roles.c.role_id,
        )
        .where(
            User.phone_number == phone_number,
            Role.name == role_name,
        )
    )

    return db.execute(statement).first() is not None


def register_user(
    db: Session,
    full_name: str,
    phone_number: str,
    email: Optional[str],
    password: str,
) -> User:

    phone_number = phone_number.strip()
    full_name = full_name.strip()

    if not full_name:
        raise ValueError(
            "Full name is required."
        )

    if phone_has_role(
        db,
        phone_number,
        "customer",
    ):
        raise ValueError(
            "A customer account with this phone number already exists."
        )

    if email:
        email = email.strip().lower()

        existing_email = get_user_by_email(
            db,
            email,
        )

        if existing_email:
            raise ValueError(
                "A user with this email already exists."
            )

    # Public registration creates customer accounts only.
    customer_role = db.execute(
        select(Role).where(
            Role.name == "customer"
        )
    ).scalar_one_or_none()

    if customer_role is None:
        raise ValueError(
            "Customer role is not configured. User registration is unavailable."
        )

    # Import here to keep auth dependencies lightweight.
    from app.models.customer import Customer
    from app.services.customer_service import generate_customer_id

    try:
        # Create the login user.
        user = User(
            phone_number=phone_number,
            email=email,
            password_hash=hash_password(password),
            is_phone_verified=False,
            status="active",
        )

        db.add(user)
        db.flush()

        # Mandatory customer role assignment.
        db.execute(
            user_roles.insert().values(
                user_id=user.id,
                role_id=customer_role.id,
            )
        )

        # Create the actual DigiBills customer profile.
        customer = Customer(
            customer_id=generate_customer_id(),
            user_id=user.id,
            full_name=full_name,
            phone_number=phone_number,
            email=email,
            status="active",
        )

        db.add(customer)

        # User + role + customer profile are committed together.
        db.commit()
        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        raise


def authenticate_user(
    db: Session,
    phone_number: str,
    password: str,
    account_type: str,
) -> Optional[User]:

    phone_number = phone_number.strip()
    account_type = account_type.strip().lower()

    role_name = {
        "admin": "super_admin",
        "retailer": "retailer_owner",
        "customer": "customer",
        "salesman": "salesman",
    }.get(account_type)
    # The employee does not choose cashier/manager/etc. at login.
    if account_type == "employee":
        statement = (
            select(User)
            .join(
                Employee,
                Employee.user_id == User.id,
            )
            .where(
                User.phone_number == phone_number,
                Employee.status == "active",
            )
        )

        user = db.execute(statement).scalars().first()

        if not user:
            return None

        if not user.password_hash:
            return None

        if not verify_password(password, user.password_hash):
            return None

        if user.status != "active":
            return None

        user.last_login_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(user)

        return user

    if role_name is None:
        return None

    # Find the selected account type for this phone number.
    # The same phone number may belong to both a retailer
    # and a customer account.
    statement = (
        select(User)
        .join(
            user_roles,
            user_roles.c.user_id == User.id,
        )
        .join(
            Role,
            Role.id == user_roles.c.role_id,
        )
        .where(
            User.phone_number == phone_number,
            Role.name == role_name,
        )
    )

    user = db.execute(statement).scalars().first()

    if not user:
        return None

    if not user.password_hash:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    if user.status != "active":
        return None

    # Retailer owners can only log in after their retailer
    # registration has been approved by an administrator.
    if account_type == "retailer":
        from app.models.retailer import Retailer

        retailer = db.execute(
            select(Retailer).where(
                Retailer.owner_user_id == user.id
            )
        ).scalar_one_or_none()

        if retailer is None or retailer.status != "active":
            return None

    # Salesmen must have an active salesman employee record.
    if account_type == "salesman":
        salesman = db.execute(
            select(Employee).where(
                Employee.user_id == user.id,
                Employee.employee_type == "salesman",
                Employee.status == "active",
            )
        ).scalar_one_or_none()

        if salesman is None:
            return None

    user.last_login_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    return user


def create_user_token(user: User) -> str:
    return create_access_token(
        str(user.id)
    )

def change_user_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
) -> User:
    if not user.password_hash:
        raise ValueError(
            "This account does not have a password set."
        )

    if not verify_password(
        current_password,
        user.password_hash,
    ):
        raise ValueError(
            "Current password is incorrect."
        )

    if current_password == new_password:
        raise ValueError(
            "New password must be different from the current password."
        )

    user.password_hash = hash_password(new_password)

    db.commit()
    db.refresh(user)

    return user


def register_retailer(
    db: Session,
    phone_number: str,
    email: str,
    password: str,
    business_name: str,
    business_type: str,
    business_phone_number: str,
    business_email: Optional[str],
    address: str,
) -> tuple[User, object]:
    """
    Public retailer registration.

    Creates the user and retailer in the same transaction.
    The retailer_owner role is assigned automatically.
    The retailer starts in pending status and must be approved
    by an administrator before login is allowed.
    """

    phone_number = phone_number.strip()

    if phone_has_role(
        db,
        phone_number,
        "retailer_owner",
    ):
        raise ValueError(
            "A retailer account with this phone number already exists."
        )

    existing_email = get_user_by_email(
        db,
        email,
    )

    if existing_email:
        raise ValueError(
            "A user with this email already exists."
        )

    retailer_role = db.execute(
        select(Role).where(
            Role.name == "retailer_owner"
        )
    ).scalar_one_or_none()

    if retailer_role is None:
        raise ValueError(
            "Retailer owner role is not configured. "
            "Retailer registration is unavailable."
        )

    # Import here to avoid circular imports.
    from app.models.retailer import Retailer
    from app.services.retailer_service import generate_retailer_id

    try:
        user = User(
            phone_number=phone_number.strip(),
            email=email,
            password_hash=hash_password(password),
            is_phone_verified=False,
            status="active",
        )

        db.add(user)
        db.flush()

        # Automatically assign retailer_owner.
        db.execute(
            user_roles.insert().values(
                user_id=user.id,
                role_id=retailer_role.id,
            )
        )

        retailer = Retailer(
            retailer_id=generate_retailer_id(),
            owner_user_id=user.id,
            business_name=business_name.strip(),
            business_type=business_type.strip(),
            phone_number=business_phone_number.strip(),
            email=business_email,
            address=address.strip(),
            status="pending",
        )

        db.add(retailer)

        db.commit()

        db.refresh(user)
        db.refresh(retailer)

        return user, retailer

    except Exception:
        db.rollback()
        raise

