from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.customer import (
    CustomerCreateRequest,
    CustomerResponse,
)
from app.services.customer_service import (
    create_customer,
    get_all_customers,
    get_customer_by_user_id,
)


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


def customer_to_response(customer):
    return CustomerResponse(
        id=str(customer.id),
        customer_id=customer.customer_id,
        user_id=str(customer.user_id),
        full_name=customer.full_name,
        phone_number=customer.phone_number,
        email=customer.email,
        status=customer.status,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
    )


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_endpoint(
    request: CustomerCreateRequest,
    current_user: User = Depends(
        require_permission("customer.manage")
    ),
    db: Session = Depends(get_db),
):
    try:
        customer = create_customer(
            db=db,
            user_id=current_user.id,
            full_name=request.full_name,
            phone_number=request.phone_number,
            email=request.email,
        )

        return customer_to_response(customer)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[CustomerResponse],
)
def list_customers(
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customers = get_all_customers(db)

    return [
        customer_to_response(customer)
        for customer in customers
    ]


@router.get(
    "/me",
    response_model=CustomerResponse,
)
def get_my_customer(
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
            detail="Customer profile not found.",
        )

    return customer_to_response(customer)