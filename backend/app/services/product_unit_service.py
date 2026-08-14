import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product_unit import ProductUnit
from app.models.product_variant import ProductVariant


def get_product_unit_by_id(
    db: Session,
    product_unit_id: uuid.UUID,
) -> Optional[ProductUnit]:
    statement = select(ProductUnit).where(
        ProductUnit.id == product_unit_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_product_unit_by_serial_number(
    db: Session,
    serial_number: str,
) -> Optional[ProductUnit]:
    statement = select(ProductUnit).where(
        ProductUnit.serial_number == serial_number
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_product_variant_by_id(
    db: Session,
    product_variant_id: str,
) -> Optional[ProductVariant]:
    try:
        parsed_id = uuid.UUID(product_variant_id)
    except ValueError:
        return None

    statement = select(ProductVariant).where(
        ProductVariant.id == parsed_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def create_product_unit(
    db: Session,
    product_variant_id: str,
    serial_number: str,
    status: str = "in_stock",
) -> ProductUnit:
    serial_number = serial_number.strip()

    if not serial_number:
        raise ValueError(
            "Serial number cannot be empty."
        )

    product_variant = get_product_variant_by_id(
        db,
        product_variant_id,
    )

    if product_variant is None:
        raise ValueError(
            "Product variant not found."
        )

    if product_variant.status != "active":
        raise ValueError(
            "Product variant is not active."
        )

    if not product_variant.track_inventory:
        raise ValueError(
            "Product variant does not use inventory tracking."
        )

    if not product_variant.requires_serial_number:
        raise ValueError(
            "Product variant does not require serial number tracking."
        )

    existing_unit = get_product_unit_by_serial_number(
        db,
        serial_number,
    )

    if existing_unit is not None:
        raise ValueError(
            "A product unit with this serial number already exists."
        )

    valid_statuses = {
        "in_stock",
        "sold",
        "returned",
        "damaged",
        "inactive",
    }

    status = status.lower().strip()

    if status not in valid_statuses:
        raise ValueError(
            "Invalid product unit status."
        )

    product_unit = ProductUnit(
        product_variant_id=product_variant.id,
        serial_number=serial_number,
        status=status,
    )

    db.add(product_unit)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(product_unit)

    return product_unit
