import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.user import User
from app.schemas.purchase_order import (
    PurchaseOrderCreateRequest,
    PurchaseOrderItemCreateRequest,
    PurchaseOrderItemResponse,
    PurchaseOrderReceiveRequest,
    PurchaseOrderResponse,
)
from app.services.product_variant_service import (
    get_variant_by_sku,
)
from app.services.purchase_order_service import (
    add_purchase_order_item,
    create_purchase_order,
    get_purchase_order_by_reference,
    get_purchase_order_items,
    get_purchase_orders_for_retailer,
    receive_purchase_order_item,
    update_purchase_order_status,
)
from app.services.retailer_service import (
    get_retailer_by_owner,
)
from app.services.supplier_service import (
    get_supplier_by_supplier_id,
)


router = APIRouter(
    prefix="/purchase-orders",
    tags=["Purchase Orders"],
)


def purchase_order_to_response(order):
    return PurchaseOrderResponse(
        id=str(order.id),
        purchase_order_id=order.purchase_order_id,
        retailer_id=str(order.retailer_id),
        supplier_id=str(order.supplier_id),
        location_id=str(order.location_id),
        created_by_user_id=(
            str(order.created_by_user_id)
            if order.created_by_user_id
            else None
        ),
        status=order.status,
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount,
        expected_delivery_date=order.expected_delivery_date,
        received_at=order.received_at,
        notes=order.notes,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def purchase_order_item_to_response(
    item,
    purchase_order_id=None,
):
    return PurchaseOrderItemResponse(
        id=str(item.id),
        purchase_order_id=(
            purchase_order_id
            if purchase_order_id is not None
            else str(item.purchase_order_id)
        ),
        product_variant_id=str(item.product_variant_id),
        product_name=item.product_name,
        sku=item.sku,
        ordered_quantity=item.ordered_quantity,
        received_quantity=item.received_quantity,
        unit_cost=item.unit_cost,
        tax_rate=item.tax_rate,
        tax_amount=item.tax_amount,
        line_total=item.line_total,
        received_at=item.received_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def get_location_for_retailer(
    db: Session,
    location_id: str,
    retailer_id,
):
    try:
        parsed_location_id = uuid.UUID(
            str(location_id)
        )
    except (ValueError, TypeError):
        return None

    statement = select(InventoryLocation).where(
        InventoryLocation.id == parsed_location_id,
        InventoryLocation.retailer_id == retailer_id,
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_purchase_order_endpoint(
    request: PurchaseOrderCreateRequest,
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
            detail="Retailer not found for this user.",
        )

    supplier = get_supplier_by_supplier_id(
        db,
        request.supplier_id,
    )

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    location = get_location_for_retailer(
        db,
        request.location_id,
        retailer.id,
    )

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory location not found for this retailer.",
        )

    try:
        order = create_purchase_order(
            db=db,
            retailer=retailer,
            supplier=supplier,
            location=location,
            created_by_user=current_user,
            notes=request.notes,
            expected_delivery_date=(
                request.expected_delivery_date
            ),
        )

        return purchase_order_to_response(order)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{purchase_order_id}/items",
    response_model=PurchaseOrderItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_purchase_order_item_endpoint(
    purchase_order_id: str,
    request: PurchaseOrderItemCreateRequest,
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
            detail="Retailer not found for this user.",
        )

    order = get_purchase_order_by_reference(
        db,
        purchase_order_id,
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found.",
        )

    if order.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found.",
        )

    variant = get_variant_by_sku(
        db,
        request.sku,
    )

    if variant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found.",
        )

    try:
        item = add_purchase_order_item(
            db=db,
            purchase_order=order,
            product_variant=variant,
            ordered_quantity=request.ordered_quantity,
            unit_cost=request.unit_cost,
            tax_rate=request.tax_rate,
        )

        return purchase_order_item_to_response(item, order.purchase_order_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[PurchaseOrderResponse],
)
def list_purchase_orders_endpoint(
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
            detail="Retailer not found for this user.",
        )

    orders = get_purchase_orders_for_retailer(
        db,
        retailer.id,
    )

    return [
        purchase_order_to_response(order)
        for order in orders
    ]


@router.get(
    "/{purchase_order_id}/items",
    response_model=list[PurchaseOrderItemResponse],
)
def get_purchase_order_items_endpoint(
    purchase_order_id: str,
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
            detail="Purchase order not found.",
        )

    order = get_purchase_order_by_reference(
        db,
        purchase_order_id,
    )

    if order is None or order.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found.",
        )

    items = get_purchase_order_items(
        db,
        order.id,
    )

    return [
        purchase_order_item_to_response(item)
        for item in items
    ]


@router.post(
    "/{purchase_order_id}/items/{item_id}/receive",
    response_model=PurchaseOrderItemResponse,
)
def receive_purchase_order_item_endpoint(
    purchase_order_id: str,
    item_id: str,
    request: PurchaseOrderReceiveRequest,
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
            detail="Retailer not found for this user.",
        )

    order = get_purchase_order_by_reference(
        db,
        purchase_order_id,
    )

    if order is None or order.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found.",
        )

    try:
        parsed_item_id = uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid purchase order item ID.",
        )

    statement = select(PurchaseOrderItem).where(
        PurchaseOrderItem.id == parsed_item_id,
        PurchaseOrderItem.purchase_order_id == order.id,
    )

    item = db.execute(
        statement
    ).scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order item not found.",
        )

    location = get_location_for_retailer(
        db,
        str(order.location_id),
        retailer.id,
    )

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory location not found.",
        )

    variant_statement = select(
        __import__(
            "app.models.product_variant",
            fromlist=["ProductVariant"],
        ).ProductVariant
    ).where(
        __import__(
            "app.models.product_variant",
            fromlist=["ProductVariant"],
        ).ProductVariant.id
        == item.product_variant_id
    )

    product_variant = db.execute(
        variant_statement
    ).scalar_one_or_none()

    if product_variant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found.",
        )

    inventory_statement = select(InventoryItem).where(
        InventoryItem.retailer_id == retailer.id,
        InventoryItem.location_id == location.id,
        InventoryItem.product_variant_id
        == product_variant.id,
    )

    inventory_item = db.execute(
        inventory_statement
    ).scalar_one_or_none()

    if inventory_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found for this product and location.",
        )

    try:
        item = receive_purchase_order_item(
            db=db,
            purchase_order=order,
            purchase_order_item=item,
            retailer=retailer,
            location=location,
            product_variant=product_variant,
            inventory_item=inventory_item,
            received_quantity=request.received_quantity,
            performed_by_user_id=current_user.id,
        )

        return purchase_order_item_to_response(item, order.purchase_order_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.patch(
    "/{purchase_order_id}/status",
    response_model=PurchaseOrderResponse,
)
def update_purchase_order_status_endpoint(
    purchase_order_id: str,
    new_status: str,
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
            detail="Retailer not found for this user.",
        )

    order = get_purchase_order_by_reference(
        db,
        purchase_order_id,
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found.",
        )

    if order.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found.",
        )

    try:
        order = update_purchase_order_status(
            db=db,
            purchase_order=order,
            status=new_status,
        )

        return purchase_order_to_response(order)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/{purchase_order_id}",
    response_model=PurchaseOrderResponse,
)
def get_purchase_order_endpoint(
    purchase_order_id: str,
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
            detail="Purchase order not found.",
        )

    order = get_purchase_order_by_reference(
        db,
        purchase_order_id,
    )

    if order is None or order.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found.",
        )

    return purchase_order_to_response(order)