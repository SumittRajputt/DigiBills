from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.customer import Customer
from app.models.customer_digibill import CustomerDigiBill
from app.models.invoice import Invoice
from app.models.user import User
from app.services.customer_service import get_customer_by_user_id
from app.services.invoice_service import get_invoice_items
from app.api.routes.customer_invoices import (
    get_customer_payment_summary,
)
from app.schemas.customer_bill_response import (
    CustomerBillProductResponse,
    CustomerBillResponse,
)
from app.schemas.customer_digibill_response import (
    CustomerDigiBillResponse,
)


router = APIRouter(
    prefix="/customer/bills",
    tags=["Customer Bills"],
)


def _decimal(value) -> Decimal:
    return Decimal(str(value or 0))


def _digibill_total(totals: dict) -> Decimal:
    for key in (
        "total_amount",
        "grand_total",
        "total",
        "amount",
    ):
        if key in totals and totals[key] is not None:
            return _decimal(totals[key])

    return Decimal("0.00")


def _digibill_payment_status(payment: dict) -> str:
    status = payment.get("status")

    if status:
        return str(status).lower()

    payment_status = payment.get("payment_status")

    if payment_status:
        return str(payment_status).lower()

    return "unknown"


def _digibill_products(products: list) -> list[
    CustomerBillProductResponse
]:
    result = []

    for product in products or []:
        result.append(
            CustomerBillProductResponse(
                product_name=product.get("product_name"),
                brand=product.get("brand"),
                model_number=product.get("model_number"),
                serial_number=product.get("serial_number"),
                quantity=(
                    _decimal(product["quantity"])
                    if product.get("quantity") is not None
                    else None
                ),
                unit_price=(
                    _decimal(product["unit_price"])
                    if product.get("unit_price") is not None
                    else None
                ),
                discount=(
                    _decimal(product["discount"])
                    if product.get("discount") is not None
                    else None
                ),
                tax_amount=(
                    _decimal(product["tax_amount"])
                    if product.get("tax_amount") is not None
                    else None
                ),
                total_amount=(
                    _decimal(product["total_amount"])
                    if product.get("total_amount") is not None
                    else None
                ),
            )
        )

    return result


@router.get(
    "/{digibill_id}",
    response_model=CustomerDigiBillResponse,
)
def get_customer_digibill(
    digibill_id: str,
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
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found.",
        )

    digibill = (
        db.query(CustomerDigiBill)
        .filter(
            CustomerDigiBill.digibill_id == digibill_id,
            CustomerDigiBill.customer_id == customer.id,
            CustomerDigiBill.status == "confirmed",
        )
        .first()
    )

    if digibill is None:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DigiBill not found.",
        )

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


@router.get(
    "",
    response_model=list[CustomerBillResponse],
)
def list_customer_bills(
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
        return []

    if customer.status != "active":
        return []

    invoices = db.execute(
        select(Invoice)
        .where(
            Invoice.customer_id == customer.id,
            Invoice.status == "active",
        )
        .order_by(
            Invoice.invoice_date.desc(),
            Invoice.created_at.desc(),
        )
    ).scalars().all()

    digibills = db.execute(
        select(CustomerDigiBill)
        .where(
            CustomerDigiBill.customer_id == customer.id,
            CustomerDigiBill.status == "confirmed",
        )
        .order_by(
            CustomerDigiBill.invoice_date.desc(),
            CustomerDigiBill.created_at.desc(),
        )
    ).scalars().all()

    bills: list[CustomerBillResponse] = []

    for invoice in invoices:
        items = get_invoice_items(
            db,
            invoice.id,
        )

        summary = get_customer_payment_summary(
            db,
            invoice,
        )

        products = [
            CustomerBillProductResponse(
                product_name=getattr(
                    item,
                    "product_name",
                    None,
                ),
                quantity=_decimal(
                    getattr(item, "quantity", 0)
                ),
                unit_price=_decimal(
                    getattr(item, "unit_price", 0)
                ),
                discount=_decimal(
                    getattr(item, "discount_amount", 0)
                ),
                tax_amount=_decimal(
                    getattr(item, "tax_amount", 0)
                ),
                total_amount=_decimal(
                    getattr(item, "line_total", 0)
                ),
            )
            for item in items
        ]

        retailer_name = None

        if hasattr(invoice, "retailer") and invoice.retailer:
            retailer_name = getattr(
                invoice.retailer,
                "business_name",
                None,
            )

        bills.append(
            CustomerBillResponse(
                source="retailer",
                bill_id=invoice.invoice_id,
                bill_number=invoice.invoice_number,
                bill_date=invoice.invoice_date,
                products=products,
                subtotal=_decimal(invoice.subtotal),
                discount_amount=_decimal(
                    invoice.discount_amount
                ),
                tax_amount=_decimal(invoice.tax_amount),
                total_amount=_decimal(
                    invoice.total_amount
                ),
                payment_status=summary["payment_status"],
                status=invoice.status,
                retailer_name=retailer_name,
                created_at=invoice.created_at,
                updated_at=invoice.updated_at,
            )
        )

    # Prevent the same underlying purchase from appearing more than once
    # in the customer's bill list while preserving all DigiBill records.
    seen_digibill_purchases = set()

    for digibill in digibills:
        payment = digibill.payment or {}

        purchase_key = (
            digibill.invoice_number,
            digibill.invoice_date,
            payment.get("transaction_reference"),
        )

        if purchase_key in seen_digibill_purchases:
            continue

        seen_digibill_purchases.add(purchase_key)

        retailer_name = None

        if digibill.retailer_data:
            retailer_name = (
                digibill.retailer_data.get("business_name")
                or digibill.retailer_data.get("name")
                or digibill.retailer_data.get("retailer_name")
            )

        totals = digibill.totals or {}

        bills.append(
            CustomerBillResponse(
                source="uploaded",
                bill_id=digibill.digibill_id,
                bill_number=digibill.invoice_number,
                bill_date=digibill.invoice_date,
                products=_digibill_products(
                    digibill.products
                ),
                subtotal=(
                    _decimal(totals["subtotal"])
                    if totals.get("subtotal") is not None
                    else None
                ),
                discount_amount=(
                    _decimal(totals["discount"])
                    if totals.get("discount") is not None
                    else None
                ),
                tax_amount=(
                    _decimal(totals["tax"])
                    if totals.get("tax") is not None
                    else None
                ),
                total_amount=_digibill_total(
                    totals
                ),
                payment_status=_digibill_payment_status(
                    digibill.payment
                ),
                status=digibill.status,
                retailer_name=retailer_name,
                uploaded_bill_id=str(
                    digibill.uploaded_bill_id
                ),
                digibill_id=digibill.digibill_id,
                created_at=digibill.created_at,
                updated_at=digibill.updated_at,
            )
        )

    bills.sort(
        key=lambda bill: (
            bill.bill_date or bill.created_at
        ),
        reverse=True,
    )

    return bills
