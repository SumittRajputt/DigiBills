from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_all_users(
    db: Session,
) -> List[User]:
    statement = (
        select(User)
        .order_by(User.created_at.desc())
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_user_by_id(
    db: Session,
    user_id: UUID,
) -> Optional[User]:
    statement = select(User).where(
        User.id == user_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()
