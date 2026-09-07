from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User


security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    user_id = decode_access_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active.",
        )

    return user

def get_current_salesman(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.employee import Employee

    salesman = (
        db.query(Employee)
        .filter(
            Employee.user_id == current_user.id,
            Employee.employee_type == "salesman",
            Employee.status == "active",
        )
        .first()
    )

    if salesman is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active salesman account is required.",
        )

    return salesman


def get_current_employee(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.employee import Employee

    employee = (
        db.query(Employee)
        .filter(
            Employee.user_id == current_user.id,
            Employee.status == 'active',
        )
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Active employee account is required.',
        )

    return employee
