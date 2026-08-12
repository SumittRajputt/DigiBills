from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.product_variant import (
    ProductVariantCreateRequest,
    ProductVariantResponse,
)
from app.services.product_variant_service import (
    create_product_variant,
    get_variant_by_sku,
)


router = APIRouter(
    prefix="/product-variants",
    tags=["Product Variants"],
)


def variant_to_response(variant):
    return ProductVariantResponse(
        id=str(variant.id),
        product_id=str(variant.product_id),
        sku=variant.sku,
        barcode=variant.barcode,
        variant_name=variant.variant_name,
        selling_price=variant.selling_price,
        purchase_cost=variant.purchase_cost,
        tax_rate=variant.tax_rate,
        track_inventory=variant.track_inventory,
        requires_serial_number=variant.requires_serial_number,
        status=variant.status,
    )


@router.post(
    "",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_variant_endpoint(
    request: ProductVariantCreateRequest,
    current_user: User = Depends(
        require_permission("product.manage")
    ),
    db: Session = Depends(get_db),
):
    try:
        variant = create_product_variant(
            db=db,
            product_code=request.product_code,
            sku=request.sku,
            barcode=request.barcode,
            variant_name=request.variant_name,
            selling_price=request.selling_price,
            purchase_cost=request.purchase_cost,
            tax_rate=request.tax_rate,
            track_inventory=request.track_inventory,
            requires_serial_number=request.requires_serial_number,
        )

        return variant_to_response(variant)

    except ValueError as exc:
        if str(exc) == "Product not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/{sku}",
    response_model=ProductVariantResponse,
)
def get_product_variant_endpoint(
    sku: str,
    current_user: User = Depends(
        require_permission("product.view")
    ),
    db: Session = Depends(get_db),
):
    variant = get_variant_by_sku(
        db,
        sku,
    )

    if variant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found.",
        )

    return variant_to_response(variant)