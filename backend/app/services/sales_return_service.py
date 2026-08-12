import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.sales_return import SalesReturn
from app.models.sales_return_item import SalesReturnItem
from app.models.stock_movement import StockMovement
from app.services.stock_movement_service import create_stock_movement


def generate_sales_return_id() -> str:
    return f"SR-{uuid.uuid4().hex[:10].upper()}"


def get_invoice_by_reference(
    db: Session,
    invoice_reference: str,
) -> Optional[Invoice]:
    statement = select(Invoice).where(
        Invoice.invoice_id == invoice_reference
    )

    return db.execute(statement).scalar_one_or_none()


def get_sales_return_by_reference(
    db: Session,
    return_reference: str,
) -> Optional[SalesReturn]:
    statement = select(SalesReturn).where(
        SalesReturn.return_id == return_reference
    )

    return db.execute(statement).scalar_one_or_none()


def get_sales_return_items(
    db: Session,
    sales_return_id: uuid.UUID,
):
    statement = (
        select(SalesReturnItem)
        .where(
            SalesReturnItem.sales_return_id == sales_return_id
        )
        .order_by(
            SalesReturnItem.created_at.asc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_invoice_item(
    db: Session,
    invoice_item_id: str,
) -> Optional[InvoiceItem]:
    try:
        parsed_id = uuid.UUID(invoice_item_id)
    except ValueError:
        return None

    statement = select(InvoiceItem).where(
        InvoiceItem.id == parsed_id
    )

    return db.execute(statement).scalar_one_or_none()


def get_inventory_item(
    db: Session,
    retailer_id: uuid.UUID,
    location_id: uuid.UUID,
    product_variant_id: uuid.UUID,
) -> Optional[InventoryItem]:
    statement = select(InventoryItem).where(
        InventoryItem.retailer_id == retailer_id,
        InventoryItem.location_id == location_id,
        InventoryItem.product_variant_id == product_variant_id,
    )

    return db.execute(statement).scalar_one_or_none()


def get_invoice_location(
    db: Session,
    invoice_id: uuid.UUID,
    retailer_id: uuid.UUID,
) -> Optional[InventoryLocation]:
    statement = (
        select(StockMovement.location_id)
        .where(
            StockMovement.retailer_id == retailer_id,
            StockMovement.reference_type == "invoice",
            StockMovement.reference_id == invoice_id,
            StockMovement.movement_type == "sale",
        )
        .order_by(
            StockMovement.created_at.asc()
        )
        .limit(1)
    )

    location_id = db.execute(statement).scalar_one_or_none()

    if location_id is None:
        return None

    location_statement = select(
        InventoryLocation
    ).where(
        InventoryLocation.id == location_id,
        InventoryLocation.retailer_id == retailer_id,
        InventoryLocation.is_active.is_(True),
    )

    return db.execute(
        location_statement
    ).scalar_one_or_none()


def create_sales_return(
    db: Session,
    retailer: Retailer,
    invoice: Invoice,
    reason: Optional[str] = None,
    notes: Optional[str] = None,
) -> SalesReturn:
    if invoice.retailer_id != retailer.id:
        raise ValueError(
            "Invoice does not belong to this retailer."
        )

    if invoice.status != "active":
        raise ValueError(
            "Only active invoices can be returned."
        )

    existing_statement = select(SalesReturn).where(
        SalesReturn.invoice_id == invoice.id,
        SalesReturn.status == "requested",
    )

    existing_return = db.execute(
        existing_statement
    ).scalar_one_or_none()

    if existing_return is not None:
        raise ValueError(
            "A requested sales return already exists for this invoice."
        )

    sales_return = SalesReturn(
        return_id=generate_sales_return_id(),
        invoice_id=invoice.id,
        retailer_id=retailer.id,
        customer_id=invoice.customer_id,
        processed_by_user_id=None,
        return_amount=Decimal("0.00"),
        refund_amount=Decimal("0.00"),
        refund_method=None,
        status="requested",
        reason=reason,
        notes=notes,
    )

    db.add(sales_return)
    db.commit()
    db.refresh(sales_return)

    return sales_return


def add_sales_return_item(
    db: Session,
    sales_return: SalesReturn,
    invoice_item_id: str,
    quantity: int,
    condition: str,
    return_to_inventory: bool,
    restocking_fee: Decimal,
    reason: Optional[str] = None,
) -> SalesReturnItem:
    if sales_return.status != "requested":
        raise ValueError(
            "Items can only be added to a requested sales return."
        )

    if quantity <= 0:
        raise ValueError(
            "Return quantity must be greater than zero."
        )

    if restocking_fee < 0:
        raise ValueError(
            "Restocking fee cannot be negative."
        )

    invoice_item = get_invoice_item(
        db,
        invoice_item_id,
    )

    if invoice_item is None:
        raise ValueError(
            "Invoice item not found."
        )

    invoice = db.execute(
        select(Invoice).where(
            Invoice.id == sales_return.invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None:
        raise ValueError(
            "Invoice not found."
        )

    if invoice_item.invoice_id != invoice.id:
        raise ValueError(
            "Invoice item does not belong to this invoice."
        )

    condition = condition.lower().strip()

    valid_conditions = {
        "good",
        "damaged",
        "defective",
        "used",
    }

    if condition not in valid_conditions:
        raise ValueError(
            "Invalid return condition."
        )

    existing_items_statement = select(
        SalesReturnItem
    ).where(
        SalesReturnItem.sales_return_id == sales_return.id,
        SalesReturnItem.invoice_item_id == invoice_item.id,
    )

    existing_items = list(
        db.execute(
            existing_items_statement
        ).scalars().all()
    )

    existing_quantity = sum(
        item.quantity
        for item in existing_items
    )

    if existing_quantity + quantity > invoice_item.quantity:
        raise ValueError(
            "Return quantity cannot exceed sold quantity."
        )

    unit_price = invoice_item.unit_price

    return_amount = (
        unit_price * Decimal(quantity)
    )

    if restocking_fee > return_amount:
        raise ValueError(
            "Restocking fee cannot exceed return amount."
        )

    refund_amount = (
        return_amount - restocking_fee
    )

    sales_return_item = SalesReturnItem(
        sales_return_id=sales_return.id,
        invoice_item_id=invoice_item.id,
        product_variant_id=invoice_item.product_variant_id,
        product_name=invoice_item.product_name,
        sku=invoice_item.sku,
        quantity=quantity,
        unit_price=unit_price,
        return_amount=return_amount,
        restocking_fee=restocking_fee,
        refund_amount=refund_amount,
        condition=condition,
        return_to_inventory=return_to_inventory,
        reason=reason,
    )

    db.add(sales_return_item)

    sales_return.return_amount = (
        (sales_return.return_amount or Decimal("0.00"))
        + return_amount
    )

    sales_return.refund_amount = (
        (sales_return.refund_amount or Decimal("0.00"))
        + refund_amount
    )

    db.commit()
    db.refresh(sales_return_item)
    db.refresh(sales_return)

    return sales_return_item


def process_sales_return(
    db: Session,
    sales_return: SalesReturn,
    retailer: Retailer,
    processed_by_user_id: uuid.UUID,
    refund_method: Optional[str] = None,
) -> SalesReturn:
    if sales_return.status != "requested":
        raise ValueError(
            "Only requested sales returns can be processed."
        )

    if sales_return.retailer_id != retailer.id:
        raise ValueError(
            "Sales return does not belong to this retailer."
        )

    items = get_sales_return_items(
        db,
        sales_return.id,
    )

    if not items:
        raise ValueError(
            "Sales return must contain at least one item."
        )

    invoice = db.execute(
        select(Invoice).where(
            Invoice.id == sales_return.invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None:
        raise ValueError(
            "Invoice not found."
        )

    if invoice.retailer_id != retailer.id:
        raise ValueError(
            "Invoice does not belong to this retailer."
        )

    location = get_invoice_location(
        db,
        invoice.id,
        retailer.id,
    )

    if location is None:
        raise ValueError(
            "Inventory location could not be determined from the invoice."
        )

    for item in items:
        if not item.return_to_inventory:
            continue

        inventory_item = get_inventory_item(
            db=db,
            retailer_id=retailer.id,
            location_id=location.id,
            product_variant_id=item.product_variant_id,
        )

        if inventory_item is None:
            raise ValueError(
                f"Inventory item not found for SKU {item.sku}."
            )

        product_variant = db.execute(
            select(ProductVariant).where(
                ProductVariant.id == item.product_variant_id
            )
        ).scalar_one_or_none()

        if product_variant is None:
            raise ValueError(
                f"Product variant not found for SKU {item.sku}."
            )

        create_stock_movement(
            db=db,
            retailer=retailer,
            location=location,
            product_variant=product_variant,
            inventory_item=inventory_item,
            movement_type="return_in",
            quantity=item.quantity,
            performed_by_user_id=processed_by_user_id,
            unit_cost=inventory_item.average_cost,
            reference_type="sales_return",
            reference_id=sales_return.id,
            notes=(
                f"Returned against sales return "
                f"{sales_return.return_id}"
            ),
            commit=False,
        )

    sales_return.processed_by_user_id = (
        processed_by_user_id
    )
    sales_return.refund_method = refund_method
    sales_return.status = "processed"
    sales_return.processed_at = (
        datetime.now(timezone.utc)
    )

    db.commit()
    db.refresh(sales_return)

    return sales_return
