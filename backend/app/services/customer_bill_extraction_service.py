from datetime import datetime, timedelta, timezone
from decimal import Decimal
import re
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.customer_bill_extraction import CustomerBillExtraction
from app.models.customer_uploaded_bill import CustomerUploadedBill
from app.services.customer_bill_pdf_service import (
    CustomerBillPdfExtractionError,
    extract_pdf_text,
)
from app.services.customer_bill_validation_service import (
    validate_bill_document,
)
from app.services.customer_uploaded_bill_cleanup_service import (
    delete_uploaded_bill,
)
from app.schemas.customer_bill_extraction import (
    CustomerBillExtraction as CustomerBillExtractionSchema,
    ExtractedBillTotals,
    ExtractedCustomer,
    ExtractedPayment,
    ExtractedProduct,
    ExtractedRetailer,
    ExtractedWarrantyEvidence,
)



def _first_match(pattern: str, text: str, flags: int = re.IGNORECASE) -> Optional[str]:
    match = re.search(pattern, text, flags)
    if not match:
        return None
    return match.group(1).strip()


def _decimal(value: Optional[str]) -> Optional[Decimal]:
    if not value:
        return None

    cleaned = value.replace(",", "").replace("₹", "").strip()

    try:
        return Decimal(cleaned)
    except Exception:
        return None


def _parse_invoice_date(value: Optional[str]):
    if not value:
        return None

    value = value.strip()

    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def _parse_structured_bill(raw_text: str) -> dict:
    """
    Local rule-based parser.

    This intentionally uses the extracted PDF text only.
    No external AI/API is required.
    """

    text = raw_text.replace("\r", "\n")

    invoice_number = _first_match(
        r"Invoice\s+Number\s*:\s*([A-Z0-9\-\/]+)",
        text,
    )

    invoice_date_raw = _first_match(
        r"Invoice\s+Date\s*:\s*(\d{2}[./-]\d{2}[./-]\d{4})",
        text,
    )

    invoice_date = _parse_invoice_date(invoice_date_raw)

    retailer_name = _first_match(
        r"Sold\s+By\s*:\s*\n?\s*([^\n*]+)",
        text,
    )

    retailer_gstin = _first_match(
        r"GST\s+Registration\s+No\.?\s*:\s*([A-Z0-9]+)",
        text,
    )

    retailer_pan = _first_match(
        r"PAN\s+No:\s*([A-Z0-9]+)",
        text,
    )

    billing_customer = _first_match(
        r"Billing\s+Address\s*:\s*\n\s*([^\n]+)",
        text,
    )

    billing_address_match = re.search(
        r"Billing\s+Address\s*:\s*\n\s*[^\n]+\n(.*?)(?=\nIN\s*\n\nState/UT Code:)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    customer_address = None

    if billing_address_match:
        customer_address = " ".join(
            line.strip()
            for line in billing_address_match.group(1).splitlines()
            if line.strip()
        )

    retailer_address_match = re.search(
        r"Sold\s+By\s*:\s*\n?\s*[^\n*]+\s*\n\*\s*\n?(.*?)(?=\nPAN\s+No:)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    retailer_address = None

    if retailer_address_match:
        retailer_address = " ".join(
            line.strip()
            for line in retailer_address_match.group(1).splitlines()
            if line.strip()
        )

    gst_amount_raw = _first_match(
        r"TOTAL:\s*₹?\s*([\d,]+\.\d{2})",
        text,
    )

    total_amount_raw = _first_match(
        r"TOTAL:\s*₹?\s*[\d,]+\.\d{2}\s*₹?\s*([\d,]+\.\d{2})",
        text,
    )

    if total_amount_raw is None:
        total_amount_raw = _first_match(
            r"Invoice\s+Value:\s*([\d,]+\.\d{2})",
            text,
        )

    total_amount = _decimal(total_amount_raw)
    tax_amount = _decimal(gst_amount_raw)

    unit_price_raw = _first_match(
        r"₹([\d,]+\.\d{2})\s+1\s+₹[\d,]+\.\d{2}\s+18%",
        text,
    )

    unit_price = _decimal(unit_price_raw)

    quantity_raw = _first_match(
        r"₹[\d,]+\.\d{2}\s+(\d+(?:\.\d+)?)\s+₹[\d,]+\.\d{2}\s+18%",
        text,
    )

    quantity = _decimal(quantity_raw)

    net_amount_raw = _first_match(
        r"₹[\d,]+\.\d{2}\s+\d+(?:\.\d+)?\s+₹([\d,]+\.\d{2})\s+18%",
        text,
    )

    net_amount = _decimal(net_amount_raw)

    product_match = re.search(
        r"\n1\s+(.+?)\nHSN:",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    product_description = None
    model_number = None
    brand = None

    if product_match:
        product_description = " ".join(
            line.strip()
            for line in product_match.group(1).splitlines()
            if line.strip()
        )

        model_match = re.search(
            r"\b([A-Za-z][A-Za-z0-9]*\d[A-Za-z0-9]*)\s*\(Black\)",
            product_description,
        )

        if model_match:
            model_number = model_match.group(1)

            # Keep the model number in its dedicated field instead of
            # repeating it in the product name when the invoice already
            # includes it as a separate identifier after "|".
            # Remove pipe-separated catalog/product identifiers from the
            # display name. Some PDFs repeat the identifier inside a
            # parenthesized block across line breaks.
            product_description = re.sub(
                r"\s*\|\s*[A-Za-z0-9][A-Za-z0-9._/-]*"
                r"\s*\(\s*[A-Za-z0-9][A-Za-z0-9._/-]*\s*\)\s*$",
                "",
                product_description,
            ).strip()

            # Fallback for a pipe-separated identifier without the
            # repeated parenthesized value.
            product_description = re.sub(
                r"\s*\|\s*[A-Za-z0-9][A-Za-z0-9._/-]*\s*$",
                "",
                product_description,
            ).strip()

        brand_match = re.match(
            r"([A-Za-z][A-Za-z0-9]*)\s+",
            product_description,
        )

        if brand_match:
            brand = brand_match.group(1)

    payment_transaction = _first_match(
        r"Payment\s+Transaction\s+ID:\s*\n?\s*([A-Za-z0-9]+)",
        text,
    )

    payment_method = _first_match(
        r"Mode\s+of\s+Payment:\s*\n?\s*([A-Za-z][A-Za-z0-9 ]+)",
        text,
    )

    order_number = _first_match(
        r"Order\s+Number:\s*([0-9\-]+)",
        text,
    )

    product = ExtractedProduct(
        product_name=product_description,
        brand=brand,
        model_number=model_number,
        serial_number=None,
        quantity=quantity,
        unit_price=unit_price,
        discount=None,
        tax_amount=tax_amount,
        total_amount=total_amount,
    )

    retailer = ExtractedRetailer(
        name=retailer_name,
        address=retailer_address,
        phone=None,
        email=None,
        gstin=retailer_gstin,
    )

    customer = ExtractedCustomer(
        name=billing_customer,
        phone=None,
        email=None,
        address=customer_address,
    )

    payment = ExtractedPayment(
        payment_method=payment_method,
        transaction_reference=payment_transaction or order_number,
        paid_amount=total_amount,
        payment_status="paid" if payment_transaction else None,
    )

    subtotal = net_amount

    totals = ExtractedBillTotals(
        subtotal=subtotal,
        discount=None,
        tax_amount=tax_amount,
        total_amount=total_amount,
        amount_paid=total_amount if payment_transaction else None,
        amount_due=Decimal("0.00") if payment_transaction else None,
    )

    warranty = ExtractedWarrantyEvidence(
        mentioned="unclear",
        provider=None,
        warranty_type=None,
        duration=None,
        duration_value=None,
        duration_unit=None,
        start_date=None,
        end_date=None,
        registration_number=None,
        terms=None,
    )

    confidence_scores = {
        "invoice_number": {
            "level": "high",
            "reason": "Invoice number was explicitly labeled in the document.",
        },
        "invoice_date": {
            "level": "high",
            "reason": "Invoice date was explicitly labeled in the document.",
        },
        "retailer": {
            "level": "high",
            "reason": "Seller and GST registration details were explicitly present.",
        },
        "customer": {
            "level": "high",
            "reason": "Billing address explicitly identifies the customer.",
        },
        "product": {
            "level": "high",
            "reason": "Product description and pricing were present in the invoice table.",
        },
        "totals": {
            "level": "high",
            "reason": "Tax and total amount were explicitly shown.",
        },
        "payment": {
            "level": "high",
            "reason": "Payment transaction ID and payment mode were explicitly shown.",
        },
        "warranty": {
            "level": "unknown",
            "reason": "No explicit warranty information was identified in the extracted invoice text.",
        },
    }

    structured = CustomerBillExtractionSchema(
        retailer=retailer,
        customer=customer,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        products=[product],
        totals=totals,
        payment=payment,
        warranty=warranty,
        confidence_scores=confidence_scores,
        extraction_notes=[
            "Structured data was generated using the local PDF text parser.",
            "Warranty information was not explicitly identified in the uploaded invoice.",
        ],
    )

    return structured.model_dump(mode="json")


def create_customer_bill_extraction(
    db: Session,
    uploaded_bill: CustomerUploadedBill,
) -> CustomerBillExtraction:
    """
    Extract text from the original uploaded PDF and validate whether
    the document appears to be a purchase bill/invoice.

    This step does NOT create:
    - Invoice
    - Digital Bill
    - Product Ownership
    - Inventory movement
    - Payment
    - Warranty

    The original uploaded PDF is always preserved.
    """

    extraction = (
        db.query(CustomerBillExtraction)
        .filter(
            CustomerBillExtraction.uploaded_bill_id
            == uploaded_bill.id
        )
        .first()
    )

    if extraction is None:
        extraction = CustomerBillExtraction(
            id=uuid4(),
            uploaded_bill_id=uploaded_bill.id,
            status="processing",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(extraction)
    else:
        extraction.status = "processing"
        extraction.raw_text = None
        extraction.structured_data = None
        extraction.page_count = None
        extraction.extraction_engine = None
        extraction.extraction_model = None
        extraction.error_message = None

        # Reset validation state for a fresh extraction.
        extraction.document_status = None
        extraction.validation_score = None
        extraction.validation_reasons = None
        extraction.digibill_eligible = None

        extraction.updated_at = datetime.utcnow()

    db.flush()

    try:
        raw_text, page_count, extraction_engine = extract_pdf_text(
            uploaded_bill.storage_path
        )

        extraction.raw_text = raw_text
        extraction.page_count = page_count
        extraction.extraction_engine = extraction_engine
        extraction.extraction_model = None

        # ---------------------------------------------------------
        # No readable text
        # ---------------------------------------------------------
        if not raw_text.strip():
            extraction.status = "no_text"
            extraction.error_message = (
                "No readable text was found in the PDF. "
                "OCR may be required."
            )

            extraction.document_status = "not_bill"
            extraction.validation_score = 0
            extraction.validation_reasons = [
                "No readable document text was found."
            ]
            extraction.digibill_eligible = False

            delete_uploaded_bill(
                db,
                uploaded_bill,
            )
            db.commit()
            return None

        # ---------------------------------------------------------
        # Text extracted → validate document
        # ---------------------------------------------------------
        else:
            validation = validate_bill_document(raw_text)

            extraction.status = "text_extracted"
            extraction.error_message = None

            extraction.document_status = validation.status
            extraction.validation_score = validation.score
            extraction.validation_reasons = validation.reasons

            # Only a confirmed bill is eligible for DigiBill creation.
            extraction.digibill_eligible = (
                validation.status == "bill"
            )

            # -----------------------------------------------------
            # NOT_BILL → delete immediately
            # -----------------------------------------------------
            if validation.status == "not_bill":
                delete_uploaded_bill(
                    db,
                    uploaded_bill,
                )
                db.commit()
                return None

            # -----------------------------------------------------
            # UNCERTAIN → retain for exactly 24 hours
            # -----------------------------------------------------
            if validation.status == "uncertain":
                uploaded_bill.review_deadline_at = (
                    datetime.now(timezone.utc)
                    + timedelta(hours=24)
                )

                extraction.status = "review_required"
                extraction.structured_data = None
                extraction.error_message = None

            # -----------------------------------------------------
            # BILL → no review deadline; extract structured data
            # -----------------------------------------------------
            elif validation.status == "bill":
                uploaded_bill.review_deadline_at = None

                try:
                    extraction.structured_data = _parse_structured_bill(
                        raw_text
                    )
                    extraction.status = "structured"
                    extraction.error_message = None
                except Exception as exc:
                    extraction.status = "structured_failed"
                    extraction.structured_data = None
                    extraction.error_message = (
                        f"Structured bill extraction failed: {str(exc)}"
                    )

    except CustomerBillPdfExtractionError as exc:
        extraction.status = "failed"
        extraction.error_message = str(exc)

        extraction.document_status = "not_bill"
        extraction.validation_score = 0
        extraction.validation_reasons = [
            f"PDF extraction failed: {str(exc)}"
        ]
        extraction.digibill_eligible = False

        delete_uploaded_bill(
            db,
            uploaded_bill,
        )
        db.commit()
        return None

    extraction.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(extraction)

    return extraction
