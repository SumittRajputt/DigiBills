from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.invoice import (
    InvoiceCreateRequest,
    InvoiceDetailResponse,
    InvoiceItemResponse,
    InvoiceResponse,
)
from app.services.customer_service import get_customer_by_customer_id
from app.services.invoice_service import (
    create_invoice,
    get_invoice_by_reference,
    get_invoice_items,
    get_location_for_retailer,
    get_all_invoices,
)
from app.services.retailer_service import get_retailer_by_owner


router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
)


def invoice_to_response(invoice):
    return InvoiceResponse(
        id=str(invoice.id),
        invoice_id=invoice.invoice_id,
        retailer_id=(
            str(invoice.retailer_id)
            if invoice.retailer_id
            else None
        ),
        subscription_id=(
            str(invoice.subscription_id)
            if invoice.subscription_id
            else None
        ),
        employee_id=(
            str(invoice.employee_id)
            if invoice.employee_id
            else None
        ),
        customer_id=str(invoice.customer_id),
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        subtotal=invoice.subtotal,
        discount_amount=invoice.discount_amount,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount,
        payment_status=invoice.payment_status,
        status=invoice.status,
        notes=invoice.notes,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )


def invoice_item_to_response(item):
    return InvoiceItemResponse(
        id=str(item.id),
        invoice_id=str(item.invoice_id),
        product_variant_id=str(item.product_variant_id),
        product_name=item.product_name,
        sku=item.sku,
        quantity=item.quantity,
        unit_price=item.unit_price,
        unit_cost=item.unit_cost,
        discount_amount=item.discount_amount,
        tax_rate=item.tax_rate,
        tax_amount=item.tax_amount,
        line_total=item.line_total,
        created_at=item.created_at,
    )


def invoice_detail_to_response(invoice, items):
    return InvoiceDetailResponse(
        id=str(invoice.id),
        invoice_id=invoice.invoice_id,
        retailer_id=(
            str(invoice.retailer_id)
            if invoice.retailer_id
            else None
        ),
        subscription_id=(
            str(invoice.subscription_id)
            if invoice.subscription_id
            else None
        ),
        employee_id=(
            str(invoice.employee_id)
            if invoice.employee_id
            else None
        ),
        customer_id=str(invoice.customer_id),
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        subtotal=invoice.subtotal,
        discount_amount=invoice.discount_amount,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount,
        payment_status=invoice.payment_status,
        status=invoice.status,
        notes=invoice.notes,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
        items=[
            invoice_item_to_response(item)
            for item in items
        ],
    )


@router.post(
    "",
    response_model=InvoiceDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invoice_endpoint(
    request: InvoiceCreateRequest,
    current_user: User = Depends(
        require_permission("invoice.create")
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

    customer = get_customer_by_customer_id(
        db,
        request.customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer is not active.",
        )

    location = get_location_for_retailer(
        db,
        request.location_id,
        retailer.id,
    )

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory location not found.",
        )

    try:
        invoice = create_invoice(
            db=db,
            retailer=retailer,
            customer=customer,
            location=location,
            items=request.items,
            invoice_number=request.invoice_number,
            invoice_discount=request.discount_amount,
            notes=request.notes,
            employee_id=None,
            user_id=current_user.id,
        )

        items = get_invoice_items(
            db,
            invoice.id,
        )

        return invoice_detail_to_response(
            invoice,
            items,
        )

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[InvoiceResponse],
)
def list_invoices(
    current_user: User = Depends(
        require_permission("invoice.view")
    ),
    db: Session = Depends(get_db),
):
    invoices = get_all_invoices(db)

    return [
        invoice_to_response(invoice)
        for invoice in invoices
    ]


@router.get(
    "/{invoice_id}",
    response_model=InvoiceDetailResponse,
)
def get_invoice_endpoint(
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

    items = get_invoice_items(
        db,
        invoice.id,
    )

    return invoice_detail_to_response(
        invoice,
        items,
    )
