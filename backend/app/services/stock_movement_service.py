import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.stock_movement import StockMovement


def create_stock_movement(
    db: Session,
    retailer: Retailer,
    location: InventoryLocation,
    product_variant: ProductVariant,
    inventory_item: InventoryItem,
    movement_type: str,
    quantity: int,
    performed_by_user_id: Optional[uuid.UUID] = None,
    unit_cost: Optional[Decimal] = None,
    reference_type: Optional[str] = None,
    reference_id: Optional[uuid.UUID] = None,
    notes: Optional[str] = None,
    commit: bool = True,
) -> StockMovement:

    if quantity <= 0:
        raise ValueError(
            "Stock movement quantity must be greater than zero."
        )

    if location.retailer_id != retailer.id:
        raise ValueError(
            "Inventory location does not belong to this retailer."
        )

    if inventory_item.retailer_id != retailer.id:
        raise ValueError(
            "Inventory item does not belong to this retailer."
        )

    if inventory_item.location_id != location.id:
        raise ValueError(
            "Inventory item does not belong to this location."
        )

    if inventory_item.product_variant_id != product_variant.id:
        raise ValueError(
            "Inventory item does not belong to this product variant."
        )

    movement_type = movement_type.lower().strip()

    incoming_types = {
        "purchase",
        "opening_stock",
        "stock_in",
        "return_in",
        "adjustment_in",
    }

    outgoing_types = {
        "sale",
        "stock_out",
        "return_out",
        "adjustment_out",
    }

    if movement_type not in (
        incoming_types | outgoing_types
    ):
        raise ValueError(
            "Invalid stock movement type."
        )

    if movement_type in outgoing_types:
        available_quantity = (
            inventory_item.quantity_on_hand
            - inventory_item.quantity_reserved
        )

        if quantity > available_quantity:
            raise ValueError(
                "Insufficient available stock."
            )

        inventory_item.quantity_on_hand -= quantity

    else:
        previous_quantity = (
            inventory_item.quantity_on_hand
        )

        inventory_item.quantity_on_hand += quantity

        inventory_item.last_stocked_at = (
            datetime.now(timezone.utc)
        )

        if unit_cost is not None:
            if unit_cost < 0:
                raise ValueError(
                    "Unit cost cannot be negative."
                )

            previous_average_cost = (
                inventory_item.average_cost
                or Decimal("0")
            )

            total_previous_cost = (
                Decimal(previous_quantity)
                * previous_average_cost
            )

            total_new_cost = (
                Decimal(quantity) * unit_cost
            )

            total_quantity = (
                previous_quantity + quantity
            )

            if total_quantity > 0:
                inventory_item.average_cost = (
                    total_previous_cost
                    + total_new_cost
                ) / Decimal(total_quantity)

    if (
        movement_type in outgoing_types
        and unit_cost is not None
        and unit_cost < 0
    ):
        raise ValueError(
            "Unit cost cannot be negative."
        )

    movement = StockMovement(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=product_variant.id,
        movement_type=movement_type,
        quantity=quantity,
        unit_cost=unit_cost,
        reference_type=reference_type,
        reference_id=reference_id,
        performed_by_user_id=performed_by_user_id,
        notes=notes,
    )

    db.add(movement)

    if commit:
        db.commit()
        db.refresh(movement)
        db.refresh(inventory_item)

    else:
        db.flush()

    return movement


def get_stock_movements_for_inventory(
    db: Session,
    retailer_id: uuid.UUID,
    location_id: uuid.UUID,
    product_variant_id: uuid.UUID,
):
    statement = (
        select(StockMovement)
        .where(
            StockMovement.retailer_id == retailer_id,
            StockMovement.location_id == location_id,
            StockMovement.product_variant_id
            == product_variant_id,
        )
        .order_by(
            StockMovement.created_at.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )