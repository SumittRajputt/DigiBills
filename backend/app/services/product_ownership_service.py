import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product_ownership import ProductOwnership
from app.models.product_unit import ProductUnit
from app.models.product_variant import ProductVariant


def get_product_ownership(
    db: Session,
    ownership_id: str,
) -> Optional[ProductOwnership]:
    try:
        parsed_id = uuid.UUID(ownership_id)
    except ValueError:
        return None

    statement = select(ProductOwnership).where(
        ProductOwnership.id == parsed_id
    )

    return db.execute(statement).scalar_one_or_none()


def get_customer_by_id(
    db: Session,
    customer_id: str,
) -> Optional[Customer]:
    try:
        parsed_id = uuid.UUID(customer_id)
    except ValueError:
        return None

    statement = select(Customer).where(
        Customer.id == parsed_id
    )

    return db.execute(statement).scalar_one_or_none()


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

    return db.execute(statement).scalar_one_or_none()


def get_product_unit_by_id(
    db: Session,
    product_unit_id: str,
) -> Optional[ProductUnit]:
    try:
        parsed_id = uuid.UUID(product_unit_id)
    except ValueError:
        return None

    statement = select(ProductUnit).where(
        ProductUnit.id == parsed_id
    )

    return db.execute(statement).scalar_one_or_none()


def get_ownership_by_product_unit(
    db: Session,
    product_unit_id: str,
) -> Optional[ProductOwnership]:
    try:
        parsed_id = uuid.UUID(product_unit_id)
    except ValueError:
        return None

    statement = select(ProductOwnership).where(
        ProductOwnership.product_unit_id == parsed_id,
        ProductOwnership.ownership_status == "active",
    )

    return db.execute(statement).scalar_one_or_none()


def get_ownership_by_serial_number(
    db: Session,
    serial_number: str,
) -> Optional[ProductOwnership]:
    statement = (
        select(ProductOwnership)
        .join(
            ProductUnit,
            ProductUnit.id == ProductOwnership.product_unit_id,
        )
        .where(
            ProductUnit.serial_number == serial_number,
            ProductOwnership.ownership_status == "active",
        )
    )

    return db.execute(statement).scalar_one_or_none()


def assign_product_ownership(
    db: Session,
    invoice: Invoice,
    invoice_item: InvoiceItem,
    customer: Customer,
    product_unit: ProductUnit,
    source: str = "invoice",
) -> ProductOwnership:

    if invoice.customer_id != customer.id:
        raise ValueError(
            "Customer does not belong to this invoice."
        )

    if invoice_item.invoice_id != invoice.id:
        raise ValueError(
            "Invoice item does not belong to this invoice."
        )

    if invoice.status != "active":
        raise ValueError(
            "Only active invoices can create ownership."
        )

    product_variant = get_product_variant_by_id(
        db,
        str(invoice_item.product_variant_id),
    )

    if product_variant is None:
        raise ValueError(
            "Product variant not found."
        )

    if product_unit.product_variant_id != product_variant.id:
        raise ValueError(
            "Product unit does not belong to the invoice item product variant."
        )

    if not product_variant.track_inventory:
        raise ValueError(
            "Ownership cannot be created for a product "
            "with inventory tracking disabled."
        )

    if not product_variant.requires_serial_number:
        raise ValueError(
            "Ownership requires a product variant "
            "that requires serial number tracking."
        )

    if product_unit.status != "in_stock":
        raise ValueError(
            f"Product unit '{product_unit.serial_number}' "
            "is not available for ownership assignment."
        )

    existing_ownership = db.execute(
        select(ProductOwnership).where(
            ProductOwnership.product_unit_id == product_unit.id,
            ProductOwnership.ownership_status == "active",
        )
    ).scalar_one_or_none()

    if existing_ownership is not None:
        raise ValueError(
            f"Product unit '{product_unit.serial_number}' "
            "already has an active owner."
        )

    ownership = ProductOwnership(
        product_unit_id=product_unit.id,
        customer_id=customer.id,
        ownership_status="active",
        acquired_at=datetime.now(timezone.utc),
        released_at=None,
        source=source,
    )

    db.add(ownership)

    product_unit.status = "sold"

    return ownership


def create_product_ownership(
    db: Session,
    invoice: Invoice,
    invoice_item: InvoiceItem,
    customer: Customer,
    product_unit: ProductUnit,
    source: str = "invoice",
) -> ProductOwnership:

    ownership = assign_product_ownership(
        db=db,
        invoice=invoice,
        invoice_item=invoice_item,
        customer=customer,
        product_unit=product_unit,
        source=source,
    )

    db.commit()
    db.refresh(ownership)

    return ownership
