import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.schemas.user_role import UserRoleRequest
from app.services.authorization_service import get_user_roles
from app.services.user_role_service import (
    assign_role_to_user,
    remove_role_from_user,
)
from app.services.user_service import (
    get_all_users,
    get_user_by_id,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def user_to_response(
    db: Session,
    user: User,
) -> UserResponse:
    roles = get_user_roles(
        db=db,
        user_id=user.id,
    )

    return UserResponse(
        id=str(user.id),
        phone_number=user.phone_number,
        email=user.email,
        status=user.status,
        is_phone_verified=user.is_phone_verified,
        roles=[role.name for role in roles],
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.get(
    "",
    response_model=list[UserResponse],
)
def list_users(
    current_user: User = Depends(
        require_permission("user.view")
    ),
    db: Session = Depends(get_db),
):
    users = get_all_users(db)

    return [
        user_to_response(db, user)
        for user in users
    ]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: str,
    current_user: User = Depends(
        require_permission("user.view")
    ),
    db: Session = Depends(get_db),
):
    try:
        parsed_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID.",
        )

    user = get_user_by_id(db, parsed_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user_to_response(db, user)


@router.post(
    "/{user_id}/roles",
    response_model=UserResponse,
)
def assign_user_role(
    user_id: str,
    request: UserRoleRequest,
    current_user: User = Depends(
        require_permission("user.manage")
    ),
    db: Session = Depends(get_db),
):
    try:
        parsed_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID.",
        )

    user = get_user_by_id(db, parsed_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    try:
        assign_role_to_user(
            db=db,
            user=user,
            role_name=request.role_name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return user_to_response(db, user)


@router.delete(
    "/{user_id}/roles/{role_name}",
    response_model=UserResponse,
)
def remove_user_role(
    user_id: str,
    role_name: str,
    current_user: User = Depends(
        require_permission("user.manage")
    ),
    db: Session = Depends(get_db),
):
    try:
        parsed_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID.",
        )

    user = get_user_by_id(db, parsed_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    removed = remove_role_from_user(
        db=db,
        user=user,
        role_name=role_name,
    )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found.",
        )

    return user_to_response(db, user)
