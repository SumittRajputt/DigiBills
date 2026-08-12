from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.retailer import (
    RetailerCreateRequest,
    RetailerResponse,
)
from app.schemas.retailer_approval import (
    RetailerRejectRequest,
)
from app.services.retailer_approval_service import (
    approve_retailer,
    reject_retailer,
)
from app.services.retailer_service import (
    create_retailer,
    get_retailer_by_owner,
    get_retailer_by_retailer_id,
)


router = APIRouter(
    prefix="/retailers",
    tags=["Retailers"],
)


def retailer_to_response(retailer):
    return RetailerResponse(
        id=str(retailer.id),
        retailer_id=retailer.retailer_id,
        owner_user_id=str(retailer.owner_user_id),
        business_name=retailer.business_name,
        business_type=retailer.business_type,
        phone_number=retailer.phone_number,
        email=retailer.email,
        address=retailer.address,
        status=retailer.status,
        approved_at=retailer.approved_at,
        approved_by=(
            str(retailer.approved_by)
            if retailer.approved_by
            else None
        ),
        rejection_reason=retailer.rejection_reason,
        created_at=retailer.created_at,
        updated_at=retailer.updated_at,
    )


@router.post(
    "",
    response_model=RetailerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_retailer_endpoint(
    request: RetailerCreateRequest,
    current_user: User = Depends(
        require_permission("retailer.manage")
    ),
    db: Session = Depends(get_db),
):
    try:
        retailer = create_retailer(
            db=db,
            owner_user=current_user,
            business_name=request.business_name,
            business_type=request.business_type,
            phone_number=request.phone_number,
            email=request.email,
            address=request.address,
        )

        return retailer_to_response(retailer)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/me",
    response_model=RetailerResponse,
)
def get_my_retailer(
    current_user: User = Depends(
        require_permission("retailer.view")
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

    return retailer_to_response(retailer)


@router.post(
    "/{retailer_id}/approve",
    response_model=RetailerResponse,
)
def approve_retailer_endpoint(
    retailer_id: str,
    current_user: User = Depends(
        require_permission("retailer.manage")
    ),
    db: Session = Depends(get_db),
):
    retailer = get_retailer_by_retailer_id(
        db,
        retailer_id,
    )

    if retailer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found.",
        )

    try:
        retailer = approve_retailer(
            db=db,
            retailer=retailer,
            approved_by=current_user,
        )

        return retailer_to_response(retailer)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{retailer_id}/reject",
    response_model=RetailerResponse,
)
def reject_retailer_endpoint(
    retailer_id: str,
    request: RetailerRejectRequest,
    current_user: User = Depends(
        require_permission("retailer.manage")
    ),
    db: Session = Depends(get_db),
):
    retailer = get_retailer_by_retailer_id(
        db,
        retailer_id,
    )

    if retailer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retailer not found.",
        )

    try:
        retailer = reject_retailer(
            db=db,
            retailer=retailer,
            rejected_by=current_user,
            rejection_reason=request.rejection_reason,
        )

        return retailer_to_response(retailer)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )