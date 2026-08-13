import uuid
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.warranty import Warranty


def generate_warranty_id() -> str:
    return f"WAR-{uuid.uuid4().hex[:10].upper()}"


def get_warranty_by_reference(
    db: Session,
    warranty_reference: str,
) -> Optional[Warranty]:
    statement = select(Warranty).where(
        Warranty.warranty_id == warranty_reference
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_warranty_by_id(
    db: Session,
    warranty_id: uuid.UUID,
) -> Optional[Warranty]:
    statement = select(Warranty).where(
        Warranty.id == warranty_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_invoice_by_reference(
    db: Session,
    invoice_reference: str,
) -> Optional[Invoice]:
    statement = select(Invoice).where(
        Invoice.invoice_id == invoice_reference
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_customer_by_uuid(
    db: Session,
    customer_id: uuid.UUID,
) -> Optional[Customer]:
    statement = select(Customer).where(
        Customer.id == customer_id
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


def create_warranty(
    db: Session,
    retailer: Retailer,
    invoice: Invoice,
    product_variant_id: str,
    start_date: date,
    end_date: date,
    duration_months: int,
    is_transferable: bool = True,
) -> Warranty:

    if invoice.retailer_id != retailer.id:
        raise ValueError(
            "Invoice does not belong to this retailer."
        )

    if invoice.status != "active":
        raise ValueError(
            "Only active invoices can have warranties."
        )

    if start_date > end_date:
        raise ValueError(
            "Warranty start date cannot be after end date."
        )

    if duration_months <= 0:
        raise ValueError(
            "Warranty duration must be greater than zero."
        )

    product_variant = get_product_variant_by_id(
        db,
        product_variant_id,
    )

    if product_variant is None:
        raise ValueError(
            "Product variant not found."
        )

    invoice_item_exists = False

    for item in invoice.items:
        if str(item.product_variant_id) == product_variant_id:
            invoice_item_exists = True
            break

    if not invoice_item_exists:
        raise ValueError(
            "Product variant was not sold on this invoice."
        )

    existing_statement = select(Warranty).where(
        Warranty.invoice_id == invoice.id,
        Warranty.product_variant_id == product_variant.id,
        Warranty.status == "active",
    )

    existing_warranty = db.execute(
        existing_statement
    ).scalar_one_or_none()

    if existing_warranty is not None:
        raise ValueError(
            "An active warranty already exists for this invoice item."
        )

    warranty = Warranty(
        warranty_id=generate_warranty_id(),
        invoice_id=invoice.id,
        product_variant_id=product_variant.id,
        customer_id=invoice.customer_id,
        start_date=start_date,
        end_date=end_date,
        duration_months=duration_months,
        is_transferable=is_transferable,
        status="active",
    )

    db.add(warranty)
    db.commit()
    db.refresh(warranty)

    return warranty


def update_warranty_status(
    db: Session,
    warranty: Warranty,
    new_status: str,
) -> Warranty:

    new_status = new_status.lower().strip()

    valid_statuses = {
        "active",
        "expired",
        "cancelled",
    }

    if new_status not in valid_statuses:
        raise ValueError(
            "Invalid warranty status."
        )

    if warranty.status == "cancelled" and new_status != "cancelled":
        raise ValueError(
            "A cancelled warranty cannot be reactivated."
        )

    warranty.status = new_status

    db.commit()
    db.refresh(warranty)

    return warranty


def transfer_warranty(
    db: Session,
    warranty: Warranty,
    new_customer_id: str,
) -> Warranty:

    if warranty.status != "active":
        raise ValueError(
            "Only active warranties can be transferred."
        )

    if not warranty.is_transferable:
        raise ValueError(
            "This warranty is not transferable."
        )

    try:
        customer_uuid = uuid.UUID(new_customer_id)
    except ValueError:
        raise ValueError(
            "Invalid customer ID."
        )

    customer = get_customer_by_uuid(
        db,
        customer_uuid,
    )

    if customer is None:
        raise ValueError(
            "Customer not found."
        )

    if customer.id == warranty.customer_id:
        raise ValueError(
            "Warranty already belongs to this customer."
        )

    warranty.customer_id = customer.id

    db.commit()
    db.refresh(warranty)

    return warranty
