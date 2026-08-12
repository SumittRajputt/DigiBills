from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.authorization_service import (
    user_has_permission,
    user_has_role,
)


def require_role(role_name: str) -> Callable:
    def role_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not user_has_role(
            db=db,
            user=current_user,
            role_name=role_name,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' is required.",
            )

        return current_user

    return role_dependency


def require_permission(permission_name: str) -> Callable:
    def permission_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not user_has_permission(
            db=db,
            user=current_user,
            permission_name=permission_name,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' is required.",
            )

        return current_user

    return permission_dependency