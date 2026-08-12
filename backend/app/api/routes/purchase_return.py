import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.inventory_location import InventoryLocation
from app.models.product_variant import ProductVariant
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.purchase_return import (
    PurchaseReturnCreateRequest,
    PurchaseReturnItemCreateRequest,
    PurchaseReturnItemResponse,
    PurchaseReturnResponse,
)
from app.services.purchase_return_service import (
    add_purchase_return_item,
    create_purchase_return,
    get_purchase_return_by_reference,
    get_purchase_return_items,
    get_purchase_returns_for_retailer,
    process_purchase_return,
)
from app.services.retailer_service import get_retailer_by_owner


router = APIRouter(
    prefix="/purchase-returns",
    tags=["Purchase Returns"],
)


def purchase_return_to_response(
    purchase_return: object,
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


def purchase_return_item_to_response(
    item: object,
) -> PurchaseReturnItemResponse:
    return PurchaseReturnItemResponse(
        id=str(item.id),
        purchase_return_id=str(
            item.purchase_return_id
        ),
        purchase_order_item_id=str(
            item.purchase_order_item_id
        ),
        product_variant_id=str(
            item.product_variant_id
        ),
        product_name=item.product_name,
        sku=item.sku,
        quantity=item.quantity,
        unit_cost=item.unit_cost,
        return_amount=item.return_amount,
        reason=item.reason,
        condition=item.condition,
        created_at=item.created_at,
    )


def get_purchase_order(
    db: Session,
    purchase_order_reference: str,
):
    statement = select(PurchaseOrder).where(
        PurchaseOrder.purchase_order_id
        == purchase_order_reference
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_supplier(
    db: Session,
    supplier_id: uuid.UUID,
):
    statement = select(Supplier).where(
        Supplier.id == supplier_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_location(
    db: Session,
    location_id: uuid.UUID,
    retailer_id: uuid.UUID,
):
    statement = select(InventoryLocation).where(
        InventoryLocation.id == location_id,
        InventoryLocation.retailer_id == retailer_id,
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


@router.post(
    "",
    response_model=PurchaseReturnResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_purchase_return_endpoint(
    request: PurchaseReturnCreateRequest,
    current_user: User = Depends(
        require_permission("inventory.manage")
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
            detail="Retailer not found.",
        )

    purchase_order = get_purchase_order(
        db,
        request.purchase_order_id,
    )

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found.",
        )

    if purchase_order.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found.",
        )

    supplier = get_supplier(
        db,
        purchase_order.supplier_id,
    )

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    location = get_location(
        db,
        purchase_order.location_id,
        retailer.id,
    )

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory location not found.",
        )

    try:
        purchase_return = create_purchase_return(
            db=db,
            retailer=retailer,
            purchase_order=purchase_order,
            supplier=supplier,
            location=location,
            reason=request.reason,
            notes=request.notes,
        )

        return purchase_return_to_response(
            purchase_return
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[PurchaseReturnResponse],
)
def list_purchase_returns_endpoint(
    current_user: User = Depends(
        require_permission("inventory.view")
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
            detail="Retailer not found.",
        )

    returns = get_purchase_returns_for_retailer(
        db,
        retailer.id,
    )

    return [
        purchase_return_to_response(
            purchase_return
        )
        for purchase_return in returns
    ]


@router.get(
    "/{return_id}",
    response_model=PurchaseReturnResponse,
)
def get_purchase_return_endpoint(
    return_id: str,
    current_user: User = Depends(
        require_permission("inventory.view")
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
            detail="Purchase return not found.",
        )

    purchase_return = get_purchase_return_by_reference(
        db,
        return_id,
    )

    if (
        purchase_return is None
        or purchase_return.retailer_id != retailer.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase return not found.",
        )

    return purchase_return_to_response(
        purchase_return
    )


@router.post(
    "/{return_id}/items",
    response_model=PurchaseReturnItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_purchase_return_item_endpoint(
    return_id: str,
    request: PurchaseReturnItemCreateRequest,
    current_user: User = Depends(
        require_permission("inventory.manage")
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
            detail="Retailer not found.",
        )

    purchase_return = get_purchase_return_by_reference(
        db,
        return_id,
    )

    if (
        purchase_return is None
        or purchase_return.retailer_id != retailer.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase return not found.",
        )

    try:
        purchase_order_item_id = uuid.UUID(
            request.purchase_order_item_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order item ID.",
        )

    statement = select(
        PurchaseOrderItem
    ).where(
        PurchaseOrderItem.id
        == purchase_order_item_id,
        PurchaseOrderItem.purchase_order_id
        == purchase_return.purchase_order_id,
    )

    purchase_order_item = db.execute(
        statement
    ).scalar_one_or_none()

    if purchase_order_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order item not found.",
        )

    variant_statement = select(
        ProductVariant
    ).where(
        ProductVariant.id
        == purchase_order_item.product_variant_id
    )

    product_variant = db.execute(
        variant_statement
    ).scalar_one_or_none()

    if product_variant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found.",
        )

    try:
        item = add_purchase_return_item(
            db=db,
            purchase_return=purchase_return,
            purchase_order_item=purchase_order_item,
            product_variant=product_variant,
            quantity=request.quantity,
            reason=request.reason,
            condition=request.condition,
        )

        return purchase_return_item_to_response(item)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/{return_id}/items",
    response_model=list[PurchaseReturnItemResponse],
)
def get_purchase_return_items_endpoint(
    return_id: str,
    current_user: User = Depends(
        require_permission("inventory.view")
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
            detail="Purchase return not found.",
        )

    purchase_return = get_purchase_return_by_reference(
        db,
        return_id,
    )

    if (
        purchase_return is None
        or purchase_return.retailer_id != retailer.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase return not found.",
        )

    items = get_purchase_return_items(
        db,
        purchase_return.id,
    )

    return [
        purchase_return_item_to_response(item)
        for item in items
    ]


@router.post(
    "/{return_id}/process",
    response_model=PurchaseReturnResponse,
)
def process_purchase_return_endpoint(
    return_id: str,
    current_user: User = Depends(
        require_permission("inventory.manage")
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
            detail="Retailer not found.",
        )

    purchase_return = get_purchase_return_by_reference(
        db,
        return_id,
    )

    if (
        purchase_return is None
        or purchase_return.retailer_id != retailer.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase return not found.",
        )

    try:
        purchase_return = process_purchase_return(
            db=db,
            purchase_return=purchase_return,
            retailer=retailer,
            processed_by_user_id=current_user.id,
        )

        return purchase_return_to_response(
            purchase_return
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )