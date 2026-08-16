from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentDetailResponse,
    PaymentRefundRequest,
)
from app.services.invoice_service import get_invoice_by_reference
from app.services.payment_service import (
    cancel_payment,
    create_payment,
    get_all_payments,
    get_invoice_payments,
    get_payment_by_reference,
    refund_payment,
)
from app.services.retailer_service import get_retailer_by_owner


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


def payment_to_response(payment):
    return PaymentDetailResponse(
        id=str(payment.id),
        payment_id=payment.payment_id,
        invoice_id=str(payment.invoice_id),
        amount=payment.amount,
        payment_method=payment.payment_method,
        payment_status=payment.payment_status,
        transaction_reference=payment.transaction_reference,
        paid_at=payment.paid_at,
        refund_amount=payment.refund_amount,
        refund_status=payment.refund_status,
        notes=payment.notes,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


@router.post(
    "",
    response_model=PaymentDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_endpoint(
    request: PaymentCreateRequest,
    current_user: User = Depends(
        require_permission("invoice.manage")
    ),
    db: Session = Depends(get_db),
):
    retailer = get_retailer_by_owner(
        db,
        current_user.id,
    )

    if retailer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found for this user.",
        )

    if retailer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Retailer is not active.",
        )

    invoice = get_invoice_by_reference(
        db,
        request.invoice_id,
    )

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if invoice.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    try:
        payment = create_payment(
            db=db,
            invoice=invoice,
            amount=request.amount,
            payment_method=request.payment_method,
            transaction_reference=request.transaction_reference,
            notes=request.notes,
            retailer_id=retailer.id,
            user_id=current_user.id,
        )

        return payment_to_response(payment)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[PaymentDetailResponse],
)
def list_payments(
    current_user: User = Depends(
        require_permission("invoice.view")
    ),
    db: Session = Depends(get_db),
):
    payments = get_all_payments(db)

    return [
        payment_to_response(payment)
        for payment in payments
    ]


@router.get(
    "/invoice/{invoice_id}",
    response_model=list[PaymentDetailResponse],
)
def get_invoice_payments_endpoint(
    invoice_id: str,
    current_user: User = Depends(
        require_permission("invoice.view")
    ),
    db: Session = Depends(get_db),
):
    retailer = get_retailer_by_owner(
        db,
        current_user.id,
    )

    if retailer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found for this user.",
        )

    invoice = get_invoice_by_reference(
        db,
        invoice_id,
    )

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if invoice.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    payments = get_invoice_payments(
        db,
        invoice.id,
    )

    return [
        payment_to_response(payment)
        for payment in payments
    ]


@router.get(
    "/{payment_id}",
    response_model=PaymentDetailResponse,
)
def get_payment_endpoint(
    payment_id: str,
    current_user: User = Depends(
        require_permission("invoice.view")
    ),
    db: Session = Depends(get_db),
):
    retailer = get_retailer_by_owner(
        db,
        current_user.id,
    )

    if retailer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found for this user.",
        )

    payment = get_payment_by_reference(
        db,
        payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    from sqlalchemy import select
    from app.models.invoice import Invoice

    invoice = db.execute(
        select(Invoice).where(
            Invoice.id == payment.invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if invoice.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    return payment_to_response(payment)


@router.post(
    "/{payment_id}/refund",
    response_model=PaymentDetailResponse,
)
def refund_payment_endpoint(
    payment_id: str,
    request: PaymentRefundRequest,
    current_user: User = Depends(
        require_permission("invoice.manage")
    ),
    db: Session = Depends(get_db),
):
    retailer = get_retailer_by_owner(
        db,
        current_user.id,
    )

    if retailer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found for this user.",
        )

    payment = get_payment_by_reference(
        db,
        payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    from sqlalchemy import select
    from app.models.invoice import Invoice

    invoice = db.execute(
        select(Invoice).where(
            Invoice.id == payment.invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if invoice.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    try:
        payment = refund_payment(
            db=db,
            payment=payment,
            refund_amount=request.refund_amount,
            notes=request.notes,
            retailer_id=retailer.id,
            user_id=current_user.id,
        )

        return payment_to_response(payment)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{payment_id}/cancel",
    response_model=PaymentDetailResponse,
)
def cancel_payment_endpoint(
    payment_id: str,
    current_user: User = Depends(
        require_permission("invoice.manage")
    ),
    db: Session = Depends(get_db),
):
    retailer = get_retailer_by_owner(
        db,
        current_user.id,
    )

    if retailer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found for this user.",
        )

    payment = get_payment_by_reference(
        db,
        payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    from sqlalchemy import select
    from app.models.invoice import Invoice

    invoice = db.execute(
        select(Invoice).where(
            Invoice.id == payment.invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if invoice.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    try:
        payment = cancel_payment(
            db=db,
            payment=payment,
            retailer_id=retailer.id,
            user_id=current_user.id,
        )

        return payment_to_response(payment)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
