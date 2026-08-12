from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_control import user_roles
from app.models.role import Role
from app.models.user import User


def assign_role_to_user(
    db: Session,
    user: User,
    role_name: str,
) -> Role:
    role_statement = select(Role).where(
        Role.name == role_name
    )

    role = db.execute(
        role_statement
    ).scalar_one_or_none()

    if role is None:
        raise ValueError(
            f"Role '{role_name}' does not exist."
        )

    existing_assignment = db.execute(
        select(user_roles.c.user_id).where(
            user_roles.c.user_id == user.id,
            user_roles.c.role_id == role.id,
        )
    ).first()

    if existing_assignment is None:
        db.execute(
            user_roles.insert().values(
                user_id=user.id,
                role_id=role.id,
            )
        )

        db.commit()

    return role


def remove_role_from_user(
    db: Session,
    user: User,
    role_name: str,
) -> bool:
    role_statement = select(Role).where(
        Role.name == role_name
    )

    role = db.execute(
        role_statement
    ).scalar_one_or_none()

    if role is None:
        return False

    result = db.execute(
        user_roles.delete().where(
            user_roles.c.user_id == user.id,
            user_roles.c.role_id == role.id,
        )
    )

    db.commit()

    return result.rowcount > 0


def get_user_role_names(
    db: Session,
    user: User,
) -> list:
    statement = (
        select(Role.name)
        .join(
            user_roles,
            user_roles.c.role_id == Role.id,
        )
        .where(
            user_roles.c.user_id == user.id
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )