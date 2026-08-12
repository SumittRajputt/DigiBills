import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product_variant import ProductVariant
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.retailer import Retailer
from app.models.supplier import Supplier
from app.models.user import User
from app.services.stock_movement_service import (
    create_stock_movement,
)


def get_purchase_order_by_id(
    db: Session,
    purchase_order_id: uuid.UUID,
) -> Optional[PurchaseOrder]:
    statement = select(PurchaseOrder).where(
        PurchaseOrder.id == purchase_order_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_purchase_order_by_reference(
    db: Session,
    purchase_order_id: str,
) -> Optional[PurchaseOrder]:
    statement = select(PurchaseOrder).where(
        PurchaseOrder.purchase_order_id
        == purchase_order_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_purchase_orders_for_retailer(
    db: Session,
    retailer_id: uuid.UUID,
):
    statement = (
        select(PurchaseOrder)
        .where(
            PurchaseOrder.retailer_id
            == retailer_id
        )
        .order_by(
            PurchaseOrder.created_at.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_purchase_order_items(
    db: Session,
    purchase_order_id: uuid.UUID,
):
    statement = (
        select(PurchaseOrderItem)
        .where(
            PurchaseOrderItem.purchase_order_id
            == purchase_order_id
        )
        .order_by(
            PurchaseOrderItem.created_at.asc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def create_purchase_order(
    db: Session,
    retailer: Retailer,
    supplier: Supplier,
    location: InventoryLocation,
    created_by_user: User,
    notes: Optional[str] = None,
    expected_delivery_date: Optional[datetime] = None,
) -> PurchaseOrder:

    if retailer.status != "active":
        raise ValueError(
            "Retailer is not active."
        )

    if supplier.retailer_id != retailer.id:
        raise ValueError(
            "Supplier does not belong to this retailer."
        )

    if not supplier.is_active:
        raise ValueError(
            "Supplier is not active."
        )

    if location.retailer_id != retailer.id:
        raise ValueError(
            "Inventory location does not belong to this retailer."
        )

    if not location.is_active:
        raise ValueError(
            "Inventory location is not active."
        )

    purchase_order = PurchaseOrder(
        purchase_order_id=(
            f"PO-{uuid.uuid4().hex[:10].upper()}"
        ),
        retailer_id=retailer.id,
        supplier_id=supplier.id,
        location_id=location.id,
        created_by_user_id=created_by_user.id,
        status="draft",
        subtotal=Decimal("0"),
        tax_amount=Decimal("0"),
        total_amount=Decimal("0"),
        expected_delivery_date=expected_delivery_date,
        notes=notes,
    )

    db.add(purchase_order)
    db.commit()
    db.refresh(purchase_order)

    return purchase_order


def add_purchase_order_item(
    db: Session,
    purchase_order: PurchaseOrder,
    product_variant: ProductVariant,
    ordered_quantity: int,
    unit_cost: Decimal,
    tax_rate: Decimal = Decimal("0"),
) -> PurchaseOrderItem:

    if purchase_order.status != "draft":
        raise ValueError(
            "Items can only be added to a draft purchase order."
        )

    if ordered_quantity <= 0:
        raise ValueError(
            "Ordered quantity must be greater than zero."
        )

    if unit_cost < 0:
        raise ValueError(
            "Unit cost cannot be negative."
        )

    if tax_rate < 0:
        raise ValueError(
            "Tax rate cannot be negative."
        )

    subtotal = (
        Decimal(ordered_quantity)
        * unit_cost
    )

    tax_amount = (
        subtotal
        * tax_rate
        / Decimal("100")
    )

    line_total = (
        subtotal
        + tax_amount
    )

    item = PurchaseOrderItem(
        purchase_order_id=purchase_order.id,
        product_variant_id=product_variant.id,
        product_name=product_variant.variant_name,
        sku=product_variant.sku,
        ordered_quantity=ordered_quantity,
        received_quantity=0,
        unit_cost=unit_cost,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        line_total=line_total,
    )

    db.add(item)

    purchase_order.subtotal = (
        purchase_order.subtotal
        + subtotal
    )

    purchase_order.tax_amount = (
        purchase_order.tax_amount
        + tax_amount
    )

    purchase_order.total_amount = (
        purchase_order.subtotal
        + purchase_order.tax_amount
    )

    db.commit()
    db.refresh(item)
    db.refresh(purchase_order)

    return item


def update_purchase_order_status(
    db: Session,
    purchase_order: PurchaseOrder,
    status: str,
) -> PurchaseOrder:

    allowed_statuses = {
        "draft",
        "ordered",
        "partially_received",
        "received",
        "cancelled",
    }

    status = status.lower().strip()

    if status not in allowed_statuses:
        raise ValueError(
            "Invalid purchase order status."
        )

    if (
        status
        in {
            "ordered",
            "partially_received",
            "received",
        }
        and purchase_order.status == "cancelled"
    ):
        raise ValueError(
            "Cancelled purchase orders cannot be reopened."
        )

    purchase_order.status = status

    db.commit()
    db.refresh(purchase_order)

    return purchase_order


def receive_purchase_order_item(
    db: Session,
    purchase_order: PurchaseOrder,
    purchase_order_item: PurchaseOrderItem,
    retailer: Retailer,
    location: InventoryLocation,
    product_variant: ProductVariant,
    inventory_item: InventoryItem,
    received_quantity: int,
    performed_by_user_id: Optional[uuid.UUID] = None,
) -> PurchaseOrderItem:

    if purchase_order.retailer_id != retailer.id:
        raise ValueError(
            "Purchase order does not belong to this retailer."
        )

    if purchase_order_item.purchase_order_id != purchase_order.id:
        raise ValueError(
            "Purchase order item does not belong to this purchase order."
        )

    if location.id != purchase_order.location_id:
        raise ValueError(
            "Inventory location does not match the purchase order."
        )

    if product_variant.id != purchase_order_item.product_variant_id:
        raise ValueError(
            "Product variant does not match the purchase order item."
        )

    if purchase_order.status not in {
        "ordered",
        "partially_received",
    }:
        raise ValueError(
            "Purchase order is not available for receiving."
        )

    if received_quantity <= 0:
        raise ValueError(
            "Received quantity must be greater than zero."
        )

    remaining_quantity = (
        purchase_order_item.ordered_quantity
        - purchase_order_item.received_quantity
    )

    if received_quantity > remaining_quantity:
        raise ValueError(
            "Received quantity cannot exceed the remaining ordered quantity."
        )

    try:
        create_stock_movement(
            db=db,
            retailer=retailer,
            location=location,
            product_variant=product_variant,
            inventory_item=inventory_item,
            movement_type="purchase",
            quantity=received_quantity,
            performed_by_user_id=performed_by_user_id,
            unit_cost=purchase_order_item.unit_cost,
            reference_type="purchase_order",
            reference_id=purchase_order.id,
            notes=(
                f"Received against purchase order "
                f"{purchase_order.purchase_order_id}"
            ),
            commit=False,
        )

        purchase_order_item.received_quantity += (
            received_quantity
        )

        if (
            purchase_order_item.received_quantity
            >= purchase_order_item.ordered_quantity
        ):
            purchase_order_item.received_at = (
                datetime.now(timezone.utc)
            )

        all_items = get_purchase_order_items(
            db,
            purchase_order.id,
        )

        all_received = all(
            item.received_quantity
            >= item.ordered_quantity
            for item in all_items
        )

        any_received = any(
            item.received_quantity > 0
            for item in all_items
        )

        if all_received:
            purchase_order.status = "received"
            purchase_order.received_at = (
                datetime.now(timezone.utc)
            )
        elif any_received:
            purchase_order.status = (
                "partially_received"
            )

        db.commit()

        db.refresh(purchase_order_item)
        db.refresh(purchase_order)
        db.refresh(inventory_item)

        return purchase_order_item

    except Exception:
        db.rollback()
        raise