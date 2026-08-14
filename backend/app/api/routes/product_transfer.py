import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.customer import Customer
from app.models.product_transfer import ProductTransfer
from app.models.product_unit import ProductUnit
from app.models.user import User
from app.schemas.product_transfer import (
    ProductTransferCreateRequest,
    ProductTransferRejectRequest,
    ProductTransferResponse,
)
from app.services.product_transfer_service import (
    approve_product_transfer,
    create_product_transfer,
    reject_product_transfer,
)


router = APIRouter(
    prefix="/product-transfers",
    tags=["Product Transfers"],
)


def transfer_to_response(
    transfer: ProductTransfer,
) -> ProductTransferResponse:
    return ProductTransferResponse(
        id=str(transfer.id),
        transfer_id=transfer.transfer_id,
        product_unit_id=str(transfer.product_unit_id),
        from_customer_id=str(transfer.from_customer_id),
        to_customer_id=str(transfer.to_customer_id),
        requested_by_user_id=str(
            transfer.requested_by_user_id
        ),
        approved_by_user_id=(
            str(transfer.approved_by_user_id)
            if transfer.approved_by_user_id
            else None
        ),
        status=transfer.status,
        reason=transfer.reason,
        rejection_reason=transfer.rejection_reason,
        requested_at=transfer.requested_at,
        approved_at=transfer.approved_at,
        completed_at=transfer.completed_at,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


@router.post(
    "",
    response_model=ProductTransferResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_transfer_endpoint(
    request: ProductTransferCreateRequest,
    current_user: User = Depends(
        require_permission("product.manage")
    ),
    db: Session = Depends(get_db),
):
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

    try:
        parsed_from_customer_id = uuid.UUID(
            request.from_customer_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source customer not found.",
        )

    from_customer = db.execute(
        select(Customer).where(
            Customer.id == parsed_from_customer_id
        )
    ).scalar_one_or_none()

    if from_customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source customer not found.",
        )

    try:
        parsed_to_customer_id = uuid.UUID(
            request.to_customer_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination customer not found.",
        )

    to_customer = db.execute(
        select(Customer).where(
            Customer.id == parsed_to_customer_id
        )
    ).scalar_one_or_none()

    if to_customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination customer not found.",
        )

    try:
        transfer = create_product_transfer(
            db=db,
            product_unit=product_unit,
            from_customer=from_customer,
            to_customer=to_customer,
            requested_by_user_id=current_user.id,
            reason=request.reason,
        )

        return transfer_to_response(transfer)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{transfer_id}/approve",
    response_model=ProductTransferResponse,
)
def approve_product_transfer_endpoint(
    transfer_id: str,
    current_user: User = Depends(
        require_permission("product.manage")
    ),
    db: Session = Depends(get_db),
):
    transfer = db.execute(
        select(ProductTransfer).where(
            ProductTransfer.transfer_id == transfer_id
        )
    ).scalar_one_or_none()

    if transfer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product transfer not found.",
        )

    try:
        transfer = approve_product_transfer(
            db=db,
            transfer=transfer,
            approved_by_user_id=current_user.id,
        )

        return transfer_to_response(transfer)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{transfer_id}/reject",
    response_model=ProductTransferResponse,
)
def reject_product_transfer_endpoint(
    transfer_id: str,
    request: ProductTransferRejectRequest,
    current_user: User = Depends(
        require_permission("product.manage")
    ),
    db: Session = Depends(get_db),
):
    transfer = db.execute(
        select(ProductTransfer).where(
            ProductTransfer.transfer_id == transfer_id
        )
    ).scalar_one_or_none()

    if transfer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product transfer not found.",
        )

    try:
        transfer = reject_product_transfer(
            db=db,
            transfer=transfer,
            rejected_by_user_id=current_user.id,
            rejection_reason=request.rejection_reason,
        )

        return transfer_to_response(transfer)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/{transfer_id}",
    response_model=ProductTransferResponse,
)
def get_product_transfer_endpoint(
    transfer_id: str,
    current_user: User = Depends(
        require_permission("product.view")
    ),
    db: Session = Depends(get_db),
):
    transfer = db.execute(
        select(ProductTransfer).where(
            ProductTransfer.transfer_id == transfer_id
        )
    ).scalar_one_or_none()

    if transfer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product transfer not found.",
        )

    return transfer_to_response(transfer)
