from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.customer_bill_extraction import CustomerBillExtraction
from app.models.customer_digibill import CustomerDigiBill
from app.models.customer_uploaded_bill import CustomerUploadedBill


def _resolve_storage_path(storage_path: str) -> Path:
    path = Path(storage_path)

    if path.is_absolute():
        return path

    return Path(__file__).resolve().parents[2] / path


def delete_uploaded_bill(
    db: Session,
    uploaded_bill: CustomerUploadedBill,
) -> None:
    """
    Permanently delete a customer-uploaded bill and its extraction record.

    This is intended for documents that are explicitly classified as
    NOT_BILL or have expired their uncertain-review retention period.

    The physical PDF is removed as part of the same application operation.
    """

    # A bill that has already produced a DigiBill is permanent.
    digibill = (
        db.query(CustomerDigiBill)
        .filter(
            CustomerDigiBill.uploaded_bill_id
            == uploaded_bill.id
        )
        .first()
    )

    if digibill is not None:
        return

    extraction = (
        db.query(CustomerBillExtraction)
        .filter(
            CustomerBillExtraction.uploaded_bill_id
            == uploaded_bill.id
        )
        .first()
    )

    storage_path = _resolve_storage_path(
        uploaded_bill.storage_path
    )

    if storage_path.exists() and storage_path.is_file():
        storage_path.unlink()

    if extraction is not None:
        db.delete(extraction)

    db.delete(uploaded_bill)

    db.flush()


def is_uncertain_review_expired(
    uploaded_bill: CustomerUploadedBill,
    now: Optional[datetime] = None,
) -> bool:
    if uploaded_bill.review_deadline_at is None:
        return False

    if now is None:
        now = datetime.now(timezone.utc)

    deadline = uploaded_bill.review_deadline_at

    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    return deadline <= now


def cleanup_expired_uncertain_bills(
    db: Session,
    now: Optional[datetime] = None,
) -> int:
    """
    Permanently delete customer-uploaded bills whose uncertain-review
    deadline has expired.

    Returns the number of bills successfully selected for cleanup.
    """

    if now is None:
        now = datetime.now(timezone.utc)

    uncertain_bills = (
        db.query(CustomerUploadedBill)
        .join(
            CustomerBillExtraction,
            CustomerBillExtraction.uploaded_bill_id
            == CustomerUploadedBill.id,
        )
        .filter(
            CustomerBillExtraction.document_status == "uncertain",
            CustomerUploadedBill.review_deadline_at.isnot(None),
            CustomerUploadedBill.review_deadline_at <= now,
        )
        .all()
    )

    deleted_count = 0

    for uploaded_bill in uncertain_bills:
        before_id = uploaded_bill.id

        delete_uploaded_bill(
            db,
            uploaded_bill,
        )

        # The cleanup function can encounter a DigiBill created
        # concurrently. The delete service protects against that.
        if (
            db.query(CustomerUploadedBill)
            .filter(CustomerUploadedBill.id == before_id)
            .first()
            is None
        ):
            deleted_count += 1

    db.commit()

    return deleted_count
