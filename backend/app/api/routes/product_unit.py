from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.product_unit import (
    ProductUnitCreateRequest,
    ProductUnitResponse,
)
from app.services.product_unit_service import (
    create_product_unit,
    get_product_units_by_variant,
)


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


@router.get(
    "/variant/{product_variant_id}",
    response_model=list[ProductUnitResponse],
)
def list_product_units_endpoint(
    product_variant_id: str,
    current_user: User = Depends(
        require_permission("product.view")
    ),
    db: Session = Depends(get_db),
):
    try:
        parsed_id = __import__("uuid").UUID(product_variant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid product variant ID.",
        )

    units = get_product_units_by_variant(
        db,
        parsed_id,
    )

    return [
        product_unit_to_response(unit)
        for unit in units
    ]



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
