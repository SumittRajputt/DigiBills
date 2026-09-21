from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CustomerBillValidationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bill_id: str
    document_status: Optional[str] = None
    validation_score: Optional[int] = None
    validation_reasons: List[str] = []
    digibill_eligible: bool = False
