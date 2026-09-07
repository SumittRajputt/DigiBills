from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.customer import Customer
from app.models.product import Product
from app.models.product_ownership import ProductOwnership
from app.models.product_unit import ProductUnit
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.schemas.customer_product import CustomerProductResponse
from app.services.customer_service import get_customer_by_user_id


router = APIRouter(
    prefix="/customer/products",
    tags=["Customer Products"],
)


@router.get(
    "",
    response_model=list[CustomerProductResponse],
)
def list_customer_products(
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

    rows = db.execute(
        select(
            ProductOwnership,
            ProductUnit,
            ProductVariant,
            Product,
        )
        .join(
            ProductUnit,
            ProductUnit.id == ProductOwnership.product_unit_id,
        )
        .join(
            ProductVariant,
            ProductVariant.id == ProductUnit.product_variant_id,
        )
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .where(
            ProductOwnership.customer_id == customer.id,
            ProductOwnership.ownership_status == "active",
        )
        .order_by(
            ProductOwnership.acquired_at.desc(),
        )
    ).all()

    return [
        CustomerProductResponse(
            ownership_id=str(ownership.id),
            product_unit_id=str(product_unit.id),
            product_variant_id=str(product_variant.id),
            product_id=str(product.id),

            product_name=product.name,
            product_code=product.product_code,
            brand=product.brand,
            category=product.category,
            description=product.description,

            variant_name=product_variant.variant_name,
            sku=product_variant.sku,
            barcode=product_variant.barcode,

            serial_number=product_unit.serial_number,
            product_unit_status=product_unit.status,

            ownership_status=ownership.ownership_status,
            acquired_at=ownership.acquired_at,
            released_at=ownership.released_at,
            source=ownership.source,
        )
        for (
            ownership,
            product_unit,
            product_variant,
            product,
        ) in rows
    ]
