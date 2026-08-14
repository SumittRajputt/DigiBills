import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.product_ownership import ProductOwnership
from app.models.product_unit import ProductUnit
from app.models.user import User
from app.schemas.product_ownership import (
    ProductOwnershipCreateRequest,
    ProductOwnershipResponse,
)
from app.services.product_ownership_service import (
    create_product_ownership,
    get_ownership_by_product_unit,
    get_ownership_by_serial_number,
    get_product_ownership,
)


router = APIRouter(
    prefix="/product-ownerships",
    tags=["Product Ownership"],
)


def ownership_to_response(
    ownership: ProductOwnership,
) -> ProductOwnershipResponse:
    return ProductOwnershipResponse(
        id=str(ownership.id),
        product_unit_id=str(
            ownership.product_unit_id
        ),
        customer_id=str(
            ownership.customer_id
        ),
        ownership_status=ownership.ownership_status,
        acquired_at=ownership.acquired_at,
        released_at=ownership.released_at,
        source=ownership.source,
        created_at=ownership.created_at,
    )


@router.post(
    "",
    response_model=ProductOwnershipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_ownership_endpoint(
    request: ProductOwnershipCreateRequest,
    current_user: User = Depends(
        require_permission("invoice.manage")
    ),
    db: Session = Depends(get_db),
):
    invoice = db.execute(
        select(Invoice).where(
            Invoice.invoice_id == request.invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if invoice.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active invoices can create ownership.",
        )

    try:
        parsed_invoice_item_id = uuid.UUID(
            request.invoice_item_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice item not found.",
        )

    invoice_item = db.execute(
        select(InvoiceItem).where(
            InvoiceItem.id == parsed_invoice_item_id,
            InvoiceItem.invoice_id == invoice.id,
        )
    ).scalar_one_or_none()

    if invoice_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice item not found.",
        )

    try:
        parsed_product_unit_id = uuid.UUID(
            request.product_unit_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product unit not found.",
        )

    product_unit = db.execute(
        select(ProductUnit).where(
            ProductUnit.id == parsed_product_unit_id
        )
    ).scalar_one_or_none()

    if product_unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product unit not found.",
        )

    if product_unit.product_variant_id != (
        invoice_item.product_variant_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Product unit does not belong to "
                "the product variant on this invoice item."
            ),
        )

    customer = db.execute(
        select(Customer).where(
            Customer.id == invoice.customer_id
        )
    ).scalar_one_or_none()

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

    try:
        ownership = create_product_ownership(
            db=db,
            invoice=invoice,
            invoice_item=invoice_item,
            product_unit=product_unit,
            customer=customer,
            source="invoice",
        )

        return ownership_to_response(
            ownership
        )

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/{ownership_id}",
    response_model=ProductOwnershipResponse,
)
def get_product_ownership_endpoint(
    ownership_id: str,
    current_user: User = Depends(
        require_permission("invoice.view")
    ),
    db: Session = Depends(get_db),
):
    ownership = get_product_ownership(
        db=db,
        ownership_id=ownership_id,
    )

    if ownership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product ownership not found.",
        )

    return ownership_to_response(ownership)


@router.get(
    "/serial/{serial_number}",
    response_model=ProductOwnershipResponse,
)
def get_ownership_by_serial_endpoint(
    serial_number: str,
    current_user: User = Depends(
        require_permission("invoice.view")
    ),
    db: Session = Depends(get_db),
):
    ownership = get_ownership_by_serial_number(
        db=db,
        serial_number=serial_number,
    )

    if ownership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active ownership not found for this serial number.",
        )

    return ownership_to_response(ownership)
