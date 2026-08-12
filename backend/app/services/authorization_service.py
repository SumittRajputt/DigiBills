from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_control import role_permissions, user_roles
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


def get_user_roles(
    db: Session,
    user_id: UUID,
) -> List[Role]:
    statement = (
        select(Role)
        .join(
            user_roles,
            user_roles.c.role_id == Role.id,
        )
        .where(
            user_roles.c.user_id == user_id
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_user_permissions(
    db: Session,
    user_id: UUID,
) -> List[Permission]:
    statement = (
        select(Permission)
        .join(
            role_permissions,
            role_permissions.c.permission_id == Permission.id,
        )
        .join(
            user_roles,
            user_roles.c.role_id == role_permissions.c.role_id,
        )
        .where(
            user_roles.c.user_id == user_id
        )
        .distinct()
    )

    return list(
        db.execute(statement).scalars().all()
    )


def user_has_role(
    db: Session,
    user: User,
    role_name: str,
) -> bool:
    roles = get_user_roles(
        db,
        user.id,
    )

    return any(
        role.name == role_name
        for role in roles
    )


def user_has_permission(
    db: Session,
    user: User,
    permission_name: str,
) -> bool:
    permissions = get_user_permissions(
        db,
        user.id,
    )

    return any(
        permission.name == permission_name
        for permission in permissions
    )


def get_role_by_name(
    db: Session,
    role_name: str,
) -> Optional[Role]:
    statement = select(Role).where(
        Role.name == role_name
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_permission_by_name(
    db: Session,
    permission_name: str,
) -> Optional[Permission]:
    statement = select(Permission).where(
        Permission.name == permission_name
    )

    return db.execute(
        statement
    ).scalar_one_or_none()