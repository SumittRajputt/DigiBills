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


def register_user(
    db: Session,
    phone_number: str,
    email: Optional[str],
    password: str,
) -> User:

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

    user = User(
        phone_number=phone_number,
        email=email,
        password_hash=hash_password(password),
        is_phone_verified=False,
        status="active",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    phone_number: str,
    password: str,
) -> Optional[User]:

    user = get_user_by_phone(
        db,
        phone_number,
    )

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

    user.last_login_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    return user


def create_user_token(user: User) -> str:
    return create_access_token(
        str(user.id)
    )