import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User


RESET_TOKEN_EXPIRE_MINUTES = 30


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_password_reset_token(
    db: Session,
    user: User,
) -> str:
    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)

    # Invalidate existing unused tokens for this user.
    existing_tokens = db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
    ).scalars().all()

    for existing_token in existing_tokens:
        existing_token.used_at = datetime.now(timezone.utc)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
    )

    db.add(reset_token)
    db.commit()

    return raw_token


def get_valid_password_reset_token(
    db: Session,
    raw_token: str,
) -> Optional[PasswordResetToken]:
    token_hash = _hash_token(raw_token)

    reset_token = db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
        )
    ).scalar_one_or_none()

    if reset_token is None:
        return None

    now = datetime.now(timezone.utc)

    if reset_token.expires_at <= now:
        return None

    return reset_token


def reset_user_password(
    db: Session,
    reset_token: PasswordResetToken,
    new_password: str,
) -> User:
    user = db.execute(
        select(User).where(User.id == reset_token.user_id)
    ).scalar_one_or_none()

    if user is None:
        raise ValueError("User account not found.")

    user.password_hash = hash_password(new_password)
    reset_token.used_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user)

    return user
