import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer


def get_inventory_item(
    db: Session,
    retailer_id: uuid.UUID,
    location_id: uuid.UUID,
    product_variant_id: uuid.UUID,
) -> Optional[InventoryItem]:
    statement = select(InventoryItem).where(
        InventoryItem.retailer_id == retailer_id,
        InventoryItem.location_id == location_id,
        InventoryItem.product_variant_id == product_variant_id,
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def create_inventory_item(
    db: Session,
    retailer: Retailer,
    location: InventoryLocation,
    product_variant: ProductVariant,
    reorder_level: int = 0,
    reorder_quantity: int = 0,
    average_cost: Decimal = Decimal("0"),
) -> InventoryItem:

    if location.retailer_id != retailer.id:
        raise ValueError(
            "Inventory location does not belong to this retailer."
        )

    if not location.is_active:
        raise ValueError(
            "Inventory location is not active."
        )

    existing_item = get_inventory_item(
        db,
        retailer.id,
        location.id,
        product_variant.id,
    )

    if existing_item:
        raise ValueError(
            "Inventory already exists for this product variant at this location."
        )

    if reorder_level < 0:
        raise ValueError(
            "Reorder level cannot be negative."
        )

    if reorder_quantity < 0:
        raise ValueError(
            "Reorder quantity cannot be negative."
        )

    if average_cost < 0:
        raise ValueError(
            "Average cost cannot be negative."
        )

    inventory_item = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=product_variant.id,
        quantity_on_hand=0,
        quantity_reserved=0,
        reorder_level=reorder_level,
        reorder_quantity=reorder_quantity,
        average_cost=average_cost,
        last_stocked_at=None,
    )

    db.add(inventory_item)
    db.commit()
    db.refresh(inventory_item)

    return inventory_item


def check_reorder_status(
    inventory_item: InventoryItem,
) -> dict:
    quantity_available = inventory_item.quantity_available

    needs_reorder = (
        quantity_available <= inventory_item.reorder_level
    )

    return {
        "inventory_id": str(inventory_item.id),
        "quantity_available": quantity_available,
        "reorder_level": inventory_item.reorder_level,
        "reorder_quantity": inventory_item.reorder_quantity,
        "needs_reorder": needs_reorder,
    }