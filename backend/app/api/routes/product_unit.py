from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.product_unit import (
    ProductUnitCreateRequest,
    ProductUnitResponse,
)
from app.services.product_unit_service import create_product_unit


router = APIRouter(
    prefix="/product-units",
    tags=["Product Units"],
)


def product_unit_to_response(
    product_unit,
) -> ProductUnitResponse:
    return ProductUnitResponse(
        id=str(product_unit.id),
        product_variant_id=str(
            product_unit.product_variant_id
        ),
        serial_number=product_unit.serial_number,
        status=product_unit.status,
        created_at=product_unit.created_at,
        updated_at=product_unit.updated_at,
    )


@router.post(
    "",
    response_model=ProductUnitResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_unit_endpoint(
    request: ProductUnitCreateRequest,
    current_user: User = Depends(
        require_permission("inventory.manage")
    ),
    db: Session = Depends(get_db),
):
    try:
        product_unit = create_product_unit(
            db=db,
            product_variant_id=request.product_variant_id,
            serial_number=request.serial_number,
            status=request.status,
        )

        return product_unit_to_response(product_unit)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
