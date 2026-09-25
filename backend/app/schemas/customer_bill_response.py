from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class CustomerBillProductResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_name: Optional[str] = None
    brand: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None


class CustomerBillResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    bill_id: str
    bill_number: Optional[str] = None
    bill_date: Optional[datetime] = None

    products: List[CustomerBillProductResponse]

    subtotal: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Decimal

    payment_status: str
    status: str

    retailer_name: Optional[str] = None

    uploaded_bill_id: Optional[str] = None
    digibill_id: Optional[str] = None

    created_at: datetime
    updated_at: datetime
