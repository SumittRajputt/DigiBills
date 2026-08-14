import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.services.audit_log_service import create_audit_log


def generate_payment_id() -> str:
    return f"PAY-{uuid.uuid4().hex[:10].upper()}"


def get_payment_by_reference(
    db: Session,
    payment_reference: str,
) -> Optional[Payment]:
    statement = select(Payment).where(
        Payment.payment_id == payment_reference
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_payment_by_id(
    db: Session,
    payment_id: uuid.UUID,
) -> Optional[Payment]:
    statement = select(Payment).where(
        Payment.id == payment_id
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_invoice_by_reference(
    db: Session,
    invoice_reference: str,
) -> Optional[Invoice]:
    statement = select(Invoice).where(
        Invoice.invoice_id == invoice_reference
    )

    return db.execute(
        statement
    ).scalar_one_or_none()


def get_invoice_payments(
    db: Session,
    invoice_id: uuid.UUID,
):
    statement = (
        select(Payment)
        .where(
            Payment.invoice_id == invoice_id
        )
        .order_by(
            Payment.paid_at.asc()
        )
    )

    return list(
        db.execute(statement).scalars().all()
    )


def get_completed_payment_total(
    db: Session,
    invoice_id: uuid.UUID,
) -> Decimal:
    payments = get_invoice_payments(
        db,
        invoice_id,
    )

    total = Decimal("0.00")

    for payment in payments:
        if payment.payment_status == "completed":
            total += (
                payment.amount
                - (payment.refund_amount or Decimal("0.00"))
            )

    return total


def create_payment(
    db: Session,
    invoice: Invoice,
    amount: Decimal,
    payment_method: str,
    transaction_reference: Optional[str] = None,
    notes: Optional[str] = None,
    retailer_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
) -> Payment:
    if invoice.status != "active":
        raise ValueError(
            "Only active invoices can receive payments."
        )

    amount = Decimal(amount)

    if amount <= Decimal("0.00"):
        raise ValueError(
            "Payment amount must be greater than zero."
        )

    payment_method = (
        payment_method.strip().lower()
    )

    if not payment_method:
        raise ValueError(
            "Payment method is required."
        )

    already_paid = get_completed_payment_total(
        db,
        invoice.id,
    )

    remaining_amount = (
        invoice.total_amount - already_paid
    )

    if remaining_amount <= Decimal("0.00"):
        raise ValueError(
            "Invoice is already fully paid."
        )

    if amount > remaining_amount:
        raise ValueError(
            f"Payment amount cannot exceed "
            f"remaining invoice amount of "
            f"{remaining_amount:.2f}."
        )

    payment = Payment(
        payment_id=generate_payment_id(),
        invoice_id=invoice.id,
        amount=amount,
        payment_method=payment_method,
        payment_status="completed",
        transaction_reference=transaction_reference,
        paid_at=datetime.now(timezone.utc),
        refund_amount=Decimal("0.00"),
        refund_status=None,
        notes=notes,
    )

    db.add(payment)
    db.flush()

    new_paid_total = (
        already_paid + amount
    )

    if new_paid_total >= invoice.total_amount:
        invoice.payment_status = "paid"
    else:
        invoice.payment_status = "partial"

    invoice.updated_at = datetime.now(timezone.utc)

    create_audit_log(
        db=db,
        retailer_id=retailer_id,
        user_id=user_id,
        action="PAYMENT_CREATED",
        entity_type="payment",
        entity_id=payment.id,
        description=(
            f"Payment {payment.payment_id} created for "
            f"invoice {invoice.invoice_id} "
            f"amount {payment.amount:.2f} "
            f"via {payment.payment_method}."
        ),
    )

    db.commit()
    db.refresh(payment)
    db.refresh(invoice)

    return payment


def refund_payment(
    db: Session,
    payment: Payment,
    refund_amount: Decimal,
    notes: Optional[str] = None,
    retailer_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
) -> Payment:
    if payment.payment_status != "completed":
        raise ValueError(
            "Only completed payments can be refunded."
        )

    refund_amount = Decimal(refund_amount)

    if refund_amount <= Decimal("0.00"):
        raise ValueError(
            "Refund amount must be greater than zero."
        )

    existing_refund = (
        payment.refund_amount
        or Decimal("0.00")
    )

    refundable_amount = (
        payment.amount - existing_refund
    )

    if refund_amount > refundable_amount:
        raise ValueError(
            f"Refund amount cannot exceed "
            f"refundable amount of "
            f"{refundable_amount:.2f}."
        )

    payment.refund_amount = (
        existing_refund + refund_amount
    )

    if payment.refund_amount >= payment.amount:
        payment.refund_status = "refunded"
    else:
        payment.refund_status = "partial"

    if notes:
        payment.notes = notes

    payment.updated_at = datetime.now(timezone.utc)

    invoice = db.execute(
        select(Invoice).where(
            Invoice.id == payment.invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None:
        raise ValueError(
            "Invoice not found for payment."
        )

    total_paid_after_refund = (
        get_completed_payment_total(
            db,
            invoice.id,
        )
        - refund_amount
    )

    if total_paid_after_refund <= Decimal("0.00"):
        invoice.payment_status = "unpaid"
    elif total_paid_after_refund < invoice.total_amount:
        invoice.payment_status = "partial"
    else:
        invoice.payment_status = "paid"

    invoice.updated_at = datetime.now(timezone.utc)

    create_audit_log(
        db=db,
        retailer_id=retailer_id,
        user_id=user_id,
        action="PAYMENT_REFUNDED",
        entity_type="payment",
        entity_id=payment.id,
        description=(
            f"Payment {payment.payment_id} refunded "
            f"amount {refund_amount:.2f}. "
            f"Refund status: {payment.refund_status}."
        ),
    )

    db.commit()
    db.refresh(payment)
    db.refresh(invoice)

    return payment


def cancel_payment(
    db: Session,
    payment: Payment,
    retailer_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
) -> Payment:
    if payment.payment_status != "completed":
        raise ValueError(
            "Only completed payments can be cancelled."
        )

    if payment.refund_amount and payment.refund_amount > 0:
        raise ValueError(
            "A payment with refunds cannot be cancelled."
        )

    payment.payment_status = "cancelled"
    payment.updated_at = datetime.now(timezone.utc)

    invoice = db.execute(
        select(Invoice).where(
            Invoice.id == payment.invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None:
        raise ValueError(
            "Invoice not found for payment."
        )

    invoice_paid_total = get_completed_payment_total(
        db,
        invoice.id,
    )

    if invoice_paid_total <= Decimal("0.00"):
        invoice.payment_status = "unpaid"
    elif invoice_paid_total < invoice.total_amount:
        invoice.payment_status = "partial"
    else:
        invoice.payment_status = "paid"

    invoice.updated_at = datetime.now(timezone.utc)

    create_audit_log(
        db=db,
        retailer_id=retailer_id,
        user_id=user_id,
        action="PAYMENT_CANCELLED",
        entity_type="payment",
        entity_id=payment.id,
        description=(
            f"Payment {payment.payment_id} cancelled."
        ),
    )

    db.commit()
    db.refresh(payment)
    db.refresh(invoice)

    return payment
