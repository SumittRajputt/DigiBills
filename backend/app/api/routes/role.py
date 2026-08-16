from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleResponse


router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.get(
    "",
    response_model=list[RoleResponse],
)
def list_roles(
    current_user: User = Depends(
        require_permission("user.view")
    ),
    db: Session = Depends(get_db),
):
    statement = select(Role).order_by(Role.name)

    roles = list(
        db.execute(statement).scalars().all()
    )

    return [
        RoleResponse(
            id=str(role.id),
            name=role.name,
            description=role.description,
        )
        for role in roles
    ]
