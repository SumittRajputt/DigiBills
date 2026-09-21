from datetime import date
from decimal import Decimal
from typing import List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


ConfidenceLevel = Literal[
    "high",
    "medium",
    "low",
    "unknown",
]


class ExtractionFieldConfidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: ConfidenceLevel = "unknown"
    reason: Optional[str] = None


class ExtractedRetailer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None


class ExtractedCustomer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class ExtractedProduct(BaseModel):
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


class ExtractedPayment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_method: Optional[str] = None
    transaction_reference: Optional[str] = None
    paid_amount: Optional[Decimal] = None
    payment_status: Optional[str] = None


class ExtractedWarrantyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mentioned: Literal[
        "yes",
        "no",
        "unclear",
    ] = "unclear"

    provider: Optional[str] = None
    warranty_type: Optional[str] = None
    duration: Optional[str] = None
    duration_value: Optional[Decimal] = None
    duration_unit: Optional[Literal["months", "years"]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    registration_number: Optional[str] = None
    terms: Optional[str] = None


class ExtractedBillTotals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subtotal: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    amount_paid: Optional[Decimal] = None
    amount_due: Optional[Decimal] = None


class CustomerBillExtraction(BaseModel):
    """
    Structured representation of information extracted from a
    customer self-uploaded PDF bill.

    This schema is intentionally separate from the existing
    retailer Invoice / InvoiceItem models.
    """

    model_config = ConfigDict(extra="forbid")

    retailer: ExtractedRetailer = Field(
        default_factory=ExtractedRetailer
    )

    customer: ExtractedCustomer = Field(
        default_factory=ExtractedCustomer
    )

    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None

    products: List[ExtractedProduct] = Field(
        default_factory=list
    )

    totals: ExtractedBillTotals = Field(
        default_factory=ExtractedBillTotals
    )

    payment: ExtractedPayment = Field(
        default_factory=ExtractedPayment
    )

    warranty: ExtractedWarrantyEvidence = Field(
        default_factory=ExtractedWarrantyEvidence
    )

    confidence_scores: dict[str, ExtractionFieldConfidence] = Field(
        default_factory=dict
    )

    extraction_notes: List[str] = Field(
        default_factory=list
    )
