from datetime import date
from decimal import Decimal
from typing import Optional

from app.schemas.customer_bill_extraction import CustomerBillExtraction
from app.schemas.customer_warranty_confirmation import WarrantyConfirmation
from app.services.customer_warranty_service import calculate_warranty_end_date


def prepare_warranty_confirmation(
    extraction: CustomerBillExtraction,
    customer_has_warranty: Optional[bool] = None,
    duration_value: Optional[Decimal] = None,
    duration_unit: Optional[str] = None,
) -> WarrantyConfirmation:
    """
    Prepare warranty confirmation data using information extracted from
    the uploaded bill.

    Customer input is requested only when required.
    """

    warranty = extraction.warranty
    invoice_date = extraction.invoice_date

    # ---------------------------------------------------------
    # 1. Determine warranty status
    # ---------------------------------------------------------
    if warranty.mentioned == "no":
        has_warranty = "no"

    elif customer_has_warranty is True:
        has_warranty = "yes"

    elif customer_has_warranty is False:
        has_warranty = "no"

    else:
        has_warranty = "unknown"

    # ---------------------------------------------------------
    # 2. Warranty start date
    # ---------------------------------------------------------
    # Invoice date is the default warranty start date.
    start_date: Optional[date] = invoice_date

    # ---------------------------------------------------------
    # 3. Duration
    # ---------------------------------------------------------
    # Prefer duration extracted from the bill.
    # Customer-provided duration is used only when the bill
    # does not contain a usable duration.
    final_duration_value = duration_value
    final_duration_unit = duration_unit

    if final_duration_value is None:
        final_duration_value = warranty.duration_value

    if final_duration_unit is None:
        final_duration_unit = warranty.duration_unit

    end_date: Optional[date] = None

    if (
        has_warranty == "yes"
        and start_date is not None
        and final_duration_value is not None
        and final_duration_unit is not None
    ):
        end_date = calculate_warranty_end_date(
            start_date=start_date,
            duration_value=final_duration_value,
            duration_unit=final_duration_unit,
        )

    # ---------------------------------------------------------
    # 4. Extract everything available from the bill.
    # ---------------------------------------------------------
    return WarrantyConfirmation(
        has_warranty=has_warranty,
        provider=warranty.provider,
        warranty_type=warranty.warranty_type,
        start_date=start_date,
        duration_value=final_duration_value,
        duration_unit=final_duration_unit,
        end_date=end_date,
        warranty_number=warranty.registration_number,
        important_terms=warranty.terms,
        confirmed=False,
    )
