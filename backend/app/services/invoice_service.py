import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.services.stock_movement_service import create_stock_movement


MONEY_PLACES = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(
        MONEY_PLACES,
        rounding=ROUND_HALF_UP,
    )


def generate_invoice_id() -> str:
    return f"INV-{uuid.uuid4().hex[:10].upper()}"


def get_invoice_by_id(
    db: Session,
    invoice_id: uuid.UUID,
) -> Optional[Invoice]:
    statement = select(Invoice).where(
        Invoice.id == invoice_id
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


def get_customer(
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

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_location_for_retailer(
    db: Session,
    location_id: str,
    retailer_id: uuid.UUID,
) -> Optional[InventoryLocation]:
    try:
        parsed_id = uuid.UUID(location_id)
    except ValueError:
        return None

    statement = select(InventoryLocation).where(
        InventoryLocation.id == parsed_id,
        InventoryLocation.retailer_id == retailer_id,
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_variant_with_product(
    db: Session,
    sku: str,
):
    statement = (
        select(ProductVariant, Product)
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .where(
            ProductVariant.sku == sku,
        )
    )

    return db.execute(
        statement
    ).first()


def get_inventory_item(
    db: Session,
    retailer_id: uuid.UUID,
    location_id: uuid.UUID,
    product_variant_id: uuid.UUID,
) -> Optional[InventoryItem]:
    statement = select(InventoryItem).where(
        InventoryItem.retailer_id == retailer_id,
        InventoryItem.location_id == location_id,
        InventoryItem.product_variant_id
        == product_variant_id,
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def create_invoice(
    db: Session,
    retailer: Retailer,
    customer: Customer,
    location: InventoryLocation,
    items: list,
    invoice_number: Optional[str] = None,
    invoice_discount: Decimal = Decimal("0.00"),
    notes: Optional[str] = None,
    employee_id: Optional[uuid.UUID] = None,
) -> Invoice:

    if retailer.status != "active":
        raise ValueError(
            "Retailer is not active."
        )

    if customer.status != "active":
        raise ValueError(
            "Customer is not active."
        )

    if location.retailer_id != retailer.id:
        raise ValueError(
            "Inventory location does not belong to this retailer."
        )

    if invoice_discount < 0:
        raise ValueError(
            "Invoice discount cannot be negative."
        )

    invoice_discount = money(invoice_discount)

    if not items:
        raise ValueError(
            "Invoice must contain at least one item."
        )

    prepared_items = []

    subtotal = Decimal("0.00")
    total_tax = Decimal("0.00")

    for request_item in items:

        sku = request_item.sku.strip()

        if not sku:
            raise ValueError(
                "SKU cannot be empty."
            )

        result = get_variant_with_product(
            db,
            sku,
        )

        if result is None:
            raise ValueError(
                f"Product variant with SKU '{sku}' not found."
            )

        variant, product = result

        if variant.status != "active":
            raise ValueError(
                f"Product variant '{sku}' is not active."
            )

        if not variant.track_inventory:
            raise ValueError(
                f"Inventory tracking is disabled for SKU '{sku}'."
            )

        inventory_item = get_inventory_item(
            db=db,
            retailer_id=retailer.id,
            location_id=location.id,
            product_variant_id=variant.id,
        )

        if inventory_item is None:
            raise ValueError(
                f"Inventory item not found for SKU '{sku}'."
            )

        available_quantity = (
            inventory_item.quantity_on_hand
            - inventory_item.quantity_reserved
        )

        if request_item.quantity > available_quantity:
            raise ValueError(
                f"Insufficient available stock for SKU '{sku}'. "
                f"Available: {available_quantity}, "
                f"requested: {request_item.quantity}."
            )

        unit_price = (
            request_item.unit_price
            if request_item.unit_price is not None
            else variant.selling_price
        )

        unit_price = money(unit_price)

        item_discount = money(
            request_item.discount_amount
        )

        gross_amount = money(
            unit_price
            * Decimal(request_item.quantity)
        )

        if item_discount > gross_amount:
            raise ValueError(
                f"Item discount cannot exceed item amount "
                f"for SKU '{sku}'."
            )

        net_amount = money(
            gross_amount - item_discount
        )

        tax_rate = (
            variant.tax_rate
            or Decimal("0.00")
        )

        tax_amount = money(
            net_amount
            * tax_rate
            / Decimal("100")
        )

        line_total = money(
            net_amount + tax_amount
        )

        subtotal += net_amount
        total_tax += tax_amount

        prepared_items.append(
            {
                "variant": variant,
                "product": product,
                "inventory_item": inventory_item,
                "quantity": request_item.quantity,
                "unit_price": unit_price,
                "item_discount": item_discount,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "line_total": line_total,
            }
        )

    subtotal = money(subtotal)
    total_tax = money(total_tax)

    if invoice_discount > subtotal:
        raise ValueError(
            "Invoice discount cannot exceed subtotal."
        )

    total_amount = money(
        subtotal
        - invoice_discount
        + total_tax
    )

    invoice = Invoice(
        invoice_id=generate_invoice_id(),
        retailer_id=retailer.id,
        employee_id=employee_id,
        customer_id=customer.id,
        invoice_number=invoice_number,
        invoice_date=datetime.now(timezone.utc),
        subtotal=subtotal,
        discount_amount=invoice_discount,
        tax_amount=total_tax,
        total_amount=total_amount,
        payment_status="unpaid",
        status="active",
        notes=notes,
    )

    db.add(invoice)
    db.flush()

    for prepared in prepared_items:

        variant = prepared["variant"]
        product = prepared["product"]

        invoice_item = InvoiceItem(
            invoice_id=invoice.id,
            product_variant_id=variant.id,
            product_name=product.name,
            sku=variant.sku,
            quantity=prepared["quantity"],
            unit_price=prepared["unit_price"],
            unit_cost=variant.purchase_cost,
            discount_amount=prepared["item_discount"],
            tax_rate=prepared["tax_rate"],
            tax_amount=prepared["tax_amount"],
            line_total=prepared["line_total"],
        )

        db.add(invoice_item)

        create_stock_movement(
            db=db,
            retailer=retailer,
            location=location,
            product_variant=variant,
            inventory_item=prepared["inventory_item"],
            movement_type="sale",
            quantity=prepared["quantity"],
            performed_by_user_id=employee_id,
            unit_cost=variant.purchase_cost,
            reference_type="invoice",
            reference_id=invoice.id,
            notes=f"Sold against invoice {invoice.invoice_id}",
            commit=False,
        )

    db.commit()
    db.refresh(invoice)

    return invoice


def get_invoice_items(
    db: Session,
    invoice_id: uuid.UUID,
) -> list[InvoiceItem]:
    statement = (
        select(InvoiceItem)
        .where(
            InvoiceItem.invoice_id == invoice_id
        )
        .order_by(
            InvoiceItem.created_at.asc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )
