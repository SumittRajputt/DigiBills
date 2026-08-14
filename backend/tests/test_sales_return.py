from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.customer import Customer
from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.user import User
from app.services.invoice_service import create_invoice
from app.services.sales_return_service import (
    add_sales_return_item,
    create_sales_return,
    process_sales_return,
)


def create_sales_return_context(db):
    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-SR-{uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Sales Return Test Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Sales Return Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    customer_user = User(
        phone_number=f"8{uuid4().hex[:9]}",
        status="active",
    )
    db.add(customer_user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-SR-{uuid4().hex[:8].upper()}",
        user_id=customer_user.id,
        full_name="Sales Return Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    product = Product(
        product_code=f"PROD-SR-{uuid4().hex[:8].upper()}",
        name="Sales Return Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"SKU-SR-{uuid4().hex[:8].upper()}",
        variant_name="Sales Return Variant",
        purchase_cost=Decimal("1000.00"),
        selling_price=Decimal("1500.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=False,
        status="active",
    )
    db.add(variant)
    db.flush()

    inventory = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=10,
        quantity_reserved=0,
        average_cost=Decimal("1000.00"),
    )
    db.add(inventory)
    db.flush()

    invoice = Invoice(
        invoice_id=f"INV-SR-{uuid4().hex[:10].upper()}",
        retailer_id=retailer.id,
        customer_id=customer.id,
        invoice_date=__import__("datetime").datetime.utcnow(),
        subtotal=Decimal("15000.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("2700.00"),
        total_amount=Decimal("17700.00"),
        payment_status="paid",
        status="active",
    )
    db.add(invoice)
    db.flush()

    invoice_item = InvoiceItem(
        invoice_id=invoice.id,
        product_variant_id=variant.id,
        product_name=variant.variant_name,
        sku=variant.sku,
        quantity=5,
        unit_price=Decimal("1500.00"),
        unit_cost=Decimal("1000.00"),
        discount_amount=Decimal("0.00"),
        tax_rate=Decimal("18.00"),
        tax_amount=Decimal("2700.00"),
        line_total=Decimal("17700.00"),
    )
    db.add(invoice_item)
    db.flush()

    # Create the sale stock movement so the service can determine
    # the invoice's inventory location.
    from app.services.stock_movement_service import create_stock_movement

    create_stock_movement(
        db=db,
        retailer=retailer,
        location=location,
        product_variant=variant,
        inventory_item=inventory,
        movement_type="sale",
        quantity=5,
        unit_cost=Decimal("1000.00"),
        reference_type="invoice",
        reference_id=invoice.id,
        notes="Sales return test sale",
        commit=False,
    )

    db.flush()

    sales_return = create_sales_return(
        db=db,
        retailer=retailer,
        invoice=invoice,
        reason="Customer return",
        notes="Sales return test",
    )

    return (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    )


def test_create_sales_return(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    assert sales_return.status == "requested"
    assert sales_return.invoice_id == invoice.id
    assert sales_return.retailer_id == retailer.id
    assert sales_return.customer_id == customer.id
    assert sales_return.return_amount == Decimal("0.00")
    assert sales_return.refund_amount == Decimal("0.00")
    assert sales_return.reason == "Customer return"


def test_add_sales_return_item_calculates_refund(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    item = add_sales_return_item(
        db=db,
        sales_return=sales_return,
        invoice_item_id=str(invoice_item.id),
        quantity=2,
        condition="good",
        return_to_inventory=True,
        restocking_fee=Decimal("100.00"),
        reason="Customer changed mind",
    )

    assert item.quantity == 2
    assert item.unit_price == Decimal("1500.00")
    assert item.return_amount == Decimal("3000.00")
    assert item.restocking_fee == Decimal("100.00")
    assert item.refund_amount == Decimal("2900.00")

    assert sales_return.return_amount == Decimal("3000.00")
    assert sales_return.refund_amount == Decimal("2900.00")


def test_process_sales_return_reduces_inventory_when_not_returned_to_inventory(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    add_sales_return_item(
        db=db,
        sales_return=sales_return,
        invoice_item_id=str(invoice_item.id),
        quantity=2,
        condition="defective",
        return_to_inventory=False,
        restocking_fee=Decimal("0.00"),
    )

    process_sales_return(
        db=db,
        sales_return=sales_return,
        retailer=retailer,
        processed_by_user_id=user.id,
        refund_method="cash",
    )

    assert sales_return.status == "processed"
    assert sales_return.processed_by_user_id == user.id
    assert sales_return.processed_at is not None
    assert sales_return.refund_method == "cash"

    # Sale reduced 10 -> 5. Because return_to_inventory=False,
    # the returned units are not added back to inventory.
    assert inventory.quantity_on_hand == 5


def test_create_sales_return_rejects_wrong_retailer(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    other_user = User(
        phone_number=f"9{uuid4().hex[:9]}",
        status="active",
    )
    db.add(other_user)
    db.flush()

    other_retailer = Retailer(
        retailer_id=f"RET-OTHER-{uuid4().hex[:8].upper()}",
        owner_user_id=other_user.id,
        business_name="Other Retailer",
        phone_number=other_user.phone_number,
        status="active",
    )
    db.add(other_retailer)
    db.flush()

    with pytest.raises(
        ValueError,
        match="Invoice does not belong to this retailer",
    ):
        create_sales_return(
            db=db,
            retailer=other_retailer,
            invoice=invoice,
        )


def test_create_sales_return_rejects_inactive_invoice(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    # The fixture already created a return, so remove it before
    # testing invoice validation.
    db.delete(sales_return)
    db.commit()

    invoice.status = "cancelled"
    db.commit()

    with pytest.raises(
        ValueError,
        match="Only active invoices can be returned",
    ):
        create_sales_return(
            db=db,
            retailer=retailer,
            invoice=invoice,
        )


def test_create_sales_return_rejects_duplicate_requested_return(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    with pytest.raises(
        ValueError,
        match="requested sales return already exists",
    ):
        create_sales_return(
            db=db,
            retailer=retailer,
            invoice=invoice,
        )


def test_sales_return_rejects_quantity_above_sold_quantity(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    with pytest.raises(
        ValueError,
        match="cannot exceed sold quantity",
    ):
        add_sales_return_item(
            db=db,
            sales_return=sales_return,
            invoice_item_id=str(invoice_item.id),
            quantity=6,
            condition="good",
            return_to_inventory=True,
            restocking_fee=Decimal("0.00"),
        )


def test_sales_return_rejects_invalid_condition(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    with pytest.raises(
        ValueError,
        match="Invalid return condition",
    ):
        add_sales_return_item(
            db=db,
            sales_return=sales_return,
            invoice_item_id=str(invoice_item.id),
            quantity=1,
            condition="expired",
            return_to_inventory=True,
            restocking_fee=Decimal("0.00"),
        )


def test_sales_return_rejects_negative_restocking_fee(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    with pytest.raises(
        ValueError,
        match="Restocking fee cannot be negative",
    ):
        add_sales_return_item(
            db=db,
            sales_return=sales_return,
            invoice_item_id=str(invoice_item.id),
            quantity=1,
            condition="good",
            return_to_inventory=True,
            restocking_fee=Decimal("-1.00"),
        )


def test_sales_return_rejects_restocking_fee_above_return_amount(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    with pytest.raises(
        ValueError,
        match="Restocking fee cannot exceed return amount",
    ):
        add_sales_return_item(
            db=db,
            sales_return=sales_return,
            invoice_item_id=str(invoice_item.id),
            quantity=1,
            condition="good",
            return_to_inventory=True,
            restocking_fee=Decimal("2000.00"),
        )


def test_sales_return_rejects_zero_quantity(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    with pytest.raises(
        ValueError,
        match="Return quantity must be greater than zero",
    ):
        add_sales_return_item(
            db=db,
            sales_return=sales_return,
            invoice_item_id=str(invoice_item.id),
            quantity=0,
            condition="good",
            return_to_inventory=True,
            restocking_fee=Decimal("0.00"),
        )


def test_process_sales_return_rejects_without_items(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    with pytest.raises(
        ValueError,
        match="must contain at least one item",
    ):
        process_sales_return(
            db=db,
            sales_return=sales_return,
            retailer=retailer,
            processed_by_user_id=user.id,
        )


def test_sales_return_cannot_be_processed_twice(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    add_sales_return_item(
        db=db,
        sales_return=sales_return,
        invoice_item_id=str(invoice_item.id),
        quantity=1,
        condition="defective",
        return_to_inventory=False,
        restocking_fee=Decimal("0.00"),
    )

    process_sales_return(
        db=db,
        sales_return=sales_return,
        retailer=retailer,
        processed_by_user_id=user.id,
    )

    with pytest.raises(
        ValueError,
        match="Only requested sales returns can be processed",
    ):
        process_sales_return(
            db=db,
            sales_return=sales_return,
            retailer=retailer,
            processed_by_user_id=user.id,
        )


def test_process_sales_return_restores_inventory_when_returned_to_inventory(db):
    (
        user,
        retailer,
        location,
        customer,
        variant,
        inventory,
        invoice,
        invoice_item,
        sales_return,
    ) = create_sales_return_context(db)

    add_sales_return_item(
        db=db,
        sales_return=sales_return,
        invoice_item_id=str(invoice_item.id),
        quantity=2,
        condition="good",
        return_to_inventory=True,
        restocking_fee=Decimal("0.00"),
    )

    process_sales_return(
        db=db,
        sales_return=sales_return,
        retailer=retailer,
        processed_by_user_id=user.id,
    )

    assert sales_return.status == "processed"

    # Sale reduced 10 -> 5.
    # Return-to-inventory adds 2 back: 5 -> 7.
    assert inventory.quantity_on_hand == 7
