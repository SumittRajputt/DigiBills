from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.sales_return import (
    SalesReturnCreateRequest,
    SalesReturnDetailResponse,
    SalesReturnItemCreateRequest,
    SalesReturnItemResponse,
    SalesReturnProcessRequest,
    SalesReturnResponse,
)
from app.services.retailer_service import get_retailer_by_owner
from app.services.sales_return_service import (
    add_sales_return_item,
    create_sales_return,
    get_invoice_by_reference,
    get_sales_return_by_reference,
    get_sales_return_items,
    process_sales_return,
)


router = APIRouter(
    prefix="/sales-returns",
    tags=["Sales Returns"],
)


def sales_return_to_response(sales_return):
    return SalesReturnResponse(
        id=str(sales_return.id),
        return_id=sales_return.return_id,
        invoice_id=str(sales_return.invoice_id),
        retailer_id=str(sales_return.retailer_id),
        customer_id=str(sales_return.customer_id),
        processed_by_user_id=(
            str(sales_return.processed_by_user_id)
            if sales_return.processed_by_user_id
            else None
        ),
        return_amount=sales_return.return_amount,
        refund_amount=sales_return.refund_amount,
        refund_method=sales_return.refund_method,
        status=sales_return.status,
        reason=sales_return.reason,
        notes=sales_return.notes,
        requested_at=sales_return.requested_at,
        processed_at=sales_return.processed_at,
        created_at=sales_return.created_at,
        updated_at=sales_return.updated_at,
    )


def sales_return_item_to_response(item):
    return SalesReturnItemResponse(
        id=str(item.id),
        sales_return_id=str(item.sales_return_id),
        invoice_item_id=str(item.invoice_item_id),
        product_variant_id=str(item.product_variant_id),
        product_name=item.product_name,
        sku=item.sku,
        quantity=item.quantity,
        unit_price=item.unit_price,
        return_amount=item.return_amount,
        restocking_fee=item.restocking_fee,
        refund_amount=item.refund_amount,
        condition=item.condition,
        return_to_inventory=item.return_to_inventory,
        reason=item.reason,
        created_at=item.created_at,
    )


def sales_return_detail_to_response(
    sales_return,
    items,
):
    return SalesReturnDetailResponse(
        id=str(sales_return.id),
        return_id=sales_return.return_id,
        invoice_id=str(sales_return.invoice_id),
        retailer_id=str(sales_return.retailer_id),
        customer_id=str(sales_return.customer_id),
        processed_by_user_id=(
            str(sales_return.processed_by_user_id)
            if sales_return.processed_by_user_id
            else None
        ),
        return_amount=sales_return.return_amount,
        refund_amount=sales_return.refund_amount,
        refund_method=sales_return.refund_method,
        status=sales_return.status,
        reason=sales_return.reason,
        notes=sales_return.notes,
        requested_at=sales_return.requested_at,
        processed_at=sales_return.processed_at,
        created_at=sales_return.created_at,
        updated_at=sales_return.updated_at,
        items=[
            sales_return_item_to_response(item)
            for item in items
        ],
    )


@router.post(
    "",
    response_model=SalesReturnDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sales_return_endpoint(
    request: SalesReturnCreateRequest,
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
        sales_return = create_sales_return(
            db=db,
            retailer=retailer,
            invoice=invoice,
            reason=request.reason,
        product_unit_ids=request.product_unit_ids,
            notes=request.notes,
        )

        items = get_sales_return_items(
            db,
            sales_return.id,
        )

        return sales_return_detail_to_response(
            sales_return,
            items,
        )

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{return_id}/items",
    response_model=SalesReturnDetailResponse,
)
def add_sales_return_item_endpoint(
    return_id: str,
    request: SalesReturnItemCreateRequest,
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

    sales_return = get_sales_return_by_reference(
        db,
        return_id,
    )

    if sales_return is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales return not found.",
        )

    if sales_return.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales return not found.",
        )

    try:
        add_sales_return_item(
            db=db,
            sales_return=sales_return,
            invoice_item_id=request.invoice_item_id,
            quantity=request.quantity,
            condition=request.condition,
            return_to_inventory=request.return_to_inventory,
            restocking_fee=request.restocking_fee,
            reason=request.reason,
        product_unit_ids=request.product_unit_ids,
        )

        db.refresh(sales_return)

        items = get_sales_return_items(
            db,
            sales_return.id,
        )

        return sales_return_detail_to_response(
            sales_return,
            items,
        )

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{return_id}/process",
    response_model=SalesReturnDetailResponse,
)
def process_sales_return_endpoint(
    return_id: str,
    request: SalesReturnProcessRequest,
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

    sales_return = get_sales_return_by_reference(
        db,
        return_id,
    )

    if sales_return is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales return not found.",
        )

    if sales_return.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales return not found.",
        )

    try:
        process_sales_return(
            db=db,
            sales_return=sales_return,
            retailer=retailer,
            processed_by_user_id=current_user.id,
            refund_method=request.refund_method,
        )

        items = get_sales_return_items(
            db,
            sales_return.id,
        )

        return sales_return_detail_to_response(
            sales_return,
            items,
        )

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/{return_id}",
    response_model=SalesReturnDetailResponse,
)
def get_sales_return_endpoint(
    return_id: str,
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

    sales_return = get_sales_return_by_reference(
        db,
        return_id,
    )

    if sales_return is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales return not found.",
        )

    if sales_return.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sales return not found.",
        )

    items = get_sales_return_items(
        db,
        sales_return.id,
    )

    return sales_return_detail_to_response(
        sales_return,
        items,
    )
