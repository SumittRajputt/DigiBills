import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.customer_digibill import CustomerDigiBill
from app.models.product_ownership import ProductOwnership
from app.models.product_unit import ProductUnit


def normalize_serial_number(serial_number: str) -> str:
    return " ".join(serial_number.strip().split()).upper()


def get_customer_digibill(
    db: Session,
    digibill_id: str,
) -> Optional[CustomerDigiBill]:
    return db.execute(
        select(CustomerDigiBill).where(
            CustomerDigiBill.digibill_id == digibill_id.strip()
        )
    ).scalar_one_or_none()


def get_uploaded_product(
    digibill: CustomerDigiBill,
) -> Optional[dict]:
    products = digibill.products or []

    if not products:
        return None

    if len(products) != 1:
        raise ValueError(
            "Serial verification currently requires a DigiBill "
            "with exactly one product."
        )

    product = products[0]

    if not isinstance(product, dict):
        raise ValueError(
            "The DigiBill product data is invalid."
        )

    return product


def verify_customer_digibill_serial(
    db: Session,
    digibill: CustomerDigiBill,
    customer: Customer,
    serial_number: str,
) -> dict:
    if digibill.customer_id != customer.id:
        raise ValueError(
            "This DigiBill does not belong to you."
        )

    if digibill.status != "confirmed":
        raise ValueError(
            "Only confirmed DigiBills can be serial verified."
        )

    normalized_serial = normalize_serial_number(serial_number)

    if not normalized_serial:
        raise ValueError(
            "Serial number is required."
        )

    product = get_uploaded_product(digibill)

    if product is None:
        raise ValueError(
            "No product was found on this DigiBill."
        )

    normalized_brand = " ".join(
        str(product.get("brand") or "").strip().split()
    ).upper()

    normalized_model = " ".join(
        str(product.get("model_number") or "").strip().split()
    ).upper()

    if not normalized_brand or not normalized_model:
        raise ValueError(
            "Product brand and model number are required before "
            "serial verification."
        )

    existing_digibills = db.execute(
        select(CustomerDigiBill).where(
            CustomerDigiBill.verified_serial_number
            == normalized_serial,
            CustomerDigiBill.digibill_id
            != digibill.digibill_id,
            CustomerDigiBill.status == "confirmed",
        )
    ).scalars().all()

    for existing_digibill in existing_digibills:
        existing_product = get_uploaded_product(existing_digibill)

        if existing_product is None:
            continue

        existing_brand = " ".join(
            str(existing_product.get("brand") or "").strip().split()
        ).upper()

        existing_model = " ".join(
            str(existing_product.get("model_number") or "").strip().split()
        ).upper()

        if (
            existing_brand == normalized_brand
            and existing_model == normalized_model
        ):
            raise ValueError(
                "This serial number is already associated with "
                "another DigiBill for the same product and cannot "
                "be transferred."
            )

    registered_unit = db.execute(
        select(ProductUnit).where(
            ProductUnit.serial_number == normalized_serial
        )
    ).scalar_one_or_none()

    if registered_unit is not None:
        active_ownership = db.execute(
            select(ProductOwnership).where(
                ProductOwnership.product_unit_id == registered_unit.id,
                ProductOwnership.ownership_status == "active",
            )
        ).scalar_one_or_none()

        if (
            active_ownership is not None
            and active_ownership.customer_id != customer.id
        ):
            raise ValueError(
                "This serial number is already associated with "
                "another customer's registered product."
            )

    now = datetime.now(timezone.utc)

    digibill.verified_serial_number = normalized_serial
    digibill.serial_verification_status = "verified"
    digibill.serial_verified_at = now

    db.commit()
    db.refresh(digibill)

    return {
        "verified": True,
        "status": "verified",
        "digibill_id": digibill.digibill_id,
        "serial_number": normalized_serial,
        "message": "Serial number verified successfully.",
        "product": {
            "product_name": product.get("product_name"),
            "brand": product.get("brand"),
            "model_number": product.get("model_number"),
        },
    }
