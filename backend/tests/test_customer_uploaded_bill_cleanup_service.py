from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from app.models.customer import Customer
from app.models.customer_bill_extraction import CustomerBillExtraction
from app.models.customer_digibill import CustomerDigiBill
from app.models.customer_uploaded_bill import CustomerUploadedBill
from app.models.user import User
from app.services.customer_uploaded_bill_cleanup_service import (
    cleanup_expired_uncertain_bills,
    delete_uploaded_bill,
    is_uncertain_review_expired,
)


def create_test_customer(db):
    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
        status="active",
    )

    db.add(user)
    db.flush()

    customer = Customer(
        user_id=user.id,
        customer_id=f"9{uuid4().int % 10**10:010d}",
        full_name="Cleanup Test Customer",
        phone_number=f"8{uuid4().hex[:9]}",
        email=f"cleanup-{uuid4().hex[:8]}@example.com",
        status="active",
    )

    db.add(customer)
    db.flush()

    return customer


def create_test_uploaded_bill(
    db,
    customer,
    storage_path,
    review_deadline_at=None,
):
    uploaded_bill = CustomerUploadedBill(
        bill_id=f"CBB{uuid4().hex[:10].upper()}",
        customer_id=customer.id,
        original_filename="cleanup-test.pdf",
        storage_path=str(storage_path),
        content_type="application/pdf",
        file_size=1024,
        amount=Decimal("0.00"),
        payment_status="paid",
        status="completed",
        review_deadline_at=review_deadline_at,
    )

    db.add(uploaded_bill)
    db.flush()

    return uploaded_bill


def create_extraction(
    db,
    uploaded_bill,
    document_status="uncertain",
):
    extraction = CustomerBillExtraction(
        uploaded_bill_id=uploaded_bill.id,
        status="review_required",
        raw_text="Ambiguous product document",
        structured_data=None,
        document_status=document_status,
        validation_score=3,
        validation_reasons=["Product information found."],
        digibill_eligible=False,
    )

    db.add(extraction)
    db.flush()

    return extraction


def test_delete_uploaded_bill_removes_database_and_pdf(
    db,
    tmp_path,
):
    customer = create_test_customer(db)

    pdf_path = tmp_path / "delete-me.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nTEST\n%%EOF")

    uploaded_bill = create_test_uploaded_bill(
        db,
        customer,
        pdf_path,
    )

    extraction = create_extraction(
        db,
        uploaded_bill,
    )

    uploaded_bill_id = uploaded_bill.id
    extraction_id = extraction.id

    delete_uploaded_bill(
        db,
        uploaded_bill,
    )

    db.commit()

    assert not pdf_path.exists()

    assert (
        db.query(CustomerUploadedBill)
        .filter(CustomerUploadedBill.id == uploaded_bill_id)
        .first()
        is None
    )

    assert (
        db.query(CustomerBillExtraction)
        .filter(CustomerBillExtraction.id == extraction_id)
        .first()
        is None
    )


def test_uncertain_review_deadline_expiration():
    now = datetime(
        2026,
        9,
        20,
        12,
        0,
        tzinfo=timezone.utc,
    )

    class Bill:
        review_deadline_at = now + timedelta(hours=24)

    bill = Bill()

    assert (
        is_uncertain_review_expired(
            bill,
            now=now,
        )
        is False
    )

    assert (
        is_uncertain_review_expired(
            bill,
            now=now + timedelta(hours=23, minutes=59),
        )
        is False
    )

    assert (
        is_uncertain_review_expired(
            bill,
            now=now + timedelta(hours=24),
        )
        is True
    )


def test_uncertain_without_deadline_is_not_expired():
    class Bill:
        review_deadline_at = None

    assert (
        is_uncertain_review_expired(
            Bill(),
        )
        is False
    )


def test_cleanup_keeps_unexpired_uncertain_bill(
    db,
    tmp_path,
):
    customer = create_test_customer(db)

    now = datetime(
        2026,
        9,
        20,
        12,
        0,
        tzinfo=timezone.utc,
    )

    pdf_path = tmp_path / "keep-me.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nKEEP\n%%EOF")

    uploaded_bill = create_test_uploaded_bill(
        db,
        customer,
        pdf_path,
        review_deadline_at=now + timedelta(hours=1),
    )

    create_extraction(
        db,
        uploaded_bill,
        document_status="uncertain",
    )

    db.commit()

    deleted_count = cleanup_expired_uncertain_bills(
        db,
        now=now,
    )

    assert deleted_count == 0
    assert pdf_path.exists()

    remaining = (
        db.query(CustomerUploadedBill)
        .filter(
            CustomerUploadedBill.id == uploaded_bill.id
        )
        .first()
    )

    assert remaining is not None


def test_cleanup_deletes_expired_uncertain_bill(
    db,
    tmp_path,
):
    customer = create_test_customer(db)

    now = datetime(
        2026,
        9,
        20,
        12,
        0,
        tzinfo=timezone.utc,
    )

    pdf_path = tmp_path / "expired.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nEXPIRED\n%%EOF")

    uploaded_bill = create_test_uploaded_bill(
        db,
        customer,
        pdf_path,
        review_deadline_at=now - timedelta(seconds=1),
    )

    create_extraction(
        db,
        uploaded_bill,
        document_status="uncertain",
    )

    uploaded_bill_id = uploaded_bill.id

    db.commit()

    deleted_count = cleanup_expired_uncertain_bills(
        db,
        now=now,
    )

    assert deleted_count == 1
    assert not pdf_path.exists()

    assert (
        db.query(CustomerUploadedBill)
        .filter(CustomerUploadedBill.id == uploaded_bill_id)
        .first()
        is None
    )


def test_cleanup_does_not_delete_digibill_linked_bill(
    db,
    tmp_path,
):
    customer = create_test_customer(db)

    now = datetime(
        2026,
        9,
        20,
        12,
        0,
        tzinfo=timezone.utc,
    )

    pdf_path = tmp_path / "protected.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\\nPROTECTED\\n%%EOF")

    uploaded_bill = create_test_uploaded_bill(
        db,
        customer,
        pdf_path,
        review_deadline_at=now - timedelta(seconds=1),
    )

    create_extraction(
        db,
        uploaded_bill,
        document_status="bill",
    )

    digibill = CustomerDigiBill(
        digibill_id=f"DB-{uuid4().hex[:12].upper()}",
        uploaded_bill_id=uploaded_bill.id,
        customer_id=customer.id,
        invoice_number="TEST-001",
        retailer_data={},
        customer_data={},
        products=[],
        totals={},
        payment={},
        warranty_evidence={},
        confidence_scores={},
        extraction_notes=[],
        status="confirmed",
    )

    db.add(digibill)
    db.commit()

    deleted_count = cleanup_expired_uncertain_bills(
        db,
        now=now,
    )

    assert deleted_count == 0
    assert pdf_path.exists()

    remaining_bill = (
        db.query(CustomerUploadedBill)
        .filter(CustomerUploadedBill.id == uploaded_bill.id)
        .first()
    )

    assert remaining_bill is not None
