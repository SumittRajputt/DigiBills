from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.inventory_location import (
    InventoryLocationCreateRequest,
    InventoryLocationResponse,
)
from app.services.inventory_location_service import (
    create_inventory_location,
    get_all_inventory_locations,
)
from app.services.retailer_service import (
    get_retailer_by_owner,
)


router = APIRouter(
    prefix="/inventory-locations",
    tags=["Inventory Locations"],
)


def location_to_response(location):
    return InventoryLocationResponse(
        id=str(location.id),
        retailer_id=str(location.retailer_id),
        name=location.name,
        location_type=location.location_type,
        address=location.address,
        is_active=location.is_active,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )


@router.get(
    "",
    response_model=list[InventoryLocationResponse],
)
def list_inventory_locations(
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

    locations = get_all_inventory_locations(
        db,
        retailer.id,
    )

    return [
        location_to_response(location)
        for location in locations
    ]


@router.post(
    "",
    response_model=InventoryLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_location_endpoint(
    request: InventoryLocationCreateRequest,
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

    try:
        location = create_inventory_location(
            db=db,
            retailer=retailer,
            name=request.name,
            location_type=request.location_type,
            address=request.address,
        )

        return location_to_response(location)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )