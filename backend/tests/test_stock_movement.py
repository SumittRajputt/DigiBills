from decimal import Decimal
import uuid

from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.services.invoice_service import create_invoice
from app.services.stock_movement_service import create_stock_movement


def test_stock_purchase_increases_inventory(db):
    user = User(
        phone_number="9999999999",
        email="stock-test@example.com",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id="RET-TEST-001",
        owner_user_id=user.id,
        business_name="Test Retailer",
        phone_number="9999999999",
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    product = Product(
        product_code="PROD-TEST-001",
        name="Test Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku="TEST-SKU-001",
        variant_name="Test Variant",
        purchase_cost=Decimal("100.00"),
        selling_price=Decimal("150.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=False,
        status="active",
    )
    db.add(variant)
    db.flush()

    inventory_item = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=0,
        quantity_reserved=0,
        average_cost=Decimal("0.00"),
    )
    db.add(inventory_item)
    db.flush()

    movement = create_stock_movement(
        db=db,
        retailer=retailer,
        location=location,
        product_variant=variant,
        inventory_item=inventory_item,
        movement_type="purchase",
        quantity=5,
        unit_cost=Decimal("100.00"),
        reference_type="test",
        notes="Automated test",
        commit=False,
    )

    db.flush()

    assert movement.movement_type == "purchase"
    assert movement.quantity == 5
    assert inventory_item.quantity_on_hand == 5
    assert inventory_item.average_cost == Decimal("100.00")


def test_stock_sale_decreases_inventory(db):
    user = User(
        phone_number="9999999998",
        email="stock-sale-test@example.com",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id="RET-TEST-002",
        owner_user_id=user.id,
        business_name="Test Retailer Sale",
        phone_number="9999999998",
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    product = Product(
        product_code="PROD-TEST-002",
        name="Test Sale Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku="TEST-SKU-002",
        variant_name="Test Sale Variant",
        purchase_cost=Decimal("100.00"),
        selling_price=Decimal("150.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=False,
        status="active",
    )
    db.add(variant)
    db.flush()

    inventory_item = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=10,
        quantity_reserved=0,
        average_cost=Decimal("100.00"),
    )
    db.add(inventory_item)
    db.flush()

    movement = create_stock_movement(
        db=db,
        retailer=retailer,
        location=location,
        product_variant=variant,
        inventory_item=inventory_item,
        movement_type="sale",
        quantity=3,
        unit_cost=Decimal("100.00"),
        reference_type="test",
        notes="Automated sale test",
        commit=False,
    )

    db.flush()

    assert movement.movement_type == "sale"
    assert movement.quantity == 3
    assert inventory_item.quantity_on_hand == 7
    assert inventory_item.quantity_reserved == 0


def test_stock_sale_rejects_insufficient_available_stock(db):
    user = User(
        phone_number="9999999997",
        email="stock-insufficient-test@example.com",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id="RET-TEST-003",
        owner_user_id=user.id,
        business_name="Test Retailer Insufficient",
        phone_number="9999999997",
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    product = Product(
        product_code="PROD-TEST-003",
        name="Test Insufficient Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku="TEST-SKU-003",
        variant_name="Test Insufficient Variant",
        purchase_cost=Decimal("100.00"),
        selling_price=Decimal("150.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=False,
        status="active",
    )
    db.add(variant)
    db.flush()

    inventory_item = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=5,
        quantity_reserved=2,
        average_cost=Decimal("100.00"),
    )
    db.add(inventory_item)
    db.flush()

    try:
        create_stock_movement(
            db=db,
            retailer=retailer,
            location=location,
            product_variant=variant,
            inventory_item=inventory_item,
            movement_type="sale",
            quantity=4,
            unit_cost=Decimal("100.00"),
            reference_type="test",
            notes="Insufficient stock test",
            commit=False,
        )

        assert False, "Expected insufficient stock error"

    except ValueError as exc:
        assert str(exc) == "Insufficient available stock."

    assert inventory_item.quantity_on_hand == 5
    assert inventory_item.quantity_reserved == 2


def test_stock_sale_can_use_only_available_quantity(db):
    user = User(
        phone_number="9999999996",
        email="stock-reserved-test@example.com",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id="RET-TEST-004",
        owner_user_id=user.id,
        business_name="Test Retailer Reserved",
        phone_number="9999999996",
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    product = Product(
        product_code="PROD-TEST-004",
        name="Test Reserved Product",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku="TEST-SKU-004",
        variant_name="Test Reserved Variant",
        purchase_cost=Decimal("100.00"),
        selling_price=Decimal("150.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=False,
        status="active",
    )
    db.add(variant)
    db.flush()

    inventory_item = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=10,
        quantity_reserved=4,
        average_cost=Decimal("100.00"),
    )
    db.add(inventory_item)
    db.flush()

    movement = create_stock_movement(
        db=db,
        retailer=retailer,
        location=location,
        product_variant=variant,
        inventory_item=inventory_item,
        movement_type="sale",
        quantity=6,
        unit_cost=Decimal("100.00"),
        reference_type="test",
        notes="Reserved stock boundary test",
        commit=False,
    )

    db.flush()

    assert movement.quantity == 6
    assert inventory_item.quantity_on_hand == 4
    assert inventory_item.quantity_reserved == 4
    assert inventory_item.quantity_available == 0


def test_invoice_creation_decreases_stock_and_creates_audit_log(db):
    user = User(
        phone_number=f"999{uuid.uuid4().hex[:7]}",
        email=f"invoice-test-{uuid.uuid4().hex[:8]}@example.com",
        status="active",
    )
    db.add(user)
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-TEST-{uuid.uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Test Invoice Retailer",
        phone_number="9999999995",
        status="active",
    )
    db.add(retailer)
    db.flush()

    customer = Customer(
        customer_id=f"CUST-TEST-{uuid.uuid4().hex[:8].upper()}",
        user_id=user.id,
        full_name="Test Customer",
        phone_number="9999999994",
        status="active",
    )
    db.add(customer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    product = Product(
        product_code=f"PROD-TEST-{uuid.uuid4().hex[:8].upper()}",
        name="Test Invoice Product",
        status="active",
    )
    db.add(product)
    db.flush()

    sku = f"TEST-SKU-{uuid.uuid4().hex[:8].upper()}"

    variant = ProductVariant(
        product_id=product.id,
        sku=sku,
        variant_name="Test Invoice Variant",
        purchase_cost=Decimal("100.00"),
        selling_price=Decimal("150.00"),
        tax_rate=Decimal("18.00"),
        track_inventory=True,
        requires_serial_number=False,
        status="active",
    )
    db.add(variant)
    db.flush()

    inventory_item = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=10,
        quantity_reserved=0,
        average_cost=Decimal("100.00"),
    )
    db.add(inventory_item)
    db.flush()

    class InvoiceItem:
        pass

    invoice_item = InvoiceItem()
    invoice_item.sku = sku
    invoice_item.quantity = 2
    invoice_item.product_unit_ids = []
    invoice_item.unit_price = Decimal("150.00")
    invoice_item.discount_amount = Decimal("0.00")

    invoice = create_invoice(
        db=db,
        retailer=retailer,
        customer=customer,
        location=location,
        items=[invoice_item],
        invoice_number="TEST-INV-001",
        invoice_discount=Decimal("0.00"),
        notes="Automated invoice integration test",
        employee_id=None,
        user_id=user.id,
    )

    assert invoice.payment_status == "unpaid"
    assert invoice.status == "active"
    assert invoice.total_amount == Decimal("354.00")

    assert inventory_item.quantity_on_hand == 8

    movement = (
        db.query(StockMovement)
        .filter(
            StockMovement.reference_type == "invoice",
            StockMovement.reference_id == invoice.id,
        )
        .one()
    )

    assert movement.movement_type == "sale"
    assert movement.quantity == 2
    assert movement.performed_by_user_id == user.id

    audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "INVOICE_CREATED",
            AuditLog.entity_id == invoice.id,
        )
        .one()
    )

    assert audit.user_id == user.id
    assert "TEST-INV-001" not in audit.description
    assert invoice.invoice_id in audit.description
