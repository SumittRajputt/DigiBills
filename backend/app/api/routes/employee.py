from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreateRequest,
    EmployeeResponse,
)
from app.services.employee_service import (
    create_employee,
    get_retailer_employees,
)


router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


def to_response(employee) -> EmployeeResponse:
    return EmployeeResponse(
        id=str(employee.id),
        employee_id=employee.employee_id,
        user_id=str(employee.user_id),
        retailer_id=str(employee.retailer_id),
        name=employee.name,
        phone_number=employee.user.phone_number
        if employee.user
        else "",
        email=employee.user.email
        if employee.user
        else None,
        employee_type=employee.employee_type,
        status=employee.status,
        created_at=employee.created_at,
    )


@router.get(
    "",
    response_model=list[EmployeeResponse],
)
def list_employees(
    current_user: User = Depends(
        require_permission("employee.view")
    ),
    db: Session = Depends(get_db),
):
    try:
        employees = get_retailer_employees(
            db,
            current_user,
        )

        return [
            to_response(employee)
            for employee in employees
        ]

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee_endpoint(
    request: EmployeeCreateRequest,
    current_user: User = Depends(
        require_permission("employee.manage")
    ),
    db: Session = Depends(get_db),
):
    try:
        employee = create_employee(
            db=db,
            owner_user=current_user,
            name=request.name,
            phone_number=request.phone_number,
            email=request.email,
            password=request.password,
            employee_type=request.employee_type,
        )

        return to_response(employee)

    except ValueError as exc:
        detail = str(exc)

        if "limit of" in detail:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail,
            )

        if "already exists" in detail:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail,
            )

        if "not found" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
