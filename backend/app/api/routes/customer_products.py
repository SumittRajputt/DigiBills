from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.customer import Customer
from app.models.customer_digibill import CustomerDigiBill
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.invoice_item_unit import InvoiceItemUnit
from app.models.product import Product
from app.models.product_ownership import ProductOwnership
from app.models.product_unit import ProductUnit
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.schemas.customer_product import CustomerProductResponse
from app.services.customer_service import get_customer_by_user_id


router = APIRouter(
    prefix="/customer/products",
    tags=["Customer Products"],
)


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        return float(Decimal(str(value)))
    except (ValueError, TypeError, ArithmeticError):
        return None


def _uploaded_product_transfer_status(
    product: dict,
    verified_serial_number: Optional[str] = None,
) -> tuple[bool, str, str]:
    serial_number = product.get("serial_number")
    model_number = product.get("model_number")
    sku = product.get("sku")
    barcode = product.get("barcode")

    if verified_serial_number:
        return (
            True,
            "eligible",
            "Product serial number has been verified and is eligible for transfer.",
        )

    if serial_number or sku or barcode:
        return (
            True,
            "eligible_for_verification",
            "Product has a unique product identifier and can be reviewed for transfer.",
        )

    if model_number:
        return (
            False,
            "verification_required",
            "A model number is available, but no unique serial, SKU, or barcode was found.",
        )

    return (
        False,
        "verification_required",
        "No unique product identifier was found on the uploaded bill.",
    )


@router.get(
    "",
    response_model=list[CustomerProductResponse],
)
def list_customer_products(
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_customer_by_user_id(
        db,
        current_user.id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found for this user.",
        )

    if customer.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer is not active.",
        )

    results: list[CustomerProductResponse] = []

    # ---------------------------------------------------------
    # 1. Existing registered products
    # ---------------------------------------------------------
    rows = db.execute(
        select(
            ProductOwnership,
            ProductUnit,
            ProductVariant,
            Product,
            Invoice,
        )
        .join(
            ProductUnit,
            ProductUnit.id == ProductOwnership.product_unit_id,
        )
        .join(
            ProductVariant,
            ProductVariant.id == ProductUnit.product_variant_id,
        )
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .outerjoin(
            InvoiceItemUnit,
            InvoiceItemUnit.product_unit_id == ProductUnit.id,
        )
        .outerjoin(
            InvoiceItem,
            InvoiceItem.id == InvoiceItemUnit.invoice_item_id,
        )
        .outerjoin(
            Invoice,
            Invoice.id == InvoiceItem.invoice_id,
        )
        .where(
            ProductOwnership.customer_id == customer.id,
            ProductOwnership.ownership_status == "active",
        )
        .order_by(
            ProductOwnership.acquired_at.desc(),
        )
    ).all()

    for (
        ownership,
        product_unit,
        product_variant,
        product,
        invoice,
    ) in rows:
        results.append(
            CustomerProductResponse(
                ownership_id=str(ownership.id),
                product_unit_id=str(product_unit.id),
                product_variant_id=str(product_variant.id),
                product_id=str(product.id),

                product_name=product.name,
                product_code=product.product_code,
                brand=product.brand,
                category=product.category,
                description=product.description,

                variant_name=product_variant.variant_name,
                sku=product_variant.sku,
                barcode=product_variant.barcode,

                serial_number=product_unit.serial_number,
                product_unit_status=product_unit.status,

                ownership_status=ownership.ownership_status,
                acquired_at=ownership.acquired_at,
                released_at=ownership.released_at,
                source=ownership.source,

                invoice_id=(
                    invoice.invoice_id
                    if invoice is not None
                    else None
                ),
                invoice_date=(
                    invoice.invoice_date
                    if invoice is not None
                    else None
                ),
                invoice_number=(
                    invoice.invoice_number
                    if invoice is not None
                    else None
                ),

                transfer_eligible=True,
                transfer_status="eligible",
                transfer_reason=(
                    "Registered product ownership is established."
                ),
            )
        )

    # ---------------------------------------------------------
    # 2. Customer-uploaded DigiBill products
    # ---------------------------------------------------------
    digibills = db.execute(
        select(CustomerDigiBill)
        .where(
            CustomerDigiBill.customer_id == customer.id,
            CustomerDigiBill.status == "confirmed",
        )
        .order_by(
            CustomerDigiBill.invoice_date.desc(),
            CustomerDigiBill.created_at.desc(),
        )
    ).scalars().all()

    # Prevent the same underlying purchased product from appearing
    # multiple times when multiple DigiBill records represent the
    # same purchase. All DigiBill records remain preserved in the database.
    seen_uploaded_products = set()

    for digibill in digibills:
        products = (
            digibill.products
            if isinstance(digibill.products, list)
            else []
        )

        total_amount = None

        if isinstance(digibill.totals, dict):
            total_amount = _to_float(
                digibill.totals.get("total_amount")
            )

        payment = (
            digibill.payment
            if isinstance(digibill.payment, dict)
            else {}
        )

        transaction_reference = payment.get(
            "transaction_reference"
        )

        for product_data in products:
            if not isinstance(product_data, dict):
                continue

            product_name = (
                product_data.get("product_name")
                or "Product from uploaded bill"
            )

            product_key = (
                digibill.invoice_number,
                digibill.invoice_date,
                transaction_reference,
                product_name,
                product_data.get("brand"),
                product_data.get("model_number"),
                product_data.get("total_amount"),
            )

            # Only deduplicate when the purchase has a payment reference.
            # Without one, preserve the records because invoice number alone
            # is not sufficient to prove that two uploads are the same purchase.
            if transaction_reference:
                if product_key in seen_uploaded_products:
                    continue

                seen_uploaded_products.add(product_key)

            transfer_eligible, transfer_status, transfer_reason = (
                _uploaded_product_transfer_status(
                    product_data,
                    verified_serial_number=(
                        digibill.verified_serial_number
                        if digibill.serial_verification_status == "verified"
                        else None
                    ),
                )
            )

            acquired_at = (
                digibill.invoice_date
                or digibill.confirmed_at
                or digibill.created_at
                or datetime.now(timezone.utc)
            )

            results.append(
                CustomerProductResponse(
                    product_name=product_name,
                    brand=product_data.get("brand"),
                    category=product_data.get("category"),
                    description=product_data.get("description"),

                    ownership_id=None,
                    product_unit_id=None,
                    product_variant_id=None,
                    product_id=None,

                    product_code=None,
                    variant_name=None,
                    sku=product_data.get("sku"),
                    barcode=product_data.get("barcode"),
                    serial_number=product_data.get("serial_number"),
                    product_unit_status=None,

                    ownership_status="active",
                    acquired_at=acquired_at,
                    released_at=None,

                    source="uploaded_bill",

                    invoice_id=None,
                    invoice_date=digibill.invoice_date,
                    invoice_number=digibill.invoice_number,

                    digibill_id=digibill.digibill_id,
                    uploaded_bill_id=str(
                        digibill.uploaded_bill_id
                    ),

                    model_number=product_data.get(
                        "model_number"
                    ),
                    quantity=_to_float(
                        product_data.get("quantity")
                    ),
                    unit_price=_to_float(
                        product_data.get("unit_price")
                    ),
                    total_amount=(
                        _to_float(
                            product_data.get("total_amount")
                        )
                        if product_data.get("total_amount")
                        is not None
                        else total_amount
                    ),

                    transfer_eligible=transfer_eligible,
                    transfer_status=transfer_status,
                    transfer_reason=transfer_reason,
                )
            )

    return results
