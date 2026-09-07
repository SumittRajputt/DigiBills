import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory_location import InventoryLocation
from app.models.retailer import Retailer


def get_location_by_id(
    db: Session,
    location_id: uuid.UUID,
) -> Optional[InventoryLocation]:
    statement = select(InventoryLocation).where(
        InventoryLocation.id == location_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_location_by_name(
    db: Session,
    retailer_id: uuid.UUID,
    name: str,
) -> Optional[InventoryLocation]:
    statement = select(InventoryLocation).where(
        InventoryLocation.retailer_id == retailer_id,
        InventoryLocation.name == name,
    )

    return db.execute(
        statement
    ).scalar_one_or_none()



def get_all_inventory_locations(
    db: Session,
    retailer_id: uuid.UUID,
) -> list[InventoryLocation]:
    statement = (
        select(InventoryLocation)
        .where(
            InventoryLocation.retailer_id == retailer_id,
        )
        .order_by(
            InventoryLocation.created_at.desc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )

def create_inventory_location(
    db: Session,
    retailer: Retailer,
    name: str,
    location_type: str,
    address: Optional[str] = None,
) -> InventoryLocation:

    existing_location = get_location_by_name(
        db,
        retailer.id,
        name,
    )

    if existing_location:
        raise ValueError(
            "An inventory location with this name already exists."
        )

    location = InventoryLocation(
        retailer_id=retailer.id,
        name=name,
        location_type=location_type,
        address=address,
        is_active=True,
    )

    db.add(location)
    db.commit()
    db.refresh(location)

    return location