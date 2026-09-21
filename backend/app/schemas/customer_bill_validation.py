from typing import Literal

from pydantic import BaseModel, ConfigDict


BillDocumentStatus = Literal[
    "bill",
    "uncertain",
    "not_bill",
]


class CustomerBillValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: BillDocumentStatus
    score: int
    reasons: list[str]
