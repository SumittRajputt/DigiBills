import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer_bill_extraction import CustomerBillExtraction
from app.models.customer_digibill import CustomerDigiBill
from app.models.customer_uploaded_bill import CustomerUploadedBill
from app.services.customer_warranty_confirmation_service import (
    prepare_warranty_confirmation,
)

from app.schemas.customer_bill_extraction import (
    CustomerBillExtraction as CustomerBillExtractionSchema,
)


def generate_digibill_id() -> str:
    return f"DB-{uuid.uuid4().hex[:12].upper()}"


def get_digibill_by_uploaded_bill_id(
    db: Session,
    uploaded_bill_id: uuid.UUID,
) -> Optional[CustomerDigiBill]:
    statement = select(CustomerDigiBill).where(
        CustomerDigiBill.uploaded_bill_id == uploaded_bill_id
    )

    return db.execute(statement).scalar_one_or_none()


def get_digibill_by_id(
    db: Session,
    digibill_id: str,
) -> Optional[CustomerDigiBill]:
    statement = select(CustomerDigiBill).where(
        CustomerDigiBill.digibill_id == digibill_id,
    )

    return db.execute(statement).scalar_one_or_none()


def create_customer_digibill(
    db: Session,
    uploaded_bill: CustomerUploadedBill,
    customer_id: uuid.UUID,
    customer_has_warranty: str = "unknown",
    duration_value=None,
    duration_unit=None,
) -> CustomerDigiBill:
    if uploaded_bill.customer_id != customer_id:
        raise ValueError(
            "Uploaded bill does not belong to this customer."
        )

    extraction = db.execute(
        select(CustomerBillExtraction).where(
            CustomerBillExtraction.uploaded_bill_id
            == uploaded_bill.id
        )
    ).scalar_one_or_none()

    if extraction is None:
        raise ValueError(
            "Bill extraction is not available."
        )

    if not extraction.digibill_eligible:
        raise ValueError(
            "This uploaded document is not eligible for DigiBill creation."
        )

    if not extraction.structured_data:
        raise ValueError(
            "Structured bill data is not available."
        )

    existing = get_digibill_by_uploaded_bill_id(
        db=db,
        uploaded_bill_id=uploaded_bill.id,
    )

    if existing is not None:
        return existing

    try:
        structured_data = CustomerBillExtractionSchema.model_validate(
            extraction.structured_data
        )
    except Exception as exc:
        raise ValueError(
            "Stored bill data is invalid and cannot create a DigiBill."
        ) from exc

    warranty_confirmation = prepare_warranty_confirmation(
        extraction=structured_data,
        customer_has_warranty=(
            True
            if customer_has_warranty == "yes"
            else False
            if customer_has_warranty == "no"
            else None
        ),
        duration_value=duration_value,
        duration_unit=duration_unit,
    )

    now = datetime.now(timezone.utc)

    digibill = CustomerDigiBill(
        digibill_id=generate_digibill_id(),
        uploaded_bill_id=uploaded_bill.id,
        customer_id=customer_id,
        invoice_number=structured_data.invoice_number,
        invoice_date=structured_data.invoice_date,
        retailer_data=structured_data.retailer.model_dump(mode="json"),
        customer_data=structured_data.customer.model_dump(mode="json"),
        products=[
            product.model_dump(mode="json")
            for product in structured_data.products
        ],
        totals=structured_data.totals.model_dump(mode="json"),
        payment=structured_data.payment.model_dump(mode="json"),
        warranty_evidence={
            **structured_data.warranty.model_dump(mode="json"),
            "customer_confirmation": {
                "has_warranty": warranty_confirmation.has_warranty,
                "duration_value": (
                    str(warranty_confirmation.duration_value)
                    if warranty_confirmation.duration_value is not None
                    else None
                ),
                "duration_unit": warranty_confirmation.duration_unit,
                "source": "customer_confirmation",
            },
            "final": {
                "has_warranty": warranty_confirmation.has_warranty,
                "provider": warranty_confirmation.provider,
                "warranty_type": warranty_confirmation.warranty_type,
                "start_date": (
                    warranty_confirmation.start_date.isoformat()
                    if warranty_confirmation.start_date is not None
                    else None
                ),
                "duration_value": (
                    str(warranty_confirmation.duration_value)
                    if warranty_confirmation.duration_value is not None
                    else None
                ),
                "duration_unit": warranty_confirmation.duration_unit,
                "end_date": (
                    warranty_confirmation.end_date.isoformat()
                    if warranty_confirmation.end_date is not None
                    else None
                ),
                "warranty_number": warranty_confirmation.warranty_number,
                "important_terms": warranty_confirmation.important_terms,
            },
        },
        confidence_scores={
            key: value.model_dump(mode="json")
            for key, value in structured_data.confidence_scores.items()
        },
        extraction_notes=structured_data.extraction_notes,
        status="confirmed",
        confirmed_at=now,
        created_at=now,
        updated_at=now,
    )

    db.add(digibill)
    db.flush()

    return digibill
