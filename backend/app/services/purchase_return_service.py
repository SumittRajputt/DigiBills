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
from app.models.purchase_return import PurchaseReturn
from app.models.purchase_return_item import PurchaseReturnItem
from app.models.retailer import Retailer
from app.models.supplier import Supplier
from app.services.stock_movement_service import (
    create_stock_movement,
)


def get_purchase_return_by_reference(
    db: Session,
    return_id: str,
) -> Optional[PurchaseReturn]:
    statement = select(PurchaseReturn).where(
        PurchaseReturn.return_id == return_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_purchase_return_by_id(
    db: Session,
    return_uuid: uuid.UUID,
) -> Optional[PurchaseReturn]:
    statement = select(PurchaseReturn).where(
        PurchaseReturn.id == return_uuid
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_purchase_return_items(
    db: Session,
    purchase_return_id: uuid.UUID,
):
    statement = (
        select(PurchaseReturnItem)
        .where(
            PurchaseReturnItem.purchase_return_id
            == purchase_return_id
        )
        .order_by(
            PurchaseReturnItem.created_at.asc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_purchase_returns_for_retailer(
    db: Session,
    retailer_id: uuid.UUID,
):
    statement = (
        select(PurchaseReturn)
        .where(
            PurchaseReturn.retailer_id
            == retailer_id
        )
        .order_by(
            PurchaseReturn.created_at.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def create_purchase_return(
    db: Session,
    retailer: Retailer,
    purchase_order: PurchaseOrder,
    supplier: Supplier,
    location: InventoryLocation,
    reason: Optional[str] = None,
    notes: Optional[str] = None,
) -> PurchaseReturn:

    if purchase_order.retailer_id != retailer.id:
        raise ValueError(
            "Purchase order does not belong to this retailer."
        )

    if purchase_order.supplier_id != supplier.id:
        raise ValueError(
            "Supplier does not belong to this purchase order."
        )

    if purchase_order.location_id != location.id:
        raise ValueError(
            "Inventory location does not match the purchase order."
        )

    if purchase_order.status not in {
        "partially_received",
        "received",
    }:
        raise ValueError(
            "Purchase order has no received stock available for return."
        )

    purchase_return = PurchaseReturn(
        return_id=(
            f"PR-{uuid.uuid4().hex[:10].upper()}"
        ),
        purchase_order_id=purchase_order.id,
        retailer_id=retailer.id,
        supplier_id=supplier.id,
        location_id=location.id,
        return_amount=Decimal("0"),
        status="requested",
        reason=reason,
        notes=notes,
    )

    db.add(purchase_return)
    db.commit()
    db.refresh(purchase_return)

    return purchase_return


def add_purchase_return_item(
    db: Session,
    purchase_return: PurchaseReturn,
    purchase_order_item: PurchaseOrderItem,
    product_variant: ProductVariant,
    quantity: int,
    reason: Optional[str] = None,
    condition: str = "good",
) -> PurchaseReturnItem:

    if purchase_return.status != "requested":
        raise ValueError(
            "Items can only be added to a requested purchase return."
        )

    if quantity <= 0:
        raise ValueError(
            "Return quantity must be greater than zero."
        )

    condition = condition.lower().strip()

    allowed_conditions = {
        "good",
        "damaged",
        "defective",
        "expired",
    }

    if condition not in allowed_conditions:
        raise ValueError(
            "Invalid return condition."
        )

    if (
        purchase_order_item.purchase_order_id
        != purchase_return.purchase_order_id
    ):
        raise ValueError(
            "Purchase order item does not belong to this purchase order."
        )

    if (
        purchase_order_item.product_variant_id
        != product_variant.id
    ):
        raise ValueError(
            "Product variant does not match the purchase order item."
        )

    if quantity > purchase_order_item.received_quantity:
        raise ValueError(
            "Return quantity cannot exceed received quantity."
        )

    existing_statement = select(
        PurchaseReturnItem
    ).where(
        PurchaseReturnItem.purchase_return_id
        == purchase_return.id,
        PurchaseReturnItem.purchase_order_item_id
        == purchase_order_item.id,
    )

    existing_item = db.execute(
        existing_statement
    ).scalar_one_or_none()

    already_returned = (
        existing_item.quantity
        if existing_item
        else 0
    )

    if (
        already_returned + quantity
        > purchase_order_item.received_quantity
    ):
        raise ValueError(
            "Total returned quantity cannot exceed received quantity."
        )

    unit_cost = (
        purchase_order_item.unit_cost
    )

    return_amount = (
        Decimal(quantity) * unit_cost
    )

    if existing_item:
        existing_item.quantity += quantity
        existing_item.return_amount += return_amount

        if reason is not None:
            existing_item.reason = reason

        existing_item.condition = condition

        item = existing_item

    else:
        item = PurchaseReturnItem(
            purchase_return_id=purchase_return.id,
            purchase_order_item_id=purchase_order_item.id,
            product_variant_id=product_variant.id,
            product_name=purchase_order_item.product_name,
            sku=purchase_order_item.sku,
            quantity=quantity,
            unit_cost=unit_cost,
            return_amount=return_amount,
            reason=reason,
            condition=condition,
        )

        db.add(item)

    purchase_return.return_amount += return_amount

    db.commit()
    db.refresh(item)
    db.refresh(purchase_return)

    return item


def process_purchase_return(
    db: Session,
    purchase_return: PurchaseReturn,
    retailer: Retailer,
    processed_by_user_id: Optional[uuid.UUID] = None,
) -> PurchaseReturn:

    if purchase_return.retailer_id != retailer.id:
        raise ValueError(
            "Purchase return does not belong to this retailer."
        )

    if purchase_return.status != "requested":
        raise ValueError(
            "Only requested purchase returns can be processed."
        )

    items = get_purchase_return_items(
        db,
        purchase_return.id,
    )

    if not items:
        raise ValueError(
            "Purchase return must contain at least one item."
        )

    try:
        for return_item in items:

            inventory_statement = select(
                InventoryItem
            ).where(
                InventoryItem.retailer_id
                == retailer.id,
                InventoryItem.location_id
                == purchase_return.location_id,
                InventoryItem.product_variant_id
                == return_item.product_variant_id,
            )

            inventory_item = db.execute(
                inventory_statement
            ).scalar_one_or_none()

            if inventory_item is None:
                raise ValueError(
                    f"Inventory item not found for SKU "
                    f"{return_item.sku}."
                )

            available_quantity = (
                inventory_item.quantity_on_hand
                - inventory_item.quantity_reserved
            )

            if return_item.quantity > available_quantity:
                raise ValueError(
                    f"Insufficient available stock for "
                    f"SKU {return_item.sku}."
                )

            variant_statement = select(
                ProductVariant
            ).where(
                ProductVariant.id
                == return_item.product_variant_id
            )

            product_variant = db.execute(
                variant_statement
            ).scalar_one_or_none()

            if product_variant is None:
                raise ValueError(
                    f"Product variant not found for "
                    f"SKU {return_item.sku}."
                )

            location_statement = select(
                InventoryLocation
            ).where(
                InventoryLocation.id
                == purchase_return.location_id,
                InventoryLocation.retailer_id
                == retailer.id,
            )

            location = db.execute(
                location_statement
            ).scalar_one_or_none()

            if location is None:
                raise ValueError(
                    "Inventory location not found."
                )

            create_stock_movement(
                db=db,
                retailer=retailer,
                location=location,
                product_variant=product_variant,
                inventory_item=inventory_item,
                movement_type="return_out",
                quantity=return_item.quantity,
                performed_by_user_id=processed_by_user_id,
                unit_cost=return_item.unit_cost,
                reference_type="purchase_return",
                reference_id=purchase_return.id,
                notes=(
                    f"Returned to supplier "
                    f"against {purchase_return.return_id}"
                ),
                commit=False,
            )

        purchase_return.status = "processed"

        purchase_return.processed_by_user_id = (
            processed_by_user_id
        )

        purchase_return.processed_at = (
            datetime.now(timezone.utc)
        )

        db.commit()
        db.refresh(purchase_return)

        return purchase_return

    except Exception:
        db.rollback()
        raise

def get_all_purchase_returns(
    db: Session,
) -> list[PurchaseReturn]:
    statement = (
        select(PurchaseReturn)
        .order_by(
            PurchaseReturn.created_at.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_all_purchase_returns(
    db: Session,
) -> list[PurchaseReturn]:
    statement = (
        select(PurchaseReturn)
        .order_by(
            PurchaseReturn.created_at.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )
