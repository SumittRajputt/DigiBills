from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.authorization import require_role
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.purchase_return import PurchaseReturnResponse
from app.services.purchase_return_service import (
    get_all_purchase_returns,
)


router = APIRouter(
    prefix="/admin",
    tags=["Admin Purchase Returns"],
)


def purchase_return_to_response(
    purchase_return,
) -> PurchaseReturnResponse:
    return PurchaseReturnResponse(
        id=str(purchase_return.id),
        return_id=purchase_return.return_id,
        purchase_order_id=str(
            purchase_return.purchase_order_id
        ),
        retailer_id=str(
            purchase_return.retailer_id
        ),
        supplier_id=str(
            purchase_return.supplier_id
        ),
        location_id=str(
            purchase_return.location_id
        ),
        processed_by_user_id=(
            str(purchase_return.processed_by_user_id)
            if purchase_return.processed_by_user_id
            else None
        ),
        return_amount=purchase_return.return_amount,
        status=purchase_return.status,
        reason=purchase_return.reason,
        notes=purchase_return.notes,
        requested_at=purchase_return.requested_at,
        processed_at=purchase_return.processed_at,
        created_at=purchase_return.created_at,
        updated_at=purchase_return.updated_at,
    )


@router.get(
    "/purchase-returns",
    response_model=list[PurchaseReturnResponse],
)
def list_all_purchase_returns_endpoint(
    current_user: User = Depends(
        require_role("super_admin")
    ),
    db: Session = Depends(get_db),
):
    purchase_returns = get_all_purchase_returns(db)

    return [
        purchase_return_to_response(
            purchase_return
        )
        for purchase_return in purchase_returns
    ]
