from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.user import User
from app.schemas.invoice import (
    InvoiceDetailResponse,
    InvoiceResponse,
)
from app.services.customer_service import get_customer_by_user_id
from app.services.invoice_service import (
    get_invoice_by_reference,
    get_invoice_items,
)
from app.services.invoice_pdf_service import generate_invoice_pdf
from app.api.routes.invoice import (
    invoice_to_response,
    invoice_detail_to_response,
)


def get_customer_payment_summary(
    db: Session,
    invoice: Invoice,
) -> dict:
    payments = db.execute(
        select(Payment).where(
            Payment.invoice_id == invoice.id,
        )
    ).scalars().all()

    gross_paid = Decimal("0.00")
    refunds = Decimal("0.00")

    for payment in payments:
        if payment.payment_status != "completed":
            continue

        amount = Decimal(str(payment.amount or 0))
        refund = Decimal(str(payment.refund_amount or 0))

        gross_paid += amount
        refunds += min(refund, amount)

    net_paid = max(
        Decimal("0.00"),
        gross_paid - refunds,
    )

    total = Decimal(str(invoice.total_amount))

    outstanding = max(
        Decimal("0.00"),
        total - net_paid,
    )

    if net_paid >= total:
        payment_status = "paid"
    elif net_paid > Decimal("0.00"):
        payment_status = "partial"
    else:
        payment_status = "unpaid"

    return {
        "payment_status": payment_status,
        "gross_paid": gross_paid,
        "refunds": refunds,
        "net_paid": net_paid,
        "outstanding": outstanding,
    }


router = APIRouter(
    prefix="/customer/invoices",
    tags=["Customer Invoices"],
)


@router.get(
    "",
    response_model=list[InvoiceResponse],
)
def list_customer_invoices(
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

    invoices = list(
        db.execute(
            select(Invoice)
            .where(
                Invoice.customer_id == customer.id,
                Invoice.status == "active",
            )
            .order_by(
                Invoice.invoice_date.desc()
            )
        )
        .scalars()
        .all()
    )

    result = []

    for invoice in invoices:
        summary = get_customer_payment_summary(
            db,
            invoice,
        )

        items = get_invoice_items(
            db,
            invoice.id,
        )

        item_names = [
            item.product_name
            for item in items
            if item.product_name
        ]

        result.append(
            invoice_to_response(
                invoice,
                payment_status=summary["payment_status"],
                item_names=item_names,
            )
        )

    return result


@router.get(
    "/{invoice_id}/pdf",
)
def get_customer_invoice_pdf(
    invoice_id: str,
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

    invoice = get_invoice_by_reference(
        db,
        invoice_id,
    )

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if invoice.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    items = get_invoice_items(
        db,
        invoice.id,
    )

    retailer = db.execute(
        select(
            __import__(
                "app.models.retailer",
                fromlist=["Retailer"],
            ).Retailer
        ).where(
            __import__(
                "app.models.retailer",
                fromlist=["Retailer"],
            ).Retailer.id == invoice.retailer_id
        )
    ).scalar_one_or_none()

    if retailer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found.",
        )

    payment_summary = get_customer_payment_summary(
        db,
        invoice,
    )

    pdf = generate_invoice_pdf(
        invoice=invoice,
        customer=customer,
        retailer=retailer,
        items=items,
        payment_summary=payment_summary,
    )

    filename = (
        f"{invoice.invoice_id}.pdf"
    )

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'inline; filename="{filename}"'
            )
        },
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceDetailResponse,
)
def get_customer_invoice(
    invoice_id: str,
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

    invoice = get_invoice_by_reference(
        db,
        invoice_id,
    )

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if invoice.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    items = get_invoice_items(
        db,
        invoice.id,
    )

    summary = get_customer_payment_summary(
        db,
        invoice,
    )

    return invoice_detail_to_response(
        invoice,
        items,
        payment_status=summary["payment_status"],
    )
