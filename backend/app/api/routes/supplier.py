from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.supplier import (
    SupplierCreateRequest,
    SupplierResponse,
)
from app.services.retailer_service import (
    get_retailer_by_owner,
)
from app.services.supplier_service import (
    create_supplier,
    get_supplier_by_supplier_id,
    get_suppliers_for_retailer,
)


router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)


def supplier_to_response(supplier):
    return SupplierResponse(
        id=str(supplier.id),
        supplier_id=supplier.supplier_id,
        retailer_id=str(supplier.retailer_id),
        name=supplier.name,
        contact_person=supplier.contact_person,
        phone_number=supplier.phone_number,
        email=supplier.email,
        address=supplier.address,
        tax_identifier=supplier.tax_identifier,
        is_active=supplier.is_active,
        created_at=supplier.created_at,
        updated_at=supplier.updated_at,
    )


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_supplier_endpoint(
    request: SupplierCreateRequest,
    current_user: User = Depends(
        require_permission("inventory.manage")
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

    try:
        supplier = create_supplier(
            db=db,
            retailer=retailer,
            name=request.name,
            contact_person=request.contact_person,
            phone_number=request.phone_number,
            email=(
                str(request.email)
                if request.email
                else None
            ),
            address=request.address,
            tax_identifier=request.tax_identifier,
        )

        return supplier_to_response(supplier)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[SupplierResponse],
)
def list_suppliers_endpoint(
    current_user: User = Depends(
        require_permission("inventory.view")
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

    suppliers = get_suppliers_for_retailer(
        db,
        retailer.id,
    )

    return [
        supplier_to_response(supplier)
        for supplier in suppliers
    ]


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
)
def get_supplier_endpoint(
    supplier_id: str,
    current_user: User = Depends(
        require_permission("inventory.view")
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

    supplier = get_supplier_by_supplier_id(
        db,
        supplier_id,
    )

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    if supplier.retailer_id != retailer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found.",
        )

    return supplier_to_response(supplier)