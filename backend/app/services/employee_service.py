import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.access_control import user_roles
from app.models.employee import Employee
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import get_user_by_email, get_user_by_phone
from app.services.plan_limit_service import (
    PlanLimitExceededError,
    get_limit_configuration,
    get_retailer_subscription_and_plan,
)
from app.services.retailer_service import get_retailer_by_owner
from app.services.user_role_service import assign_role_to_user


ALLOWED_EMPLOYEE_ROLES = {
    "retailer_manager",
    "cashier",
    "inventory_manager",
    "salesman",
}


def generate_employee_id() -> str:
    return f"EMP-{uuid.uuid4().hex[:10].upper()}"


def get_employee_by_id(
    db: Session,
    employee_id: uuid.UUID,
) -> Optional[Employee]:
    statement = select(Employee).where(
        Employee.id == employee_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_employee_by_reference(
    db: Session,
    employee_reference: str,
) -> Optional[Employee]:
    statement = select(Employee).where(
        Employee.employee_id == employee_reference
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_active_employee_count(
    db: Session,
    retailer_id: uuid.UUID,
) -> int:
    statement = select(
        func.count(Employee.id)
    ).where(
        Employee.retailer_id == retailer_id,
        Employee.status == "active",
    )

    return int(
        db.execute(statement).scalar_one()
    )


def check_employee_limit(
    db: Session,
    retailer_id: uuid.UUID,
) -> None:
    subscription, plan = (
        get_retailer_subscription_and_plan(
            db,
            retailer_id,
        )
    )

    unlimited, limit = get_limit_configuration(
        plan,
        "employees",
    )

    if unlimited:
        return

    if limit is None:
        raise ValueError(
            "Employee limit is not configured for "
            "the retailer's subscription plan."
        )

    usage = get_active_employee_count(
        db,
        retailer_id,
    )

    if usage >= limit:
        raise PlanLimitExceededError(
            f"Employee limit of {limit} has been reached "
            f"for the retailer's subscription plan."
        )


def create_employee(
    db: Session,
    owner_user: User,
    name: str,
    phone_number: str,
    email: Optional[str],
    password: str,
    employee_type: str,
) -> Employee:
    retailer = get_retailer_by_owner(
        db,
        owner_user.id,
    )

    if retailer is None:
        raise ValueError(
            "Retailer not found for this user."
        )

    if retailer.status != "active":
        raise ValueError(
            "Retailer is not active."
        )

    if employee_type not in ALLOWED_EMPLOYEE_ROLES:
        raise ValueError(
            "Invalid employee role."
        )

    check_employee_limit(
        db,
        retailer.id,
    )

    existing_phone = get_user_by_phone(
        db,
        phone_number,
    )

    if existing_phone:
        raise ValueError(
            "A user with this phone number already exists."
        )

    if email:
        existing_email = get_user_by_email(
            db,
            email,
        )

        if existing_email:
            raise ValueError(
                "A user with this email already exists."
            )

    # Role must exist before the user is created.
    role = db.execute(
        select(Role).where(
            Role.name == employee_type
        )
    ).scalar_one_or_none()

    if role is None:
        raise ValueError(
            f"Role '{employee_type}' does not exist."
        )

    from app.core.security import hash_password

    try:
        # Create user.
        user = User(
            phone_number=phone_number,
            email=email,
            password_hash=hash_password(password),
            is_phone_verified=False,
            status="active",
        )

        db.add(user)
        db.flush()

        # Assign mandatory role.
        db.execute(
            user_roles.insert().values(
                user_id=user.id,
                role_id=role.id,
            )
        )

        # Create employee record.
        employee = Employee(
            employee_id=generate_employee_id(),
            user_id=user.id,
            employee_type=employee_type,
            retailer_id=retailer.id,
            name=name,
            status="active",
        )

        db.add(employee)

        # User + role + employee are committed together.
        db.commit()
        db.refresh(employee)

        return employee

    except Exception:
        # Nothing gets left behind if any part fails.
        db.rollback()
        raise


def get_retailer_employees(
    db: Session,
    owner_user: User,
) -> list[Employee]:
    retailer = get_retailer_by_owner(
        db,
        owner_user.id,
    )

    if retailer is None:
        raise ValueError(
            "Retailer not found for this user."
        )

    statement = (
        select(Employee)
        .where(
            Employee.retailer_id == retailer.id
        )
        .order_by(Employee.created_at.desc())
    )

    return list(
        db.execute(statement).scalars().all()
    )
