from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.retailer_dashboard import (
    RetailerDashboardResponse,
)
from app.services.retailer_dashboard_service import (
    get_retailer_dashboard,
)
from app.services.retailer_service import (
    get_retailer_by_owner,
)


router = APIRouter(
    prefix="/retailer",
    tags=["Retailer Dashboard"],
)


@router.get(
    "/dashboard",
    response_model=RetailerDashboardResponse,
)
def get_retailer_dashboard_endpoint(
    current_user: User = Depends(
        require_permission("invoice.view")
    ),
    db: Session = Depends(get_db),
):
    retailer = get_retailer_by_owner(
        db,
        current_user.id,
    )

    if retailer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found for this user.",
        )

    if retailer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Retailer is not active.",
        )

    return get_retailer_dashboard(
        db=db,
        retailer_id=retailer.id,
    )
