import hashlib
import hmac
from uuid import uuid4

from app.core.config import settings
from app.models.role import Role
from app.models.user import User
from app.models.access_control import user_roles
from app.services.auth_service import create_user_token


def create_customer_context(db):
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

    db.commit()

    token = create_user_token(user)

    return {
        "user": user,
        "token": token,
    }


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_customer_uploaded_bill_route(client, db):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Uploaded Bill Test Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": "uploaded-bill-test@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "test.pdf",
                b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201

    uploaded_bill = response.json()

    order_id = uploaded_bill["razorpay_order_id"]
    payment_id = f"pay_test_customer_bill_{uuid4().hex}"

    signature_payload = f"{order_id}|{payment_id}"

    signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        signature_payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    from unittest.mock import patch

    with patch(
        "app.api.routes.customer_uploaded_bills._get_razorpay_client"
    ) as mock_get_client, patch(
        "app.api.routes.customer_uploaded_bills.create_customer_bill_extraction"
    ) as mock_extraction:
        mock_extraction.return_value = None
        mock_client = mock_get_client.return_value

        mock_client.payment.fetch.return_value = {
            "id": payment_id,
            "order_id": order_id,
            "amount": 900,
            "currency": "INR",
            "status": "captured",
        }

        verify_response = client.post(
            "/customer/uploaded-bills/verify-payment",
            headers=auth_headers(context["token"]),
            params={
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            },
        )

    assert verify_response.status_code == 200

    result = verify_response.json()

    assert result["bill_id"] == uploaded_bill["bill_id"]
    assert result["amount"] == "9.00"
    assert result["payment_status"] == "paid"
    assert result["status"] == "completed"
    assert result["razorpay_order_id"] == order_id
    assert result["razorpay_payment_id"] == payment_id

    db.refresh(
        db.query(
            __import__(
                "app.models.customer_uploaded_bill",
                fromlist=["CustomerUploadedBill"],
            ).CustomerUploadedBill
        )
        .filter(
            __import__(
                "app.models.customer_uploaded_bill",
                fromlist=["CustomerUploadedBill"],
            ).CustomerUploadedBill.bill_id
            == uploaded_bill["bill_id"]
        )
        .first()
    )


def test_customer_uploaded_bill_invalid_payment_signature(client, db):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Invalid Payment Signature Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": "invalid-payment-signature@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    upload_response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "invalid-signature.pdf",
                b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    uploaded_bill = upload_response.json()

    verify_response = client.post(
        "/customer/uploaded-bills/verify-payment",
        headers=auth_headers(context["token"]),
        params={
            "razorpay_order_id": uploaded_bill["razorpay_order_id"],
            "razorpay_payment_id": "pay_invalid_001",
            "razorpay_signature": "invalid_signature",
        },
    )

    assert verify_response.status_code == 400
    assert verify_response.json()["detail"] == (
        "Invalid Razorpay payment signature."
    )


def test_customer_uploaded_bill_with_active_subscription_is_free(client, db):
    from datetime import datetime, timedelta, timezone

    from app.models.customer import Customer
    from app.models.subscription import Subscription
    from app.models.subscription_plan import SubscriptionPlan

    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Free Upload Subscription Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": "free-upload-subscription@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    customer = (
        db.query(Customer)
        .filter(
            Customer.user_id == context["user"].id
        )
        .one()
    )

    assert customer is not None

    now = datetime.now(timezone.utc)

    plan = SubscriptionPlan(
        plan_id=f"test_customer_upload_{uuid4().hex[:8]}",
        name="Customer Upload Test Plan",
        description="Customer upload subscription test plan",
        customer_type="customer",
        billing_type="yearly",
        monthly_price=0,
        yearly_price=99,
        per_bill_price=0,
        trial_days=0,
        features="[]",
        limits="{}",
        is_active=True,
    )

    db.add(plan)
    db.flush()

    subscription = Subscription(
        subscription_id=f"SUB-UPLOAD-{uuid4().hex[:8].upper()}",
        plan_id=plan.id,
        retailer_id=None,
        customer_id=customer.id,
        salesman_id=None,
        status="active",
        started_at=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=365),
        trial_ends_at=None,
        auto_renew=True,
    )

    db.add(subscription)
    db.commit()

    from unittest.mock import patch

    with patch(
        "app.api.routes.customer_uploaded_bills.create_customer_bill_extraction"
    ) as mock_extraction:
        mock_extraction.return_value = None

        response = client.post(
            "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "free-bill.pdf",
                b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n",
                "application/pdf",
            )
        },
    )


    print("FREE UPLOAD STATUS:", response.status_code)
    print("FREE UPLOAD RESPONSE:", response.text)

    assert response.status_code == 201

    data = response.json()

    assert data["amount"] == "0.00"
    assert data["payment_status"] == "not_required"
    assert data["status"] == "completed"
    assert data["razorpay_order_id"] is None
    assert data["razorpay_payment_id"] is None



def test_customer_uploaded_bill_rejects_non_pdf(client, db):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Non PDF Upload Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"non-pdf-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "not-a-pdf.txt",
                b"This is not a PDF file.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are allowed."


def test_customer_uploaded_bill_rejects_fake_pdf(client, db):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Fake PDF Upload Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"fake-pdf-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "fake.pdf",
                b"This file is not really a PDF.",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is not a valid PDF."


def test_customer_uploaded_bill_rejects_empty_file(client, db):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Empty PDF Upload Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"empty-pdf-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "empty.pdf",
                b"",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded PDF is empty."


def test_customer_uploaded_bill_rejects_oversized_file(client, db):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Oversized PDF Upload Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"oversized-pdf-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    oversized_pdf = b"%PDF-1.4\n" + (
        b"A" * (10 * 1024 * 1024 + 1)
    )

    response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "oversized.pdf",
                oversized_pdf,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded PDF must be 10 MB or smaller."


def test_customer_uploaded_bill_rejects_inactive_customer(client, db):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Inactive Upload Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"inactive-upload-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    from app.models.customer import Customer

    customer = (
        db.query(Customer)
        .filter(Customer.user_id == context["user"].id)
        .one()
    )

    customer.status = "inactive"
    db.commit()

    response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "inactive.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Customer account is not active."


def test_customer_uploaded_bill_payment_verification_is_idempotent(client, db, monkeypatch):
    context = create_customer_context(db)

    monkeypatch.setattr(
        "app.api.routes.customer_uploaded_bills.create_customer_bill_extraction",
        lambda **kwargs: None,
    )

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Idempotent Payment Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"idempotent-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    upload_response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "idempotent.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    bill = upload_response.json()
    order_id = bill["razorpay_order_id"]
    payment_id = f"pay_test_{uuid4().hex[:12]}"

    signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    class MockRazorpayClient:
        class Utility:
            @staticmethod
            def verify_payment_signature(_payload):
                return None

        utility = Utility()

        class Payment:
            @staticmethod
            def fetch(_payment_id):
                return {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": 900,
                    "currency": "INR",
                    "status": "captured",
                }

        payment = Payment()

    monkeypatch.setattr(
        "app.api.routes.customer_uploaded_bills._get_razorpay_client",
        lambda: MockRazorpayClient(),
    )

    payload = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    }

    first_response = client.post(
        "/customer/uploaded-bills/verify-payment",
        headers=auth_headers(context["token"]),
        params=payload,
    )

    assert first_response.status_code == 200
    assert first_response.json()["payment_status"] == "paid"
    assert first_response.json()["status"] == "completed"

    second_response = client.post(
        "/customer/uploaded-bills/verify-payment",
        headers=auth_headers(context["token"]),
        params=payload,
    )

    assert second_response.status_code == 200
    assert second_response.json()["id"] == first_response.json()["id"]
    assert second_response.json()["payment_status"] == "paid"
    assert second_response.json()["status"] == "completed"


def test_customer_uploaded_bill_rejects_wrong_razorpay_order_id(
    client, db, monkeypatch
):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Wrong Order Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"wrong-order-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    upload_response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "wrong-order.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    bill = upload_response.json()
    actual_order_id = bill["razorpay_order_id"]
    payment_id = f"pay_test_{uuid4().hex[:12]}"
    wrong_order_id = f"order_wrong_{uuid4().hex[:12]}"

    signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{wrong_order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    class MockRazorpayClient:
        class Utility:
            @staticmethod
            def verify_payment_signature(_payload):
                return None

        utility = Utility()

        class Payment:
            @staticmethod
            def fetch(_payment_id):
                return {
                    "id": payment_id,
                    "order_id": wrong_order_id,
                    "amount": 900,
                    "currency": "INR",
                    "status": "captured",
                }

        payment = Payment()

    monkeypatch.setattr(
        "app.api.routes.customer_uploaded_bills._get_razorpay_client",
        lambda: MockRazorpayClient(),
    )

    response = client.post(
        "/customer/uploaded-bills/verify-payment",
        headers=auth_headers(context["token"]),
        params={
            "razorpay_order_id": wrong_order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Uploaded bill payment order not found."

    # The original bill must remain unpaid.
    assert actual_order_id != wrong_order_id


def test_customer_uploaded_bill_rejects_wrong_payment_amount(
    client, db, monkeypatch
):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Wrong Amount Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"wrong-amount-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    upload_response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "wrong-amount.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    bill = upload_response.json()
    order_id = bill["razorpay_order_id"]
    payment_id = f"pay_test_{uuid4().hex[:12]}"

    signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    class MockRazorpayClient:
        class Utility:
            @staticmethod
            def verify_payment_signature(_payload):
                return None

        utility = Utility()

        class Payment:
            @staticmethod
            def fetch(_payment_id):
                return {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": 100,
                    "currency": "INR",
                    "status": "captured",
                }

        payment = Payment()

    monkeypatch.setattr(
        "app.api.routes.customer_uploaded_bills._get_razorpay_client",
        lambda: MockRazorpayClient(),
    )

    response = client.post(
        "/customer/uploaded-bills/verify-payment",
        headers=auth_headers(context["token"]),
        params={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Razorpay payment amount is invalid."


def test_customer_uploaded_bill_rejects_wrong_payment_currency(
    client, db, monkeypatch
):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Wrong Currency Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"wrong-currency-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    upload_response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "wrong-currency.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    bill = upload_response.json()
    order_id = bill["razorpay_order_id"]
    payment_id = f"pay_test_{uuid4().hex[:12]}"

    signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    class MockRazorpayClient:
        class Utility:
            @staticmethod
            def verify_payment_signature(_payload):
                return None

        utility = Utility()

        class Payment:
            @staticmethod
            def fetch(_payment_id):
                return {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": 900,
                    "currency": "USD",
                    "status": "captured",
                }

        payment = Payment()

    monkeypatch.setattr(
        "app.api.routes.customer_uploaded_bills._get_razorpay_client",
        lambda: MockRazorpayClient(),
    )

    response = client.post(
        "/customer/uploaded-bills/verify-payment",
        headers=auth_headers(context["token"]),
        params={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Razorpay payment currency is invalid."


def test_customer_uploaded_bill_rejects_uncaptured_payment(
    client, db, monkeypatch
):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Uncaptured Payment Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"uncaptured-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    upload_response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "uncaptured.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    bill = upload_response.json()
    order_id = bill["razorpay_order_id"]
    payment_id = f"pay_test_{uuid4().hex[:12]}"

    signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    class MockRazorpayClient:
        class Utility:
            @staticmethod
            def verify_payment_signature(_payload):
                return None

        utility = Utility()

        class Payment:
            @staticmethod
            def fetch(_payment_id):
                return {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": 900,
                    "currency": "INR",
                    "status": "authorized",
                }

        payment = Payment()

    monkeypatch.setattr(
        "app.api.routes.customer_uploaded_bills._get_razorpay_client",
        lambda: MockRazorpayClient(),
    )

    response = client.post(
        "/customer/uploaded-bills/verify-payment",
        headers=auth_headers(context["token"]),
        params={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Razorpay payment has not been captured."


def test_customer_uploaded_bill_rejects_duplicate_payment_id(
    client, db, monkeypatch
):
    context = create_customer_context(db)

    monkeypatch.setattr(
        "app.api.routes.customer_uploaded_bills.create_customer_bill_extraction",
        lambda **kwargs: None,
    )

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Duplicate Payment Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"duplicate-payment-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    upload_1 = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "bill-one.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    upload_2 = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "bill-two.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    assert upload_1.status_code == 201
    assert upload_2.status_code == 201

    bill_1 = upload_1.json()
    bill_2 = upload_2.json()

    order_id_1 = bill_1["razorpay_order_id"]
    order_id_2 = bill_2["razorpay_order_id"]

    payment_id = f"pay_test_{uuid4().hex[:12]}"

    signature_1 = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{order_id_1}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    class MockRazorpayClient:
        class Utility:
            @staticmethod
            def verify_payment_signature(_payload):
                return None

        utility = Utility()

        class Payment:
            @staticmethod
            def fetch(_payment_id):
                return {
                    "id": payment_id,
                    "order_id": order_id_1,
                    "amount": 900,
                    "currency": "INR",
                    "status": "captured",
                }

        payment = Payment()

    monkeypatch.setattr(
        "app.api.routes.customer_uploaded_bills._get_razorpay_client",
        lambda: MockRazorpayClient(),
    )

    first_response = client.post(
        "/customer/uploaded-bills/verify-payment",
        headers=auth_headers(context["token"]),
        params={
            "razorpay_order_id": order_id_1,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature_1,
        },
    )

    assert first_response.status_code == 200
    assert first_response.json()["payment_status"] == "paid"

    signature_2 = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{order_id_2}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/customer/uploaded-bills/verify-payment",
        headers=auth_headers(context["token"]),
        params={
            "razorpay_order_id": order_id_2,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature_2,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Razorpay payment does not belong to this order."


def test_customer_uploaded_bill_does_not_create_retailer_billing_records(
    client, db
):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Data Isolation Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"data-isolation-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    from app.models.invoice import Invoice
    from app.models.invoice_item import InvoiceItem
    from app.models.product_ownership import ProductOwnership

    invoice_count_before = db.query(Invoice).count()
    invoice_item_count_before = db.query(InvoiceItem).count()
    ownership_count_before = db.query(ProductOwnership).count()

    upload_response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "isolated-bill.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    invoice_count_after = db.query(Invoice).count()
    invoice_item_count_after = db.query(InvoiceItem).count()
    ownership_count_after = db.query(ProductOwnership).count()

    assert invoice_count_after == invoice_count_before
    assert invoice_item_count_after == invoice_item_count_before
    assert ownership_count_after == ownership_count_before

    uploaded_bill = upload_response.json()

    assert uploaded_bill["bill_id"].startswith("CB")
    assert uploaded_bill["amount"] == "9.00"
    assert uploaded_bill["status"] == "payment_pending"


def test_customer_uploaded_bill_list_returns_only_current_customer_bills(
    client, db
):
    context_1 = create_customer_context(db)

    create_customer_response_1 = client.post(
        "/customers",
        headers=auth_headers(context_1["token"]),
        json={
            "full_name": "List Customer One",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"list-one-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response_1.status_code == 201

    first_upload = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context_1["token"]),
        files={
            "file": (
                "first.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    second_upload = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context_1["token"]),
        files={
            "file": (
                "second.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    assert first_upload.status_code == 201
    assert second_upload.status_code == 201

    context_2 = create_customer_context(db)

    create_customer_response_2 = client.post(
        "/customers",
        headers=auth_headers(context_2["token"]),
        json={
            "full_name": "List Customer Two",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"list-two-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response_2.status_code == 201

    other_customer_upload = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context_2["token"]),
        files={
            "file": (
                "other.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    assert other_customer_upload.status_code == 201

    response = client.get(
        "/customer/uploaded-bills",
        headers=auth_headers(context_1["token"]),
    )

    assert response.status_code == 200

    bills = response.json()

    assert len(bills) == 2

    returned_bill_ids = [bill["bill_id"] for bill in bills]

    assert second_upload.json()["bill_id"] in returned_bill_ids
    assert first_upload.json()["bill_id"] in returned_bill_ids
    assert other_customer_upload.json()["bill_id"] not in returned_bill_ids

    assert bills[0]["bill_id"] == second_upload.json()["bill_id"]


def test_customer_uploaded_bill_get_and_ownership_protection(client, db):
    context_1 = create_customer_context(db)

    create_customer_response_1 = client.post(
        "/customers",
        headers=auth_headers(context_1["token"]),
        json={
            "full_name": "Get Bill Customer One",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"get-bill-one-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response_1.status_code == 201

    upload_response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context_1["token"]),
        files={
            "file": (
                "retrieval.pdf",
                b"%PDF-1.4\n1 0 obj\n",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    bill = upload_response.json()
    bill_id = bill["bill_id"]

    get_response = client.get(
        f"/customer/uploaded-bills/{bill_id}",
        headers=auth_headers(context_1["token"]),
    )

    assert get_response.status_code == 200
    assert get_response.json()["bill_id"] == bill_id
    assert get_response.json()["original_filename"] == "retrieval.pdf"

    context_2 = create_customer_context(db)

    create_customer_response_2 = client.post(
        "/customers",
        headers=auth_headers(context_2["token"]),
        json={
            "full_name": "Get Bill Customer Two",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"get-bill-two-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response_2.status_code == 201

    unauthorized_get = client.get(
        f"/customer/uploaded-bills/{bill_id}",
        headers=auth_headers(context_2["token"]),
    )

    assert unauthorized_get.status_code == 404
    assert unauthorized_get.json()["detail"] == "Uploaded bill not found."


def test_customer_uploaded_bill_download_and_ownership_protection(
    client, db
):
    context_1 = create_customer_context(db)

    create_customer_response_1 = client.post(
        "/customers",
        headers=auth_headers(context_1["token"]),
        json={
            "full_name": "Download Bill Customer One",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"download-one-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response_1.status_code == 201

    pdf_content = b"%PDF-1.4\nCustomer uploaded bill test content\n"

    upload_response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context_1["token"]),
        files={
            "file": (
                "download-test.pdf",
                pdf_content,
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    bill_data = upload_response.json()
    bill_id = bill_data["bill_id"]

    download_response = client.get(
        f"/customer/uploaded-bills/{bill_id}/download",
        headers=auth_headers(context_1["token"]),
    )

    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"
    assert download_response.content == pdf_content

    content_disposition = download_response.headers.get(
        "content-disposition",
        "",
    )

    assert "download-test.pdf" in content_disposition

    context_2 = create_customer_context(db)

    create_customer_response_2 = client.post(
        "/customers",
        headers=auth_headers(context_2["token"]),
        json={
            "full_name": "Download Bill Customer Two",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"download-two-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response_2.status_code == 201

    unauthorized_download = client.get(
        f"/customer/uploaded-bills/{bill_id}/download",
        headers=auth_headers(context_2["token"]),
    )

    assert unauthorized_download.status_code == 404
    assert unauthorized_download.json()["detail"] == "Uploaded bill not found."


def test_customer_uploaded_bill_confirmation_rejects_non_bill(client, db):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Confirmation Non Bill Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"confirmation-non-bill-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    upload_response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "resume.pdf",
                b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    uploaded_bill = upload_response.json()

    from app.models.customer_bill_extraction import CustomerBillExtraction
    from app.models.customer_uploaded_bill import CustomerUploadedBill

    bill = (
        db.query(CustomerUploadedBill)
        .filter(
            CustomerUploadedBill.bill_id == uploaded_bill["bill_id"]
        )
        .one()
    )

    extraction = CustomerBillExtraction(
        uploaded_bill_id=bill.id,
        status="extracted",
        raw_text="This is a resume document.",
        structured_data=None,
        document_status="not_bill",
        validation_score=2,
        validation_reasons=[
            "Product or item information found."
        ],
        digibill_eligible=False,
        page_count=1,
        extraction_engine="pypdf",
        extraction_model=None,
    )

    db.add(extraction)
    db.commit()

    response = client.get(
        f"/customer/uploaded-bills/{uploaded_bill['bill_id']}/confirmation",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "This uploaded document is not eligible for DigiBill creation."
    )


def test_customer_uploaded_bill_confirmation_returns_eligible_bill(client, db):
    context = create_customer_context(db)

    create_customer_response = client.post(
        "/customers",
        headers=auth_headers(context["token"]),
        json={
            "full_name": "Eligible Confirmation Customer",
            "phone_number": f"8{uuid4().hex[:9]}",
            "email": f"eligible-confirmation-{uuid4().hex[:8]}@example.com",
        },
    )

    assert create_customer_response.status_code == 201

    upload_response = client.post(
        "/customer/uploaded-bills",
        headers=auth_headers(context["token"]),
        files={
            "file": (
                "invoice.pdf",
                b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 201

    uploaded_bill = upload_response.json()

    from app.models.customer_bill_extraction import CustomerBillExtraction
    from app.models.customer_uploaded_bill import CustomerUploadedBill

    bill = (
        db.query(CustomerUploadedBill)
        .filter(
            CustomerUploadedBill.bill_id == uploaded_bill["bill_id"]
        )
        .one()
    )

    structured_data = {
        "retailer": {
            "name": "SHARMA ELECTRONICS",
            "address": "Delhi, India",
            "phone": "9876543210",
            "email": "sales@sharmaelectronics.example",
            "gstin": "07ABCDE1234F1Z5",
        },
        "customer": {
            "name": "Sumit Kumar",
            "phone": "9876500000",
            "email": "sumit@example.com",
            "address": "Delhi, India",
        },
        "invoice_number": "SE-2026-00987",
        "invoice_date": "2026-09-20",
        "products": [
            {
                "product_name": "Samsung Galaxy S25",
                "brand": "Samsung",
                "model_number": "SM-S931B",
                "serial_number": "SN123456789",
                "quantity": "1",
                "unit_price": "79999",
                "discount": "0",
                "tax_amount": "14400",
                "total_amount": "79999",
            }
        ],
        "totals": {
            "subtotal": "79999",
            "discount": "0",
            "tax_amount": "14400",
            "total_amount": "94399",
            "amount_paid": "94399",
            "amount_due": "0",
        },
        "payment": {
            "payment_method": "UPI",
            "transaction_reference": "UPI202609200001",
            "paid_amount": "94399",
            "payment_status": "paid",
        },
        "warranty": {
            "mentioned": "yes",
            "provider": "Samsung",
            "warranty_type": "Manufacturer Warranty",
            "duration": "1 Year",
            "duration_value": "1",
            "duration_unit": "years",
            "start_date": "2026-09-20",
            "end_date": "2027-09-20",
            "registration_number": None,
            "terms": "1 Year Manufacturer Warranty",
        },
        "confidence_scores": {
            "invoice_number": {
                "level": "high",
                "reason": "Invoice number clearly identified.",
            }
        },
        "extraction_notes": [],
    }

    extraction = CustomerBillExtraction(
        uploaded_bill_id=bill.id,
        status="extracted",
        raw_text="SHARMA ELECTRONICS\nInvoice No: SE-2026-00987",
        structured_data=structured_data,
        document_status="bill",
        validation_score=13,
        validation_reasons=[
            "Invoice number found.",
            "Invoice date found.",
            "Product or item information found.",
            "Quantity information found.",
            "Financial totals found.",
            "GST or tax information found.",
            "Payment information found.",
            "Purchase or invoice terms found.",
        ],
        digibill_eligible=True,
        page_count=1,
        extraction_engine="pypdf",
        extraction_model="local-rules-v1",
    )

    db.add(extraction)
    db.commit()

    response = client.get(
        f"/customer/uploaded-bills/{uploaded_bill['bill_id']}/confirmation",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["bill_id"] == uploaded_bill["bill_id"]
    assert data["eligible"] is True

    assert data["retailer"]["name"] == "SHARMA ELECTRONICS"
    assert data["retailer"]["gstin"] == "07ABCDE1234F1Z5"

    assert data["customer"]["name"] == "Sumit Kumar"

    assert data["invoice_number"] == "SE-2026-00987"
    assert data["invoice_date"] == "2026-09-20"

    assert len(data["products"]) == 1
    assert data["products"][0]["product_name"] == "Samsung Galaxy S25"
    assert data["products"][0]["brand"] == "Samsung"
    assert data["products"][0]["model_number"] == "SM-S931B"
    assert data["products"][0]["serial_number"] == "SN123456789"

    assert data["totals"]["total_amount"] == "94399"
    assert data["totals"]["amount_paid"] == "94399"
    assert data["totals"]["amount_due"] == "0"

    assert data["payment"]["payment_method"] == "UPI"
    assert data["payment"]["payment_status"] == "paid"

    assert data["warranty"]["mentioned"] == "yes"
    assert data["warranty"]["provider"] == "Samsung"
    assert data["warranty"]["duration"] == "1 Year"
    assert data["warranty"]["duration_value"] == "1"
    assert data["warranty"]["duration_unit"] == "years"
    assert data["warranty"]["start_date"] == "2026-09-20"
    assert data["warranty"]["end_date"] == "2027-09-20"


def _create_eligible_digibill_test_data(db, customer):
    from datetime import date
    from app.models.customer_bill_extraction import CustomerBillExtraction
    from app.models.customer_uploaded_bill import CustomerUploadedBill

    uploaded_bill = CustomerUploadedBill(
        bill_id=f"CBB{uuid4().hex[:10].upper()}",
        customer_id=customer.id,
        original_filename="eligible-invoice.pdf",
        storage_path="uploads/customer-bills/test-eligible.pdf",
        content_type="application/pdf",
        file_size=1024,
        amount=0,
        payment_status="paid",
        status="completed",
    )
    db.add(uploaded_bill)
    db.flush()

    extraction = CustomerBillExtraction(
        uploaded_bill_id=uploaded_bill.id,
        status="completed",
        raw_text="SHARMA ELECTRONICS Invoice SE-2026-00987",
        structured_data={
            "retailer": {
                "name": "SHARMA ELECTRONICS",
                "address": "Delhi",
                "phone": "9999999999",
                "email": "sales@example.com",
                "gstin": "07ABCDE1234F1Z5",
            },
            "customer": {
                "name": "DigiBill Test Customer",
                "phone": "8888888888",
                "email": "customer@example.com",
                "address": "Delhi",
            },
            "invoice_number": "SE-2026-00987",
            "invoice_date": "2026-09-20",
            "products": [
                {
                    "product_name": "Samsung Galaxy S25",
                    "brand": "Samsung",
                    "model_number": "SM-S931B",
                    "serial_number": "SN123456",
                    "quantity": 1,
                    "unit_price": 84999,
                    "discount": 1000,
                    "tax_amount": 14400,
                    "total_amount": 94399,
                }
            ],
            "totals": {
                "subtotal": 84999,
                "discount": 1000,
                "tax_amount": 14400,
                "total_amount": 94399,
                "amount_paid": 94399,
                "amount_due": 0,
            },
            "payment": {
                "payment_method": "UPI",
                "transaction_reference": "UPI123456",
                "paid_amount": 94399,
                "payment_status": "paid",
            },
            "warranty": {
                "mentioned": "yes",
                "provider": "Samsung",
                "warranty_type": "Manufacturer Warranty",
                "duration": "1 Year",
                "duration_value": 1,
                "duration_unit": "years",
                "start_date": "2026-09-20",
                "end_date": "2027-09-20",
                "registration_number": "WARRANTY123",
                "terms": "Standard manufacturer warranty terms.",
            },
            "confidence_scores": {},
            "extraction_notes": [],
        },
        document_status="bill",
        validation_score=13,
        validation_reasons=["Invoice contains bill information."],
        digibill_eligible=True,
    )
    db.add(extraction)
    db.commit()

    return uploaded_bill


def test_customer_uploaded_bill_confirm_creates_digibill(client, db):
    from app.models.customer import Customer
    from app.models.customer_digibill import CustomerDigiBill

    context = create_customer_context(db)

    customer = Customer(
        user_id=context["user"].id,
        customer_id=f"9{uuid4().int % 10**10:010d}",
        full_name="DigiBill API Customer",
        phone_number=f"8{uuid4().hex[:9]}",
        email=f"api-{uuid4().hex[:8]}@example.com",
        status="active",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    uploaded_bill = _create_eligible_digibill_test_data(db, customer)

    response = client.post(
        f"/customer/uploaded-bills/{uploaded_bill.bill_id}/confirm",
        headers={"Authorization": f"Bearer {context['token']}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["digibill_id"].startswith("DB-")
    assert data["uploaded_bill_id"] == str(uploaded_bill.id)
    assert data["customer_id"] == str(customer.id)
    assert data["invoice_number"] == "SE-2026-00987"
    assert data["status"] == "confirmed"

    digibill = (
        db.query(CustomerDigiBill)
        .filter(
            CustomerDigiBill.uploaded_bill_id == uploaded_bill.id
        )
        .one()
    )

    assert digibill.customer_id == customer.id
    assert digibill.digibill_id == data["digibill_id"]


def test_customer_uploaded_bill_confirm_is_idempotent(client, db):
    context = create_customer_context(db)

    from app.models.customer import Customer

    customer = Customer(
        user_id=context["user"].id,
        customer_id=f"9{uuid4().int % 10**10:010d}",
        full_name="DigiBill Idempotent Customer",
        phone_number=f"8{uuid4().hex[:9]}",
        email=f"idempotent-{uuid4().hex[:8]}@example.com",
        status="active",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    uploaded_bill = _create_eligible_digibill_test_data(db, customer)

    first = client.post(
        f"/customer/uploaded-bills/{uploaded_bill.bill_id}/confirm",
        headers={"Authorization": f"Bearer {context['token']}"},
    )

    second = client.post(
        f"/customer/uploaded-bills/{uploaded_bill.bill_id}/confirm",
        headers={"Authorization": f"Bearer {context['token']}"},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json()["digibill_id"] == second.json()["digibill_id"]


def test_customer_uploaded_bill_confirm_rejects_non_bill(client, db):
    from app.models.customer import Customer
    from app.models.customer_bill_extraction import CustomerBillExtraction
    from app.models.customer_uploaded_bill import CustomerUploadedBill

    context = create_customer_context(db)

    customer = Customer(
        user_id=context["user"].id,
        customer_id=f"9{uuid4().int % 10**10:010d}",
        full_name="Non Bill Customer",
        phone_number=f"8{uuid4().hex[:9]}",
        email=f"nonbill-{uuid4().hex[:8]}@example.com",
        status="active",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    uploaded_bill = CustomerUploadedBill(
        bill_id=f"CBB{uuid4().hex[:10].upper()}",
        customer_id=customer.id,
        original_filename="resume.pdf",
        storage_path="uploads/customer-bills/test-resume.pdf",
        content_type="application/pdf",
        file_size=1024,
        amount=0,
        payment_status="paid",
        status="completed",
    )
    db.add(uploaded_bill)
    db.flush()

    extraction = CustomerBillExtraction(
        uploaded_bill_id=uploaded_bill.id,
        status="completed",
        raw_text="Resume document",
        structured_data={},
        document_status="not_bill",
        validation_score=2,
        validation_reasons=["Document does not contain bill information."],
        digibill_eligible=False,
    )
    db.add(extraction)
    db.commit()

    response = client.post(
        f"/customer/uploaded-bills/{uploaded_bill.bill_id}/confirm",
        headers={"Authorization": f"Bearer {context['token']}"},
    )

    assert response.status_code == 422
    assert "not eligible" in response.json()["detail"].lower()


def test_customer_uploaded_bill_confirm_rejects_wrong_customer(client, db):
    from app.models.customer import Customer

    first_context = create_customer_context(db)

    first_customer = Customer(
        user_id=first_context["user"].id,
        customer_id=f"9{uuid4().int % 10**10:010d}",
        full_name="First Customer",
        phone_number=f"8{uuid4().hex[:9]}",
        email=f"first-{uuid4().hex[:8]}@example.com",
        status="active",
    )
    db.add(first_customer)
    db.commit()
    db.refresh(first_customer)

    uploaded_bill = _create_eligible_digibill_test_data(
        db,
        first_customer,
    )

    second_context = create_customer_context(db)

    second_customer = Customer(
        user_id=second_context["user"].id,
        customer_id=f"9{uuid4().int % 10**10:010d}",
        full_name="Second Customer",
        phone_number=f"8{uuid4().hex[:9]}",
        email=f"second-{uuid4().hex[:8]}@example.com",
        status="active",
    )
    db.add(second_customer)
    db.commit()

    response = client.post(
        f"/customer/uploaded-bills/{uploaded_bill.bill_id}/confirm",
        headers={"Authorization": f"Bearer {second_context['token']}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Uploaded bill not found."
