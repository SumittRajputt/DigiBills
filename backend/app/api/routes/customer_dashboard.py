from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.customer_dashboard import (
    CustomerDashboardResponse,
)
from app.services.customer_service import (
    get_customer_by_user_id,
)
from app.services.customer_dashboard_service import (
    get_customer_dashboard,
)


router = APIRouter(
    prefix="/customer",
    tags=["Customer Dashboard"],
)


@router.get(
    "/dashboard",
    response_model=CustomerDashboardResponse,
)
def get_customer_dashboard_endpoint(
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found for this user.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer is not active.",
        )

    return get_customer_dashboard(
        db=db,
        customer_id=customer.id,
    )
