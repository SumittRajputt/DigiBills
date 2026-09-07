from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.warranty import (
    WarrantyCreateRequest,
    WarrantyResponse,
    WarrantyStatusUpdateRequest,
    WarrantyTransferRequest,
)
from app.services.retailer_service import get_retailer_by_owner
from app.services.warranty_service import (
    get_warranties_for_retailer,
    create_warranty,
    get_invoice_by_reference,
    get_warranty_by_reference,
    transfer_warranty,
    update_warranty_status,
)


router = APIRouter(
    prefix="/warranties",
    tags=["Warranties"],
)


def warranty_to_response(warranty):
    return WarrantyResponse(
        id=str(warranty.id),
        warranty_id=warranty.warranty_id,
        invoice_id=str(warranty.invoice_id),
        product_variant_id=str(warranty.product_variant_id),
        customer_id=str(warranty.customer_id),
        start_date=warranty.start_date,
        end_date=warranty.end_date,
        duration_months=warranty.duration_months,
        is_transferable=warranty.is_transferable,
        status=warranty.status,
        created_at=warranty.created_at,
        updated_at=warranty.updated_at,
    )


@router.post(
    "",
    response_model=WarrantyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_warranty_endpoint(
    request: WarrantyCreateRequest,
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
        warranty = create_warranty(
            db=db,
            retailer=retailer,
            invoice=invoice,
            product_variant_id=request.product_variant_id,
            start_date=request.start_date,
            end_date=request.end_date,
            duration_months=request.duration_months,
            is_transferable=request.is_transferable,
        )

        return warranty_to_response(warranty)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[WarrantyResponse],
)
def list_warranties_endpoint(
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

    warranties = get_warranties_for_retailer(
        db,
        retailer.id,
    )

    return [
        warranty_to_response(warranty)
        for warranty in warranties
    ]


@router.get(
    "/{warranty_id}",
    response_model=WarrantyResponse,
)
def get_warranty_endpoint(
    warranty_id: str,
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

    warranty = get_warranty_by_reference(
        db,
        warranty_id,
    )

    if warranty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warranty not found.",
        )

    invoice = get_invoice_by_reference(
        db,
        str(warranty.invoice_id),
    )

    if invoice is not None and invoice.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warranty not found.",
        )

    return warranty_to_response(warranty)


@router.post(
    "/{warranty_id}/status",
    response_model=WarrantyResponse,
)
def update_warranty_status_endpoint(
    warranty_id: str,
    request: WarrantyStatusUpdateRequest,
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

    warranty = get_warranty_by_reference(
        db,
        warranty_id,
    )

    if warranty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warranty not found.",
        )

    from sqlalchemy import select
    from app.models.invoice import Invoice

    invoice = db.execute(
        select(Invoice).where(
            Invoice.id == warranty.invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None or invoice.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warranty not found.",
        )

    try:
        warranty = update_warranty_status(
            db=db,
            warranty=warranty,
            new_status=request.status,
        )

        return warranty_to_response(warranty)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{warranty_id}/transfer",
    response_model=WarrantyResponse,
)
def transfer_warranty_endpoint(
    warranty_id: str,
    request: WarrantyTransferRequest,
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

    warranty = get_warranty_by_reference(
        db,
        warranty_id,
    )

    if warranty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warranty not found.",
        )

    from sqlalchemy import select
    from app.models.invoice import Invoice

    invoice = db.execute(
        select(Invoice).where(
            Invoice.id == warranty.invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None or invoice.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warranty not found.",
        )

    try:
        warranty = transfer_warranty(
            db=db,
            warranty=warranty,
            new_customer_id=request.customer_id,
        )

        return warranty_to_response(warranty)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
