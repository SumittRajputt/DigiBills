from decimal import Decimal
from uuid import uuid4

import razorpay

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.core.config import settings
from app.api.dependencies import get_db
from app.models.customer_uploaded_bill import CustomerUploadedBill
from app.models.customer_bill_extraction import CustomerBillExtraction
from app.models.user import User
from app.services.customer_digibill_service import create_customer_digibill
from app.schemas.customer_digibill_response import CustomerDigiBillResponse
from app.schemas.customer_uploaded_bill import CustomerUploadedBillResponse
from app.schemas.customer_bill_validation_response import (
    CustomerBillValidationResponse,
)
from app.schemas.customer_bill_confirmation_response import (
    CustomerBillConfirmationResponse,
)
from app.schemas.customer_bill_extraction import (
    CustomerBillExtraction as CustomerBillExtractionSchema,
)
from app.schemas.customer_warranty_confirmation_response import (
    CustomerWarrantyConfirmationResponse,
)
from app.services.customer_service import get_customer_by_user_id
from app.services.customer_uploaded_bill_service import save_customer_bill
from app.services.customer_bill_extraction_service import (
    create_customer_bill_extraction,
)
from app.services.customer_warranty_confirmation_service import (
    prepare_warranty_confirmation,
)
from app.services.subscription_service import get_active_subscription_for_customer


router = APIRouter(
    prefix="/customer/uploaded-bills",
    tags=["Customer Uploaded Bills"],
)


def _get_razorpay_client():
    if (
        not settings.razorpay_key_id
        or not settings.razorpay_key_secret
    ):
        raise RuntimeError(
            "Razorpay credentials are not configured."
        )

    return razorpay.Client(
        auth=(
            settings.razorpay_key_id,
            settings.razorpay_key_secret,
        )
    )


def _generate_bill_id() -> str:
    return f"CB{uuid4().hex[:12].upper()}"


@router.get(
    "",
    response_model=list[CustomerUploadedBillResponse],
)
def list_customer_uploaded_bills(
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is not active.",
        )

    return (
        db.query(CustomerUploadedBill)
        .filter(
            CustomerUploadedBill.customer_id == customer.id,
        )
        .order_by(
            CustomerUploadedBill.uploaded_at.desc(),
        )
        .all()
    )


@router.get(
    "/{bill_id}/download",
)
def download_customer_uploaded_bill(
    bill_id: str,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    from fastapi.responses import FileResponse
    from pathlib import Path

    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is not active.",
        )

    uploaded_bill = (
        db.query(CustomerUploadedBill)
        .filter(
            CustomerUploadedBill.bill_id == bill_id,
            CustomerUploadedBill.customer_id == customer.id,
        )
        .first()
    )

    if uploaded_bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded bill not found.",
        )

    file_path = Path(uploaded_bill.storage_path)

    if not file_path.is_absolute():
        file_path = Path(__file__).resolve().parents[3] / file_path

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded bill file not found.",
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=uploaded_bill.original_filename,
    )


@router.get(
    "/{bill_id}",
    response_model=CustomerUploadedBillResponse,
)
def get_customer_uploaded_bill(
    bill_id: str,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is not active.",
        )

    uploaded_bill = (
        db.query(CustomerUploadedBill)
        .filter(
            CustomerUploadedBill.bill_id == bill_id,
            CustomerUploadedBill.customer_id == customer.id,
        )
        .first()
    )

    if uploaded_bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded bill not found.",
        )

    return uploaded_bill


@router.get(
    "/{bill_id}/validation",
    response_model=CustomerBillValidationResponse,
)
def get_customer_bill_validation(
    bill_id: str,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is not active.",
        )

    uploaded_bill = (
        db.query(CustomerUploadedBill)
        .filter(
            CustomerUploadedBill.bill_id == bill_id,
            CustomerUploadedBill.customer_id == customer.id,
        )
        .first()
    )

    if uploaded_bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded bill not found.",
        )

    extraction = (
        db.query(CustomerBillExtraction)
        .filter(
            CustomerBillExtraction.uploaded_bill_id
            == uploaded_bill.id,
        )
        .first()
    )

    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill extraction has not been completed yet.",
        )

    return CustomerBillValidationResponse(
        bill_id=uploaded_bill.bill_id,
        document_status=extraction.document_status,
        validation_score=extraction.validation_score,
        validation_reasons=extraction.validation_reasons or [],
        digibill_eligible=bool(
            extraction.digibill_eligible
        ),
    )


@router.get(
    "/{bill_id}/confirmation",
    response_model=CustomerBillConfirmationResponse,
)
def get_customer_bill_confirmation(
    bill_id: str,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is not active.",
        )

    uploaded_bill = (
        db.query(CustomerUploadedBill)
        .filter(
            CustomerUploadedBill.bill_id == bill_id,
            CustomerUploadedBill.customer_id == customer.id,
        )
        .first()
    )

    if uploaded_bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded bill not found.",
        )

    extraction = (
        db.query(CustomerBillExtraction)
        .filter(
            CustomerBillExtraction.uploaded_bill_id
            == uploaded_bill.id,
        )
        .first()
    )

    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill extraction has not been completed yet.",
        )

    if not extraction.digibill_eligible:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "This uploaded document is not eligible "
                "for DigiBill creation."
            ),
        )

    if not extraction.structured_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Structured bill information is not available."
            ),
        )

    try:
        extracted_data = CustomerBillExtractionSchema.model_validate(
            extraction.structured_data
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Stored bill extraction data is invalid.",
        ) from exc

    # Starting the review flow starts the 24-hour review window
    # for uncertain documents only.
    if (
        extraction.document_status == "uncertain"
        and uploaded_bill.review_deadline_at is None
    ):
        uploaded_bill.review_deadline_at = (
            datetime.now(timezone.utc) + timedelta(hours=24)
        )
        db.commit()
        db.refresh(uploaded_bill)

    return CustomerBillConfirmationResponse(
        bill_id=uploaded_bill.bill_id,
        eligible=True,
        retailer=extracted_data.retailer.model_dump(
            mode="json"
        ),
        customer=extracted_data.customer.model_dump(
            mode="json"
        ),
        invoice_number=extracted_data.invoice_number,
        invoice_date=extracted_data.invoice_date,
        products=[
            product.model_dump(mode="json")
            for product in extracted_data.products
        ],
        totals=extracted_data.totals.model_dump(
            mode="json"
        ),
        payment=extracted_data.payment.model_dump(
            mode="json"
        ),
        warranty=extracted_data.warranty.model_dump(
            mode="json"
        ),
        confidence_scores={
            key: value.model_dump(mode="json")
            for key, value
            in extracted_data.confidence_scores.items()
        },
        extraction_notes=extracted_data.extraction_notes,
    )


@router.get(
    "/{bill_id}/warranty-confirmation",
    response_model=CustomerWarrantyConfirmationResponse,
)
def get_customer_warranty_confirmation(
    bill_id: str,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is not active.",
        )

    uploaded_bill = (
        db.query(CustomerUploadedBill)
        .filter(
            CustomerUploadedBill.bill_id == bill_id,
            CustomerUploadedBill.customer_id == customer.id,
        )
        .first()
    )

    if uploaded_bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded bill not found.",
        )

    extraction = (
        db.query(CustomerBillExtraction)
        .filter(
            CustomerBillExtraction.uploaded_bill_id == uploaded_bill.id,
        )
        .first()
    )

    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill extraction has not been completed yet.",
        )

    if not extraction.structured_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Structured bill information is not available.",
        )

    try:
        extracted_data = CustomerBillExtractionSchema.model_validate(
            extraction.structured_data
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Stored bill extraction data is invalid.",
        ) from exc

    confirmation = prepare_warranty_confirmation(
        extracted_data,
    )

    return CustomerWarrantyConfirmationResponse.model_validate(
        confirmation.model_dump()
    )


@router.post(
    "/{bill_id}/confirm",
    response_model=CustomerDigiBillResponse,
)
def confirm_customer_uploaded_bill(
    bill_id: str,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is not active.",
        )

    uploaded_bill = (
        db.query(CustomerUploadedBill)
        .filter(
            CustomerUploadedBill.bill_id == bill_id,
            CustomerUploadedBill.customer_id == customer.id,
        )
        .first()
    )

    if uploaded_bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded bill not found.",
        )

    try:
        digibill = create_customer_digibill(
            db=db,
            uploaded_bill=uploaded_bill,
            customer_id=customer.id,
        )
        db.commit()
        db.refresh(digibill)

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return CustomerDigiBillResponse(
        digibill_id=digibill.digibill_id,
        uploaded_bill_id=str(digibill.uploaded_bill_id),
        customer_id=str(digibill.customer_id),
        invoice_number=digibill.invoice_number,
        invoice_date=digibill.invoice_date,
        retailer=digibill.retailer_data,
        customer=digibill.customer_data,
        products=digibill.products,
        totals=digibill.totals,
        payment=digibill.payment,
        warranty_evidence=digibill.warranty_evidence,
        confidence_scores=digibill.confidence_scores,
        extraction_notes=digibill.extraction_notes,
        status=digibill.status,
        confirmed_at=digibill.confirmed_at,
        created_at=digibill.created_at,
        updated_at=digibill.updated_at,
    )


@router.post(
    "/verify-payment",
    response_model=CustomerUploadedBillResponse,
)
async def verify_customer_bill_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is not active.",
        )

    uploaded_bill = (
        db.query(CustomerUploadedBill)
        .filter(
            CustomerUploadedBill.razorpay_order_id
            == razorpay_order_id,
            CustomerUploadedBill.customer_id
            == customer.id,
        )
        .first()
    )

    if uploaded_bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded bill payment order not found.",
        )

    if uploaded_bill.amount != Decimal("9.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This uploaded bill does not require a ₹9 payment.",
        )

    if uploaded_bill.payment_status == "paid":
        if (
            uploaded_bill.razorpay_payment_id
            == razorpay_payment_id
        ):
            return uploaded_bill

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment for this uploaded bill has already been completed.",
        )

    if uploaded_bill.status != "payment_pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This uploaded bill is not awaiting payment.",
        )

    try:
        client = _get_razorpay_client()

        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )

        # Fetch the actual payment from Razorpay.
        payment = client.payment.fetch(razorpay_payment_id)


    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Razorpay payment signature.",
        ) from exc

    # Payment must belong to this Razorpay order.
    if payment.get("order_id") != razorpay_order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Razorpay payment does not belong to this order.",
        )

    # ₹9 = 900 paise.
    if int(payment.get("amount", 0)) != 900:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Razorpay payment amount is invalid.",
        )

    # Currency must be INR.
    if payment.get("currency") != "INR":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Razorpay payment currency is invalid.",
        )

    # Payment must be captured.
    if payment.get("status") != "captured":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Razorpay payment has not been captured.",
        )

    uploaded_bill.razorpay_payment_id = razorpay_payment_id
    uploaded_bill.transaction_reference = razorpay_payment_id
    uploaded_bill.payment_status = "paid"
    uploaded_bill.status = "completed"

    db.commit()
    db.refresh(uploaded_bill)

    try:
        create_customer_bill_extraction(
            db=db,
            uploaded_bill=uploaded_bill,
        )
        db.commit()
        db.refresh(uploaded_bill)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment was completed, but bill extraction could not be completed.",
        ) from exc

    return uploaded_bill


@router.post(
    "",
    response_model=CustomerUploadedBillResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_customer_bill(
    file: UploadFile = File(...),
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is not active.",
        )

    bill_id = _generate_bill_id()

    try:
        storage_path, file_size = await save_customer_bill(
            upload_file=file,
            bill_id=bill_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    subscription = get_active_subscription_for_customer(
        db,
        customer.id,
    )

    if subscription is not None:
        amount = Decimal("0.00")
        payment_status = "not_required"
        bill_status = "completed"
        razorpay_order_id = None
    else:
        amount = Decimal("9.00")
        payment_status = "pending"
        bill_status = "payment_pending"

        try:
            client = _get_razorpay_client()

            order = client.order.create(
                {
                    "amount": 900,
                    "currency": "INR",
                    "receipt": bill_id,
                    "notes": {
                        "purpose": "Customer Uploaded Bill",
                        "bill_id": bill_id,
                        "customer_id": str(customer.id),
                    },
                }
            )

            razorpay_order_id = order["id"]

        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to create Razorpay payment order.",
            ) from exc

    uploaded_bill = CustomerUploadedBill(
        bill_id=bill_id,
        customer_id=customer.id,
        original_filename=file.filename or "uploaded_bill.pdf",
        storage_path=storage_path,
        content_type="application/pdf",
        file_size=file_size,
        amount=amount,
        payment_status=payment_status,
        status=bill_status,
        razorpay_order_id=razorpay_order_id,
    )

    db.add(uploaded_bill)
    db.commit()
    db.refresh(uploaded_bill)

    if uploaded_bill.status == "completed":
        try:
            create_customer_bill_extraction(
                db=db,
                uploaded_bill=uploaded_bill,
            )
            db.commit()
            db.refresh(uploaded_bill)
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Bill was uploaded, but extraction could not be completed.",
            ) from exc

    return uploaded_bill
