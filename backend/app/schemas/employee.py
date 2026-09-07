from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


EmployeeRole = Literal[
    "retailer_manager",
    "cashier",
    "inventory_manager",
    "salesman",
]


class EmployeeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    phone_number: str = Field(min_length=1, max_length=20)
    email: Optional[str] = Field(
        default=None,
        max_length=255,
    )
    password: str = Field(min_length=8, max_length=128)
    employee_type: EmployeeRole


class EmployeeResponse(BaseModel):
    id: str
    employee_id: str
    user_id: str
    retailer_id: str
    name: str
    phone_number: str
    email: Optional[str] = None
    employee_type: str
    status: str
    created_at: datetime
