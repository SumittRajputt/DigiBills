from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.product import (
    ProductCreateRequest,
    ProductResponse,
)
from app.services.retailer_service import get_retailer_by_owner
from app.services.product_service import (
    create_product,
    get_product_by_code,
    get_all_products,
)
from app.services.plan_limit_service import PlanLimitExceededError


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


def product_to_response(product):
    return ProductResponse(
        id=str(product.id),
        product_code=product.product_code,
        name=product.name,
        brand=product.brand,
        category=product.category,
        description=product.description,
        is_transferable=product.is_transferable,
        status=product.status,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_endpoint(
    request: ProductCreateRequest,
    current_user: User = Depends(
        require_permission("product.manage")
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Retailer is not active.",
        )

    try:
        product = create_product(
            db=db,
            retailer_id=retailer.id,
            name=request.name,
            product_code=request.product_code,
            brand=request.brand,
            category=request.category,
            description=request.description,
            is_transferable=request.is_transferable,
        )

        return product_to_response(product)

    except PlanLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_products(
    current_user: User = Depends(
        require_permission("product.view")
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

    products = get_all_products(
        db,
        retailer_id=retailer.id,
    )

    return [
        product_to_response(product)
        for product in products
    ]


@router.get(
    "/{product_code}",
    response_model=ProductResponse,
)
def get_product_endpoint(
    product_code: str,
    current_user: User = Depends(
        require_permission("product.view")
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

    product = get_product_by_code(
        db,
        product_code,
        retailer_id=retailer.id,
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return product_to_response(product)