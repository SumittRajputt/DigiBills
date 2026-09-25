from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CustomerProductResponse(BaseModel):
    # Common product identity
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

    # Registered-product architecture
    ownership_id: Optional[str] = None
    product_unit_id: Optional[str] = None
    product_variant_id: Optional[str] = None
    product_id: Optional[str] = None

    product_code: Optional[str] = None
    variant_name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    serial_number: Optional[str] = None
    product_unit_status: Optional[str] = None

    # Ownership
    ownership_status: str
    acquired_at: datetime
    released_at: Optional[datetime] = None

    # Source
    source: str

    # Bill information
    invoice_id: Optional[str] = None
    invoice_date: Optional[datetime] = None
    invoice_number: Optional[str] = None

    # Uploaded DigiBill information
    digibill_id: Optional[str] = None
    uploaded_bill_id: Optional[str] = None
    model_number: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None

    # Transfer
    transfer_eligible: bool = False
    transfer_status: Optional[str] = None
    transfer_reason: Optional[str] = None
