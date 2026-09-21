from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.models.customer import Customer
from app.models.customer_bill_extraction import CustomerBillExtraction
from app.models.customer_digibill import CustomerDigiBill
from app.models.customer_uploaded_bill import CustomerUploadedBill
from app.services.customer_digibill_service import (
    create_customer_digibill,
)


def create_test_customer(db):
    from app.models.user import User

    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
        status="active",
    )

    db.add(user)
    db.flush()

    customer = Customer(
        user_id=user.id,
        customer_id=f"9{uuid4().int % 10**10:010d}",
        full_name="DigiBill Test Customer",
        phone_number=f"8{uuid4().hex[:9]}",
        email=f"digibill-{uuid4().hex[:8]}@example.com",
        status="active",
    )

    db.add(customer)
    db.flush()

    return customer


def create_test_uploaded_bill(db, customer):
    uploaded_bill = CustomerUploadedBill(
        bill_id=f"CBB{uuid4().hex[:10].upper()}",
        customer_id=customer.id,
        original_filename="test-invoice.pdf",
        storage_path="uploads/customer-bills/test-invoice.pdf",
        content_type="application/pdf",
        file_size=1024,
        amount=Decimal("0.00"),
        payment_status="paid",
        status="completed",
    )

    db.add(uploaded_bill)
    db.flush()

    return uploaded_bill


def create_test_extraction(db, uploaded_bill):
    extraction = CustomerBillExtraction(
        uploaded_bill_id=uploaded_bill.id,
        status="extracted",
        raw_text="Test invoice",
        structured_data={
            "retailer": {
                "name": "SHARMA ELECTRONICS",
                "address": "Delhi",
                "phone": "9876543210",
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
                "transaction_reference": "UPI123456",
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
                    "reason": "Clearly identified",
                }
            },
            "extraction_notes": [],
        },
        document_status="bill",
        validation_score=13,
        validation_reasons=[
            "Invoice information found.",
            "Product information found.",
        ],
        digibill_eligible=True,
    )

    db.add(extraction)
    db.flush()

    return extraction


def test_create_customer_digibill(db):
    customer = create_test_customer(db)
    uploaded_bill = create_test_uploaded_bill(db, customer)
    create_test_extraction(db, uploaded_bill)

    digibill = create_customer_digibill(
        db=db,
        uploaded_bill=uploaded_bill,
        customer_id=customer.id,
    )

    db.commit()
    db.refresh(digibill)

    assert digibill.id is not None
    assert digibill.digibill_id.startswith("DB-")
    assert digibill.uploaded_bill_id == uploaded_bill.id
    assert digibill.customer_id == customer.id
    assert digibill.invoice_number == "SE-2026-00987"
    assert digibill.invoice_date.date() == date(2026, 9, 20)

    assert digibill.retailer_data["name"] == "SHARMA ELECTRONICS"
    assert digibill.customer_data["name"] == "DigiBill Test Customer"

    assert len(digibill.products) == 1
    assert digibill.products[0]["product_name"] == "Samsung Galaxy S25"

    assert digibill.totals["total_amount"] == "94399"
    assert digibill.payment["payment_method"] == "UPI"

    assert digibill.warranty_evidence["mentioned"] == "yes"
    assert digibill.status == "confirmed"


def test_create_customer_digibill_is_idempotent(db):
    customer = create_test_customer(db)
    uploaded_bill = create_test_uploaded_bill(db, customer)
    create_test_extraction(db, uploaded_bill)

    first = create_customer_digibill(
        db=db,
        uploaded_bill=uploaded_bill,
        customer_id=customer.id,
    )

    db.commit()

    second = create_customer_digibill(
        db=db,
        uploaded_bill=uploaded_bill,
        customer_id=customer.id,
    )

    assert second.id == first.id
    assert second.digibill_id == first.digibill_id

    count = (
        db.query(CustomerDigiBill)
        .filter(
            CustomerDigiBill.uploaded_bill_id
            == uploaded_bill.id
        )
        .count()
    )

    assert count == 1


def test_create_customer_digibill_rejects_non_bill(db):
    customer = create_test_customer(db)
    uploaded_bill = create_test_uploaded_bill(db, customer)

    extraction = CustomerBillExtraction(
        uploaded_bill_id=uploaded_bill.id,
        status="extracted",
        raw_text="This is a resume.",
        structured_data={
            "retailer": {},
            "customer": {},
            "invoice_number": None,
            "invoice_date": None,
            "products": [],
            "totals": {},
            "payment": {},
            "warranty": {
                "mentioned": "unclear"
            },
            "confidence_scores": {},
            "extraction_notes": [],
        },
        document_status="not_bill",
        validation_score=2,
        validation_reasons=[
            "Product or item information found."
        ],
        digibill_eligible=False,
    )

    db.add(extraction)
    db.commit()

    try:
        create_customer_digibill(
            db=db,
            uploaded_bill=uploaded_bill,
            customer_id=customer.id,
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == (
            "This uploaded document is not eligible "
            "for DigiBill creation."
        )
