import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.inventory_location import InventoryLocation
from app.models.user import User
from app.schemas.inventory import (
    InventoryItemCreateRequest,
    InventoryItemResponse,
)
from app.services.inventory_service import (
    check_reorder_status,
    create_inventory_item,
    get_inventory_item,
)
from app.services.product_variant_service import (
    get_variant_by_sku,
)
from app.services.retailer_service import (
    get_retailer_by_owner,
)


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)


def inventory_to_response(item):
    return InventoryItemResponse(
        id=str(item.id),
        retailer_id=str(item.retailer_id),
        location_id=str(item.location_id),
        product_variant_id=str(item.product_variant_id),
        quantity_on_hand=item.quantity_on_hand,
        quantity_reserved=item.quantity_reserved,
        quantity_available=item.quantity_available,
        reorder_level=item.reorder_level,
        reorder_quantity=item.reorder_quantity,
        average_cost=item.average_cost,
        last_stocked_at=item.last_stocked_at,
        updated_at=item.updated_at,
    )


def get_location_for_retailer(
    db: Session,
    location_id,
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
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_endpoint(
    request: InventoryItemCreateRequest,
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

    try:
        inventory_item = create_inventory_item(
            db=db,
            retailer=retailer,
            location=location,
            product_variant=variant,
            reorder_level=request.reorder_level,
            reorder_quantity=request.reorder_quantity,
            average_cost=request.average_cost,
        )

        return inventory_to_response(
            inventory_item
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


# IMPORTANT:
# Keep /{sku}/reorder-status BEFORE /{sku}

@router.get(
    "/{sku}/reorder-status",
)
def get_reorder_status_endpoint(
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

    variant = get_variant_by_sku(
        db,
        sku,
    )

    if variant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found.",
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

    item = get_inventory_item(
        db,
        retailer.id,
        location.id,
        variant.id,
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found.",
        )

    return check_reorder_status(item)


@router.get(
    "/{sku}",
    response_model=InventoryItemResponse,
)
def get_inventory_endpoint(
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

    variant = get_variant_by_sku(
        db,
        sku,
    )

    if variant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found.",
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

    item = get_inventory_item(
        db,
        retailer.id,
        location.id,
        variant.id,
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found.",
        )

    return inventory_to_response(item)