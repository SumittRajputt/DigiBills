from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CustomerProductResponse(BaseModel):
    ownership_id: str
    product_unit_id: str
    product_variant_id: str
    product_id: str

    product_name: str
    product_code: str
    brand: Optional[str]
    category: Optional[str]
    description: Optional[str]

    variant_name: str
    sku: str
    barcode: Optional[str]

    serial_number: str
    product_unit_status: str

    ownership_status: str
    acquired_at: datetime
    released_at: Optional[datetime]
    source: str
