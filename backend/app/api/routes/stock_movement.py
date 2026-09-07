import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.inventory_location import InventoryLocation
from app.models.inventory_item import InventoryItem
from app.models.user import User
from app.schemas.stock_movement import (
    StockMovementCreateRequest,
    StockMovementResponse,
)
from app.services.inventory_service import (
    create_inventory_item,
    get_inventory_item,
)
from app.services.product_variant_service import get_variant_by_sku
from app.services.retailer_service import get_retailer_by_owner
from app.services.stock_movement_service import (
    create_stock_movement,
    get_stock_movements_for_inventory,
)


router = APIRouter(
    prefix="/stock-movements",
    tags=["Stock Movements"],
)


def get_location_for_retailer(
    db: Session,
    location_id: str,
    retailer_id,
):
    try:
        parsed_location_id = uuid.UUID(location_id)
    except ValueError:
        return None

    statement = select(InventoryLocation).where(
        InventoryLocation.id == parsed_location_id,
        InventoryLocation.retailer_id == retailer_id,
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def movement_to_response(movement):
    return StockMovementResponse(
        id=str(movement.id),
        retailer_id=str(movement.retailer_id),
        location_id=str(movement.location_id),
        product_variant_id=str(movement.product_variant_id),
        movement_type=movement.movement_type,
        quantity=movement.quantity,
        unit_cost=movement.unit_cost,
        reference_type=movement.reference_type,
        reference_id=(
            str(movement.reference_id)
            if movement.reference_id
            else None
        ),
        performed_by_user_id=(
            str(movement.performed_by_user_id)
            if movement.performed_by_user_id
            else None
        ),
        notes=movement.notes,
        created_at=movement.created_at,
    )


@router.post(
    "",
    response_model=StockMovementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_stock_movement_endpoint(
    request: StockMovementCreateRequest,
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

    if retailer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Retailer is not active.",
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

    variant = get_variant_by_sku(
        db,
        request.sku,
    )

    if variant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found.",
        )

    inventory_item = get_inventory_item(
        db,
        retailer.id,
        location.id,
        variant.id,
    )

    # Automatically create the inventory record when stock is
    # being added for a product at this location for the first time.
    if inventory_item is None:
        try:
            inventory_item = create_inventory_item(
                db=db,
                retailer=retailer,
                location=location,
                product_variant=variant,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            )

    reference_id = None

    if request.reference_id:
        try:
            reference_id = uuid.UUID(
                request.reference_id
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reference ID.",
            )

    try:
        movement = create_stock_movement(
            db=db,
            retailer=retailer,
            location=location,
            product_variant=variant,
            inventory_item=inventory_item,
            movement_type=request.movement_type,
            quantity=request.quantity,
            performed_by_user_id=current_user.id,
            unit_cost=request.unit_cost,
            reference_type=request.reference_type,
            reference_id=reference_id,
            notes=request.notes,
        )

        return movement_to_response(movement)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/{sku}",
    response_model=list[StockMovementResponse],
)
def get_stock_movements_endpoint(
    sku: str,
    location_id: str,
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

    location = get_location_for_retailer(
        db,
        location_id,
        retailer.id,
    )

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory location not found for this retailer.",
        )

    variant = get_variant_by_sku(
        db,
        sku,
    )

    if variant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found.",
        )

    movements = get_stock_movements_for_inventory(
        db,
        retailer.id,
        location.id,
        variant.id,
    )

    return [
        movement_to_response(movement)
        for movement in movements
    ]