from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.models.warranty import Warranty
from app.schemas.warranty import WarrantyResponse
from app.services.customer_service import get_customer_by_user_id


router = APIRouter(
    prefix="/customer/warranty",
    tags=["Customer Warranty"],
)


def warranty_to_response(warranty: Warranty) -> WarrantyResponse:
    return WarrantyResponse(
        id=str(warranty.id),
        warranty_id=warranty.warranty_id,
        invoice_id=str(warranty.invoice_id),
        product_variant_id=str(warranty.product_variant_id),
        customer_id=str(warranty.customer_id),
        start_date=warranty.start_date,
        end_date=warranty.end_date,
        duration_months=warranty.duration_months,
        is_transferable=warranty.is_transferable,
        status=warranty.status,
        created_at=warranty.created_at,
        updated_at=warranty.updated_at,
    )


@router.get(
    "",
    response_model=list[WarrantyResponse],
)
def list_customer_warranties(
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

    warranties = db.execute(
        select(Warranty)
        .where(
            Warranty.customer_id == customer.id,
        )
        .order_by(
            Warranty.created_at.desc(),
        )
    ).scalars().all()

    return [
        warranty_to_response(warranty)
        for warranty in warranties
    ]
