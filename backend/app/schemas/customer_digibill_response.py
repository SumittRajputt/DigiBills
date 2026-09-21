from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class CustomerDigiBillProductResponse(BaseModel):
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


class CustomerDigiBillResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    digibill_id: str
    uploaded_bill_id: str
    customer_id: str

    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None

    retailer: Dict[str, Any]
    customer: Dict[str, Any]
    products: List[CustomerDigiBillProductResponse]

    totals: Dict[str, Any]
    payment: Dict[str, Any]
    warranty_evidence: Dict[str, Any]

    confidence_scores: Dict[str, Any]
    extraction_notes: List[str]

    status: str
    confirmed_at: datetime
    created_at: datetime
    updated_at: datetime
