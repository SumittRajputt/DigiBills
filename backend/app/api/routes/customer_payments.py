from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.user import User
from app.schemas.payment import PaymentResponse
from app.services.customer_service import get_customer_by_user_id


router = APIRouter(
    prefix="/customer/payments",
    tags=["Customer Payments"],
)


def payment_to_response(
    payment: Payment,
    item_names=None,
) -> PaymentResponse:
    return PaymentResponse(
        id=str(payment.id),
        payment_id=payment.payment_id,
        invoice_id=str(payment.invoice_id),
        item_names=item_names or [],
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


@router.get(
    "",
    response_model=list[PaymentResponse],
)
def list_customer_payments(
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
            detail="Customer not found for this user.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer is not active.",
        )

    payments = db.execute(
        select(Payment)
        .join(
            Invoice,
            Invoice.id == Payment.invoice_id,
        )
        .where(
            Invoice.customer_id == customer.id,
        )
        .order_by(
            Payment.paid_at.desc(),
            Payment.created_at.desc(),
        )
    ).scalars().all()

    result = []

    for payment in payments:
        invoice_items = db.execute(
            select(InvoiceItem).where(
                InvoiceItem.invoice_id == payment.invoice_id,
            )
        ).scalars().all()

        item_names = [
            item.product_name
            for item in invoice_items
            if item.product_name
        ]

        result.append(
            payment_to_response(
                payment,
                item_names=item_names,
            )
        )

    return result
