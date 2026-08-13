from uuid import uuid4

from app.models.customer import Customer
from app.models.inventory_item import InventoryItem
from app.models.inventory_location import InventoryLocation
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.retailer import Retailer
from app.models.user import User
from app.models.role import Role
from app.models.access_control import user_roles
from app.services.auth_service import create_user_token


def test_create_invoice_api(client, db):
    user = User(
        phone_number=f"999{uuid4().hex[:7]}",
        status="active",
    )
    db.add(user)
    db.flush()

    role = db.query(Role).filter(
        Role.name == "retailer_owner"
    ).one()

    db.execute(
        user_roles.insert().values(
            user_id=user.id,
            role_id=role.id,
        )
    )
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-{uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="API Test Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    location = InventoryLocation(
        retailer_id=retailer.id,
        name="API Test Store",
        location_type="store",
        is_active=True,
    )
    db.add(location)
    db.flush()

    customer_user = User(
        phone_number=f"888{uuid4().hex[:7]}",
        status="active",
    )
    db.add(customer_user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-{uuid4().hex[:8].upper()}",
        user_id=customer_user.id,
        full_name="API Test Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    product = Product(
        product_code=f"PROD-{uuid4().hex[:8].upper()}",
        name="API Test Phone",
        status="active",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        product_id=product.id,
        sku=f"API-TEST-{uuid4().hex[:8].upper()}",
        variant_name="128GB Black",
        selling_price=30000,
        purchase_cost=25000,
        tax_rate=18,
        track_inventory=True,
        status="active",
    )
    db.add(variant)
    db.flush()

    inventory = InventoryItem(
        retailer_id=retailer.id,
        location_id=location.id,
        product_variant_id=variant.id,
        quantity_on_hand=5,
        quantity_reserved=0,
        average_cost=25000,
    )
    db.add(inventory)
    db.flush()

    db.commit()

    token = create_user_token(user)

    response = client.post(
        "/invoices",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "customer_id": customer.customer_id,
            "location_id": str(location.id),
            "items": [
                {
                    "sku": variant.sku,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "active"
    assert data["payment_status"] == "unpaid"
    assert len(data["items"]) == 1
    assert data["items"][0]["sku"] == variant.sku
    assert data["items"][0]["quantity"] == 2

    db.refresh(inventory)

    assert inventory.quantity_on_hand == 3
