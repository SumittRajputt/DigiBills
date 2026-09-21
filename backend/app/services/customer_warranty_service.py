from calendar import monthrange
from datetime import date
from decimal import Decimal


def add_months(start_date: date, months: int) -> date:
    """
    Add a number of calendar months to a date.

    If the target month does not contain the original day,
    the last valid day of the target month is used.
    """
    if months < 0:
        raise ValueError("Months cannot be negative.")

    total_months = start_date.year * 12 + (start_date.month - 1) + months

    target_year = total_months // 12
    target_month = total_months % 12 + 1

    target_day = min(
        start_date.day,
        monthrange(target_year, target_month)[1],
    )

    return date(target_year, target_month, target_day)


def calculate_warranty_end_date(
    start_date: date,
    duration_value: Decimal,
    duration_unit: str,
) -> date:
    """
    Calculate warranty end date from start date and duration.
    """
    if duration_value <= 0:
        raise ValueError("Warranty duration must be greater than zero.")

    if duration_unit == "months":
        months = int(duration_value)
    elif duration_unit == "years":
        months = int(duration_value * 12)
    else:
        raise ValueError("Warranty duration unit must be 'months' or 'years'.")

    return add_months(start_date, months)
