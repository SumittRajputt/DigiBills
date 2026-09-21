from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CustomerBillConfirmationProduct(BaseModel):
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


class CustomerBillConfirmationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bill_id: str
    eligible: bool

    retailer: dict
    customer: dict

    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None

    products: List[CustomerBillConfirmationProduct] = []

    totals: dict
    payment: dict
    warranty: dict

    confidence_scores: dict = {}
    extraction_notes: List[str] = []
