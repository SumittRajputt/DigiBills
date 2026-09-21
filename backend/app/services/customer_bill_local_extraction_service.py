import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy.orm import Session

from app.models.customer_bill_extraction import CustomerBillExtraction
from app.schemas.customer_bill_extraction import (
    CustomerBillExtraction as CustomerBillExtractionSchema,
    ExtractionFieldConfidence,
    ExtractedProduct,
)


INVOICE_NUMBER_PATTERNS = [
    r"(?:invoice\s*(?:no|number|#)|bill\s*(?:no|number|#)|inv\s*(?:no|number|#))\s*[:\-]?\s*([A-Z0-9][A-Z0-9./_-]{2,})",
]

GSTIN_PATTERN = r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b"

PHONE_PATTERN = r"(?:\+91[\s-]?)?[6-9]\d{9}"
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

DATE_PATTERNS = [
    r"(?:invoice\s*)?date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    r"(?:invoice\s*)?date\s*[:\-]?\s*(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})",
]

SERIAL_PATTERNS = [
    r"(?:serial\s*(?:number|no|#)|s\.?\s*no\.?)\s*[:\-]?\s*([A-Z0-9][A-Z0-9._/-]{3,})",
]

MODEL_PATTERNS = [
    r"(?:model\s*(?:number|no|#)?)\s*[:\-]?\s*([A-Z0-9][A-Z0-9._/-]{2,})",
]

QUANTITY_PATTERNS = [
    r"(?:qty|quantity)\s*[:\-]?\s*(\d+(?:\.\d+)?)",
]

AMOUNT_PATTERNS = {
    "total_amount": [
        r"(?:grand\s*total|total\s*amount|invoice\s*total|net\s*amount|total)\s*[:\-]?\s*[₹Rs.]?\s*([\d,]+(?:\.\d{1,2})?)",
    ],
    "amount_paid": [
        r"(?:amount\s*paid|paid|received)\s*[:\-]?\s*[₹Rs.]?\s*([\d,]+(?:\.\d{1,2})?)",
    ],
    "amount_due": [
        r"(?:amount\s*due|balance\s*due|due)\s*[:\-]?\s*[₹Rs.]?\s*([\d,]+(?:\.\d{1,2})?)",
    ],
}

WARRANTY_PATTERNS = [
    r"(.{0,80}\bwarranty\b.{0,120})",
]


def _search_first(patterns: list[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def _parse_decimal(value: Optional[str]) -> Optional[Decimal]:
    if value is None:
        return None

    cleaned = value.replace(",", "").strip()

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _parse_date(value: Optional[str]):
    if not value:
        return None

    formats = [
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d-%m-%y",
        "%d/%m/%y",
        "%d %B %Y",
        "%d %b %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def _confidence(
    value: Optional[str],
    reason: str,
) -> ExtractionFieldConfidence:
    if value:
        return ExtractionFieldConfidence(
            level="high",
            reason=reason,
        )

    return ExtractionFieldConfidence(
        level="unknown",
        reason="Field was not found in the bill text.",
    )


def _extract_labeled_value(
    labels: list[str],
    text: str,
) -> Optional[str]:
    label_pattern = "|".join(re.escape(label) for label in labels)

    pattern = (
        rf"(?:{label_pattern})"
        rf"\s*[:\-]?\s*(.+)"
    )

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    if match:
        value = match.group(1).strip()
        return value.splitlines()[0].strip()

    return None


def _extract_phone(text: str) -> Optional[str]:
    match = re.search(PHONE_PATTERN, text)

    if match:
        return match.group(0).strip()

    return None


def _extract_email(text: str) -> Optional[str]:
    match = re.search(EMAIL_PATTERN, text)

    if match:
        return match.group(0).strip()

    return None


def _extract_customer_details(text: str) -> dict:
    name = _extract_labeled_value(
        [
            "customer name",
            "customer",
            "bill to",
            "billed to",
            "buyer name",
        ],
        text,
    )

    if name:
        name = re.sub(
            r"\s+(?:customer phone|phone|mobile|email|address)\b.*$",
            "",
            name,
            flags=re.IGNORECASE,
        ).strip()

    phone = None
    email = None
    address = None

    customer_match = re.search(
        r"(?:customer|bill\s*to|billed\s*to|buyer)"
        r"(.*?)(?=\n\s*(?:invoice|item|product|description|subtotal|total|gst|payment|warranty)\b|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if customer_match:
        block = customer_match.group(1)

        phone_match = re.search(PHONE_PATTERN, block)
        email_match = re.search(EMAIL_PATTERN, block)

        if phone_match:
            phone = phone_match.group(0).strip()

        if email_match:
            email = email_match.group(0).strip()

        address_match = re.search(
            r"(?:address)\s*[:\-]?\s*(.+)",
            block,
            flags=re.IGNORECASE,
        )

        if address_match:
            address = address_match.group(1).strip().splitlines()[0]

    return {
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
    }


def _extract_retailer_name(lines: list[str]) -> Optional[str]:
    ignored = {
        "invoice",
        "tax invoice",
        "bill",
        "customer bill",
        "receipt",
    }

    for line in lines[:10]:
        normalized = line.strip()

        if not normalized:
            continue

        if normalized.lower() in ignored:
            continue

        if re.search(r"\b(invoice|bill|receipt|gstin|date|phone|mobile)\b",
                     normalized,
                     re.IGNORECASE):
            continue

        return normalized

    return None


def _extract_product_blocks(text: str) -> list[str]:
    """
    Split a bill into product blocks using explicit Product/Item labels.

    This intentionally relies on explicit product labels rather than
    guessing where arbitrary invoice table rows begin.
    """
    matches = list(
        re.finditer(
            r"(?im)^(?:product|item|description)\s*:\s*",
            text,
        )
    )

    if not matches:
        return []

    blocks = []

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)

        block = text[start:end].strip()

        if block:
            blocks.append(block)

    return blocks


def _extract_product_from_block(
    block: str,
    invoice_total: Optional[Decimal],
    invoice_tax: Optional[Decimal],
) -> ExtractedProduct:
    product_name_match = re.search(
        r"(?im)^(?:product|item|description)\s*:\s*(.+)$",
        block,
    )

    product_name = (
        product_name_match.group(1).strip()
        if product_name_match
        else None
    )

    model_number = _search_first(
        MODEL_PATTERNS,
        block,
    )

    serial_number = _search_first(
        SERIAL_PATTERNS,
        block,
    )

    quantity_raw = _search_first(
        QUANTITY_PATTERNS,
        block,
    )

    quantity = _parse_decimal(quantity_raw)

    unit_price_raw = _search_first(
        [
            r"(?:unit\s*price|price\s*per\s*unit)"
            r"\s*[:\-]?\s*[₹Rs.]?\s*([\d,]+(?:\.\d{1,2})?)"
        ],
        block,
    )

    unit_price = _parse_decimal(unit_price_raw)

    product_total_raw = _search_first(
        [
            r"(?:line\s*total|item\s*total|product\s*total)"
            r"\s*[:\-]?\s*[₹Rs.]?\s*([\d,]+(?:\.\d{1,2})?)"
        ],
        block,
    )

    product_total = _parse_decimal(product_total_raw)

    # If there is no explicit product total, calculate it from
    # quantity × unit price when both values are available.
    if product_total is None and quantity is not None and unit_price is not None:
        product_total = quantity * unit_price

    return ExtractedProduct(
        product_name=product_name,
        model_number=model_number,
        serial_number=serial_number,
        quantity=quantity,
        unit_price=unit_price,
        total_amount=product_total,
    )


def _extract_product_name(text: str) -> Optional[str]:
    product_blocks = _extract_product_blocks(text)

    if product_blocks:
        match = re.search(
            r"(?im)^(?:product|item|description)\s*:\s*(.+)$",
            product_blocks[0],
        )

        if match:
            return match.group(1).strip()

    return None



def extract_bill_structured_data(
    raw_text: str,
) -> CustomerBillExtractionSchema:
    text = raw_text.strip()

    if not text:
        raise ValueError("Bill text is empty.")

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    invoice_number = _search_first(INVOICE_NUMBER_PATTERNS, text)
    invoice_date_raw = _search_first(DATE_PATTERNS, text)
    invoice_date = _parse_date(invoice_date_raw)

    gstin_match = re.search(
        GSTIN_PATTERN,
        text,
        flags=re.IGNORECASE,
    )
    gstin = gstin_match.group(0).upper() if gstin_match else None

    retailer_phone = _extract_phone(text)
    retailer_email = _extract_email(text)

    retailer_address = _extract_labeled_value(
        [
            "seller address",
            "retailer address",
            "shop address",
            "store address",
        ],
        text,
    )

    if retailer_address is None and len(lines) >= 2:
        second_line = lines[1]

        if not re.search(
            r"\b(?:phone|mobile|email|gstin|invoice|date|customer|bill)\b",
            second_line,
            flags=re.IGNORECASE,
        ):
            retailer_address = second_line

    customer_details = _extract_customer_details(text)

    serial_number = _search_first(SERIAL_PATTERNS, text)
    model_number = _search_first(MODEL_PATTERNS, text)
    quantity_raw = _search_first(QUANTITY_PATTERNS, text)
    quantity = _parse_decimal(quantity_raw)

    total_amount_raw = None

    total_matches = re.findall(
        r"(?:grand\s*total|total\s*amount|invoice\s*total|net\s*amount)"
        r"\s*[:\-]?\s*[₹Rs.]?\s*([\d,]+(?:\.\d{1,2})?)",
        text,
        flags=re.IGNORECASE,
    )

    if total_matches:
        total_amount_raw = total_matches[-1]
    else:
        total_amount_raw = _search_first(
            AMOUNT_PATTERNS["total_amount"],
            text,
        )
    paid_amount_raw = _search_first(
        AMOUNT_PATTERNS["amount_paid"],
        text,
    )
    due_amount_raw = _search_first(
        AMOUNT_PATTERNS["amount_due"],
        text,
    )

    total_amount = _parse_decimal(total_amount_raw)
    paid_amount = _parse_decimal(paid_amount_raw)
    due_amount = _parse_decimal(due_amount_raw)

    unit_price_raw = _search_first(
        [
            r"(?:unit\s*price|price\s*per\s*unit)"
            r"\s*[:\-]?\s*[₹Rs.]?\s*([\d,]+(?:\.\d{1,2})?)"
        ],
        text,
    )

    unit_price = _parse_decimal(unit_price_raw)

    subtotal_raw = _search_first(
        [
            r"(?:subtotal|sub\s*total)"
            r"\s*[:\-]?\s*[₹Rs.]?\s*([\d,]+(?:\.\d{1,2})?)"
        ],
        text,
    )

    subtotal = _parse_decimal(subtotal_raw)

    cgst_raw = _search_first(
        [
            r"cgst[^\d]*([\d,]+(?:\.\d{1,2})?)"
        ],
        text,
    )

    sgst_raw = _search_first(
        [
            r"sgst[^\d]*([\d,]+(?:\.\d{1,2})?)"
        ],
        text,
    )

    igst_raw = _search_first(
        [
            r"igst[^\d]*([\d,]+(?:\.\d{1,2})?)"
        ],
        text,
    )

    cgst = _parse_decimal(cgst_raw)
    sgst = _parse_decimal(sgst_raw)
    igst = _parse_decimal(igst_raw)

    tax_amount = None

    tax_values = [
        value for value in [cgst, sgst, igst]
        if value is not None
    ]

    if tax_values:
        tax_amount = sum(tax_values, Decimal("0"))

    payment_method = _extract_labeled_value(
        [
            "payment method",
            "payment mode",
            "mode of payment",
        ],
        text,
    )

    transaction_reference = _extract_labeled_value(
        [
            "transaction reference",
            "transaction ref",
            "upi reference",
            "utr",
            "reference number",
        ],
        text,
    )

    retailer_name = _extract_retailer_name(lines)
    product_name = _extract_product_name(text)

    warranty_match = None

    for pattern in WARRANTY_PATTERNS:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if match:
            warranty_match = match.group(1).strip()
            break

    warranty_mentioned = "yes" if warranty_match else "unclear"

    # Extract warranty duration only from explicit warranty wording.
    # Examples:
    #   Warranty: 1 Year Manufacturer Warranty
    #   Warranty: 2 Years
    #   Warranty: 6 Months
    #   12 Month Warranty
    warranty_duration = None
    warranty_duration_value = None
    warranty_duration_unit = None

    if warranty_match:
        duration_match = re.search(
            r"\b(\d+(?:\.\d+)?)\s*(year|years|yr|yrs|month|months|mo|mos)\b",
            warranty_match,
            flags=re.IGNORECASE,
        )

        if duration_match:
            warranty_duration = duration_match.group(0).strip()
            warranty_duration_value = Decimal(duration_match.group(1))
            unit = duration_match.group(2).lower()

            if unit in {"year", "years", "yr", "yrs"}:
                warranty_duration_unit = "years"
            else:
                warranty_duration_unit = "months"

    products = []

    product_blocks = _extract_product_blocks(text)

    if product_blocks:
        for block in product_blocks:
            products.append(
                _extract_product_from_block(
                    block=block,
                    invoice_total=total_amount,
                    invoice_tax=tax_amount,
                )
            )
    elif product_name or serial_number or model_number or quantity:
        products.append(
            ExtractedProduct(
                product_name=product_name,
                model_number=model_number,
                serial_number=serial_number,
                quantity=quantity,
                unit_price=unit_price,
                tax_amount=tax_amount,
                total_amount=total_amount,
            )
        )

    confidence_scores = {
        "invoice_number": _confidence(
            invoice_number,
            "Matched an invoice/bill number label.",
        ),
        "invoice_date": _confidence(
            invoice_date_raw,
            "Matched an invoice date label.",
        ),
        "retailer_name": _confidence(
            retailer_name,
            "Selected the first bill-header line that did not look like a document label.",
        ),
        "gstin": _confidence(
            gstin,
            "Matched the standard 15-character GSTIN structure.",
        ),
        "retailer_phone": _confidence(
            retailer_phone,
            "Matched an Indian mobile/phone number.",
        ),
        "retailer_email": _confidence(
            retailer_email,
            "Matched an email address.",
        ),
        "retailer_address": _confidence(
            retailer_address,
            "Matched an address label associated with the seller.",
        ),
        "customer_name": _confidence(
            customer_details.get("name"),
            "Matched a customer/buyer label.",
        ),
        "serial_number": _confidence(
            serial_number,
            "Matched a serial-number label.",
        ),
        "model_number": _confidence(
            model_number,
            "Matched a model-number label.",
        ),
        "quantity": _confidence(
            quantity_raw,
            "Matched a quantity label.",
        ),
        "total_amount": _confidence(
            total_amount_raw,
            "Matched the final invoice total.",
        ),
        "unit_price": _confidence(
            unit_price_raw,
            "Matched a unit price label.",
        ),
        "subtotal": _confidence(
            subtotal_raw,
            "Matched a subtotal label.",
        ),
        "tax_amount": _confidence(
            cgst_raw or sgst_raw or igst_raw,
            "Calculated from explicit CGST, SGST or IGST amounts.",
        ),
        "payment_method": _confidence(
            payment_method,
            "Matched a payment method label.",
        ),
        "transaction_reference": _confidence(
            transaction_reference,
            "Matched a transaction/reference label.",
        ),
    }

    extraction_notes = []

    if not product_name:
        extraction_notes.append(
            "Product name was not confidently identified by the local parser."
        )

    if warranty_mentioned == "yes":
        extraction_notes.append(
            f"Warranty wording found in bill: {warranty_match}"
        )
    else:
        extraction_notes.append(
            "No explicit warranty wording was confidently identified."
        )

    return CustomerBillExtractionSchema(
        retailer={
            "name": retailer_name,
            "address": retailer_address,
            "phone": retailer_phone,
            "email": retailer_email,
            "gstin": gstin,
        },
        customer=customer_details,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        products=products,
        totals={
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "amount_paid": paid_amount,
            "amount_due": due_amount,
        },
        payment={
            "payment_method": payment_method,
            "transaction_reference": transaction_reference,
            "paid_amount": paid_amount,
        },
        warranty={
            "mentioned": warranty_mentioned,
            "duration": warranty_duration,
            "duration_value": warranty_duration_value,
            "duration_unit": warranty_duration_unit,
            "terms": warranty_match,
        },
        confidence_scores=confidence_scores,
        extraction_notes=extraction_notes,
    )


def extract_and_store_local_bill_data(
    db: Session,
    extraction: CustomerBillExtraction,
) -> CustomerBillExtraction:
    if not extraction.raw_text or not extraction.raw_text.strip():
        extraction.status = "no_text"
        extraction.error_message = (
            "No readable bill text is available for local extraction."
        )
        db.commit()
        db.refresh(extraction)
        return extraction

    try:
        extraction.status = "local_processing"
        extraction.error_message = None
        db.flush()

        structured = extract_bill_structured_data(
            extraction.raw_text
        )

        extraction.structured_data = structured.model_dump(
            mode="json"
        )
        extraction.extraction_model = "local-rules-v1"
        extraction.status = "extracted"
        extraction.error_message = None

    except Exception as exc:
        extraction.status = "failed"
        extraction.error_message = str(exc)
        raise

    finally:
        from datetime import datetime

        extraction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(extraction)

    return extraction
