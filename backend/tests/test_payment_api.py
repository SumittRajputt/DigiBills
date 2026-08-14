from decimal import Decimal
from uuid import uuid4

from app.models.access_control import user_roles
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.retailer import Retailer
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import create_user_token


def create_payment_api_context(
    db,
    total_amount=Decimal("10000.00"),
    retailer_status="active",
):
    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
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
        retailer_id=f"RET-PAY-API-{uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Payment API Retailer",
        phone_number=user.phone_number,
        status=retailer_status,
    )
    db.add(retailer)
    db.flush()

    customer_user = User(
        phone_number=f"8{uuid4().hex[:9]}",
        status="active",
    )
    db.add(customer_user)
    db.flush()

    customer = Customer(
        customer_id=f"CUS-PAY-API-{uuid4().hex[:6].upper()}",
        user_id=customer_user.id,
        full_name="Payment API Customer",
        phone_number=customer_user.phone_number,
        status="active",
    )
    db.add(customer)
    db.flush()

    invoice = Invoice(
        invoice_id=f"INV-PAY-API-{uuid4().hex[:8].upper()}",
        retailer_id=retailer.id,
        customer_id=customer.id,
        invoice_date=__import__("datetime").datetime.utcnow(),
        subtotal=total_amount,
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=total_amount,
        payment_status="unpaid",
        status="active",
    )
    db.add(invoice)
    db.commit()

    return {
        "user": user,
        "retailer": retailer,
        "customer": customer,
        "invoice": invoice,
        "token": create_user_token(user),
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_payment_api(client, db):
    context = create_payment_api_context(db)

    response = client.post(
        "/payments",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "amount": "4000.00",
            "payment_method": " CASH ",
            "transaction_reference": "TXN-API-001",
            "notes": "API payment test",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["payment_id"].startswith("PAY-")
    assert data["invoice_id"] == str(
        context["invoice"].id
    )
    assert data["amount"] == "4000.00"
    assert data["payment_method"] == "cash"
    assert data["payment_status"] == "completed"
    assert data["transaction_reference"] == "TXN-API-001"
    assert data["refund_amount"] == "0.00"
    assert data["refund_status"] is None
    assert data["notes"] == "API payment test"
    assert data["paid_at"]
    assert data["created_at"]
    assert data["updated_at"]


def test_list_invoice_payments_api(client, db):
    context = create_payment_api_context(db)

    client.post(
        "/payments",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "amount": "4000.00",
            "payment_method": "cash",
        },
    )

    response = client.get(
        f"/payments/invoice/{context['invoice'].invoice_id}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["amount"] == "4000.00"
    assert data[0]["payment_method"] == "cash"
    assert data[0]["payment_status"] == "completed"


def test_list_invoice_payments_api_returns_empty_list(
    client,
    db,
):
    context = create_payment_api_context(db)

    response = client.get(
        f"/payments/invoice/{context['invoice'].invoice_id}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_payment_api(client, db):
    context = create_payment_api_context(db)

    create_response = client.post(
        "/payments",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "amount": "2500.00",
            "payment_method": "upi",
            "transaction_reference": "TXN-GET-001",
        },
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["payment_id"]

    response = client.get(
        f"/payments/{payment_id}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == payment_id
    assert data["amount"] == "2500.00"
    assert data["payment_method"] == "upi"
    assert data["transaction_reference"] == "TXN-GET-001"


def test_create_payment_api_rejects_unknown_invoice(
    client,
    db,
):
    context = create_payment_api_context(db)

    response = client.post(
        "/payments",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": "INV-DOES-NOT-EXIST",
            "amount": "1000.00",
            "payment_method": "cash",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found."


def test_create_payment_api_rejects_excess_payment(
    client,
    db,
):
    context = create_payment_api_context(
        db,
        total_amount=Decimal("5000.00"),
    )

    response = client.post(
        "/payments",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "amount": "5000.01",
            "payment_method": "cash",
        },
    )

    assert response.status_code == 409
    assert "cannot exceed" in response.json()["detail"]


def test_create_payment_api_rejects_payment_on_inactive_retailer(
    client,
    db,
):
    context = create_payment_api_context(
        db,
        retailer_status="pending",
    )

    response = client.post(
        "/payments",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "amount": "1000.00",
            "payment_method": "cash",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Retailer is not active."


def test_refund_payment_api_partial_refund(client, db):
    context = create_payment_api_context(db)

    create_response = client.post(
        "/payments",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "amount": "5000.00",
            "payment_method": "cash",
        },
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["payment_id"]

    response = client.post(
        f"/payments/{payment_id}/refund",
        headers=auth_headers(context["token"]),
        json={
            "refund_amount": "2000.00",
            "notes": "Partial refund",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == payment_id
    assert data["refund_amount"] == "2000.00"
    assert data["refund_status"] == "partial"


def test_refund_payment_api_full_refund(client, db):
    context = create_payment_api_context(db)

    create_response = client.post(
        "/payments",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "amount": "5000.00",
            "payment_method": "cash",
        },
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["payment_id"]

    response = client.post(
        f"/payments/{payment_id}/refund",
        headers=auth_headers(context["token"]),
        json={
            "refund_amount": "5000.00",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["refund_amount"] == "5000.00"
    assert data["refund_status"] == "refunded"


def test_refund_payment_api_rejects_excess_refund(
    client,
    db,
):
    context = create_payment_api_context(db)

    create_response = client.post(
        "/payments",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "amount": "3000.00",
            "payment_method": "cash",
        },
    )

    payment_id = create_response.json()["payment_id"]

    response = client.post(
        f"/payments/{payment_id}/refund",
        headers=auth_headers(context["token"]),
        json={
            "refund_amount": "3000.01",
        },
    )

    assert response.status_code == 409
    assert "cannot exceed" in response.json()["detail"]


def test_cancel_payment_api(client, db):
    context = create_payment_api_context(db)

    create_response = client.post(
        "/payments",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "amount": "4000.00",
            "payment_method": "cash",
        },
    )

    payment_id = create_response.json()["payment_id"]

    response = client.post(
        f"/payments/{payment_id}/cancel",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == payment_id
    assert data["payment_status"] == "cancelled"


def test_get_payment_api_returns_404_for_unknown_payment(
    client,
    db,
):
    context = create_payment_api_context(db)

    response = client.get(
        "/payments/PAY-DOES-NOT-EXIST",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found."


def test_refund_payment_api_returns_404_for_unknown_payment(
    client,
    db,
):
    context = create_payment_api_context(db)

    response = client.post(
        "/payments/PAY-DOES-NOT-EXIST/refund",
        headers=auth_headers(context["token"]),
        json={
            "refund_amount": "100.00",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found."


def test_cancel_payment_api_returns_404_for_unknown_payment(
    client,
    db,
):
    context = create_payment_api_context(db)

    response = client.post(
        "/payments/PAY-DOES-NOT-EXIST/cancel",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found."


def test_refunded_payment_cannot_be_cancelled_api(
    client,
    db,
):
    context = create_payment_api_context(db)

    create_response = client.post(
        "/payments",
        headers=auth_headers(context["token"]),
        json={
            "invoice_id": context["invoice"].invoice_id,
            "amount": "5000.00",
            "payment_method": "cash",
        },
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()["payment_id"]

    refund_response = client.post(
        f"/payments/{payment_id}/refund",
        headers=auth_headers(context["token"]),
        json={
            "refund_amount": "1000.00",
        },
    )

    assert refund_response.status_code == 200

    response = client.post(
        f"/payments/{payment_id}/cancel",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "A payment with refunds cannot be cancelled."
    )


def test_list_invoice_payments_api_returns_404_for_unknown_invoice(
    client,
    db,
):
    context = create_payment_api_context(db)

    response = client.get(
        "/payments/invoice/INV-DOES-NOT-EXIST",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invoice not found."


def test_create_payment_api_rejects_unauthenticated_request(
    client,
    db,
):
    context = create_payment_api_context(db)

    response = client.post(
        "/payments",
        json={
            "invoice_id": context["invoice"].invoice_id,
            "amount": "1000.00",
            "payment_method": "cash",
        },
    )

    assert response.status_code == 401


def test_get_payment_api_rejects_unauthenticated_request(
    client,
    db,
):
    response = client.get(
        "/payments/PAY-DOES-NOT-EXIST",
    )

    assert response.status_code == 401
