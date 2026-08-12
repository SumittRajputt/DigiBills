import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_variant import ProductVariant


def get_variant_by_id(
    db: Session,
    variant_id: uuid.UUID,
) -> Optional[ProductVariant]:
    statement = select(ProductVariant).where(
        ProductVariant.id == variant_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_variant_by_sku(
    db: Session,
    sku: str,
) -> Optional[ProductVariant]:
    statement = select(ProductVariant).where(
        ProductVariant.sku == sku
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_variant_by_barcode(
    db: Session,
    barcode: str,
) -> Optional[ProductVariant]:
    statement = select(ProductVariant).where(
        ProductVariant.barcode == barcode
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_product_by_code(
    db: Session,
    product_code: str,
) -> Optional[Product]:
    statement = select(Product).where(
        Product.product_code == product_code
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def create_product_variant(
    db: Session,
    product_code: str,
    sku: str,
    variant_name: str,
    selling_price: Decimal,
    barcode: Optional[str] = None,
    purchase_cost: Optional[Decimal] = None,
    tax_rate: Decimal = Decimal("0"),
    track_inventory: bool = True,
    requires_serial_number: bool = False,
) -> ProductVariant:

    product = get_product_by_code(
        db,
        product_code,
    )

    if product is None:
        raise ValueError(
            "Product not found."
        )

    existing_sku = get_variant_by_sku(
        db,
        sku,
    )

    if existing_sku:
        raise ValueError(
            "A variant with this SKU already exists."
        )

    if barcode:
        existing_barcode = get_variant_by_barcode(
            db,
            barcode,
        )

        if existing_barcode:
            raise ValueError(
                "A variant with this barcode already exists."
            )

    variant = ProductVariant(
        product_id=product.id,
        sku=sku,
        barcode=barcode,
        variant_name=variant_name,
        selling_price=selling_price,
        purchase_cost=purchase_cost,
        tax_rate=tax_rate,
        track_inventory=track_inventory,
        requires_serial_number=requires_serial_number,
        status="active",
    )

    db.add(variant)
    db.commit()
    db.refresh(variant)

    return variant