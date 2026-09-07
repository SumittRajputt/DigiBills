from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.services.retailer_service import get_retailer_by_owner
from app.services.report_service import get_retailer_reports


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get("")
def get_retailer_reports_endpoint(
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

    return get_retailer_reports(
        db,
        retailer.id,
    )
