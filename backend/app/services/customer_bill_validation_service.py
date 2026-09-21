import re

from app.schemas.customer_bill_validation import (
    CustomerBillValidation,
)


def validate_bill_document(text: str) -> CustomerBillValidation:
    """
    Determine whether extracted PDF text appears to represent
    a purchase bill/invoice.

    This is intentionally conservative:
    it should prevent obviously unrelated documents from entering
    the Digital Bill workflow.
    """

    if not text or not text.strip():
        return CustomerBillValidation(
            status="not_bill",
            score=0,
            reasons=["No readable document text was found."],
        )

    normalized = text.lower()

    score = 0
    reasons: list[str] = []

    # ---------------------------------------------------------
    # Invoice / bill number
    # ---------------------------------------------------------
    if re.search(
        r"\b(?:invoice|bill|inv)\s*(?:no|number|#)\b",
        normalized,
    ):
        score += 2
        reasons.append("Invoice or bill number label found.")

    # ---------------------------------------------------------
    # Invoice date
    # ---------------------------------------------------------
    if re.search(
        r"\b(?:invoice\s*)?date\s*[:\-]?",
        normalized,
    ):
        score += 2
        reasons.append("Invoice date label found.")

    # ---------------------------------------------------------
    # Product / item information
    # ---------------------------------------------------------
    if re.search(
        r"\b(?:product|item|description|sku|model|serial)\s*[:#\-]?",
        normalized,
    ):
        score += 2
        reasons.append("Product or item information found.")

    # ---------------------------------------------------------
    # Quantity
    # ---------------------------------------------------------
    if re.search(
        r"\b(?:qty|quantity)\s*[:\-]?",
        normalized,
    ):
        score += 1
        reasons.append("Quantity information found.")

    # ---------------------------------------------------------
    # Financial totals
    # ---------------------------------------------------------
    if re.search(
        r"\b(?:grand\s+total|total\s+amount|invoice\s+total|"
        r"net\s+amount|amount\s+paid|amount\s+due|subtotal)\b",
        normalized,
    ):
        score += 2
        reasons.append("Invoice financial information found.")

    # ---------------------------------------------------------
    # GST / tax evidence
    # ---------------------------------------------------------
    if re.search(
        r"\bgstin\b|\bcgst\b|\bsgst\b|\bigst\b|\bgst\b|\btax\b",
        normalized,
    ):
        score += 1
        reasons.append("Tax or GST information found.")

    # ---------------------------------------------------------
    # Payment evidence
    # ---------------------------------------------------------
    if re.search(
        r"\b(?:payment|paid|upi|cash|card|credit\s+card|"
        r"debit\s+card|transaction|utr)\b",
        normalized,
    ):
        score += 1
        reasons.append("Payment information found.")

    # ---------------------------------------------------------
    # Strong document signals
    # ---------------------------------------------------------
    bill_terms = [
        "invoice",
        "tax invoice",
        "retail invoice",
        "purchase bill",
        "sales invoice",
        "cash memo",
        "bill of sale",
    ]

    matching_bill_terms = [
        term for term in bill_terms
        if term in normalized
    ]

    if matching_bill_terms:
        score += 2
        reasons.append(
            "Purchase/invoice document terminology found."
        )

    # ---------------------------------------------------------
    # Classification
    # ---------------------------------------------------------
    if score >= 5:
        status = "bill"
    elif score >= 3:
        status = "uncertain"
    else:
        status = "not_bill"

    if not reasons:
        reasons.append(
            "Insufficient bill/invoice evidence was found."
        )

    return CustomerBillValidation(
        status=status,
        score=score,
        reasons=reasons,
    )
