import uuid
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_db
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.product import Product
from app.models.product_ownership import ProductOwnership
from app.models.product_transfer import ProductTransfer
from app.models.product_unit import ProductUnit
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.schemas.customer_transfer import (
    CustomerTransferAcceptRequest,
    CustomerTransferCreateRequest,
    CustomerTransferPayRequest,
    CustomerTransferRejectRequest,
)
from app.services.customer_service import get_customer_by_user_id
from app.services.invoice_service import generate_invoice_id
from app.services.payment_configuration_service import (
    get_payment_configuration,
)
from app.services.payment_service import create_payment
from app.services.subscription_service import (
    get_active_subscription_for_customer,
)


router = APIRouter(
    prefix="/customer/transfers",
    tags=["Customer Transfers"],
)


def get_current_customer(
    db: Session,
    current_user: User,
) -> Customer:
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

    return customer


def customer_data(customer: Optional[Customer]):
    if customer is None:
        return None

    return {
        "id": str(customer.id),
        "customer_id": customer.customer_id,
        "full_name": customer.full_name,
        "phone_number": customer.phone_number,
        "email": customer.email,
    }


def get_transfer(
    db: Session,
    transfer_id: str,
) -> ProductTransfer:
    transfer = db.execute(
        select(ProductTransfer).where(
            ProductTransfer.transfer_id == transfer_id
        )
    ).scalar_one_or_none()

    if transfer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found.",
        )

    return transfer


def get_customer_by_identifier(
    db: Session,
    identifier: str,
) -> Optional[Customer]:
    identifier = identifier.strip()

    if not identifier:
        return None

    # Email lookup
    if "@" in identifier:
        return db.execute(
            select(Customer).where(
                Customer.email.ilike(identifier)
            )
        ).scalar_one_or_none()

    # Phone lookup
    return db.execute(
        select(Customer).where(
            Customer.phone_number == identifier
        )
    ).scalar_one_or_none()


def transfer_to_response(
    db: Session,
    transfer: ProductTransfer,
):
    from_customer = db.execute(
        select(Customer).where(
            Customer.id == transfer.from_customer_id
        )
    ).scalar_one_or_none()

    to_customer = db.execute(
        select(Customer).where(
            Customer.id == transfer.to_customer_id
        )
    ).scalar_one_or_none()

    product_data = None

    product_row = db.execute(
        select(
            ProductUnit,
            ProductVariant,
            Product,
        )
        .join(
            ProductVariant,
            ProductVariant.id == ProductUnit.product_variant_id,
        )
        .join(
            Product,
            Product.id == ProductVariant.product_id,
        )
        .where(
            ProductUnit.id == transfer.product_unit_id
        )
    ).first()

    if product_row:
        unit, variant, product = product_row

        product_data = {
            "product_unit_id": str(unit.id),
            "serial_number": unit.serial_number,
            "product_variant_id": str(variant.id),
            "sku": variant.sku,
            "variant_name": variant.variant_name,
            "product_name": product.name,
        }

    payment_invoice = None

    if transfer.payment_invoice_id:
        payment_invoice = db.execute(
            select(Invoice).where(
                Invoice.id == transfer.payment_invoice_id
            )
        ).scalar_one_or_none()

    return {
        "id": str(transfer.id),
        "transfer_id": transfer.transfer_id,
        "product_unit_id": str(transfer.product_unit_id),
        "from_customer_id": str(transfer.from_customer_id),
        "to_customer_id": str(transfer.to_customer_id),
        "from_customer": customer_data(from_customer),
        "to_customer": customer_data(to_customer),
        "requested_by_user_id": str(
            transfer.requested_by_user_id
        ),
        "status": transfer.status,
        "reason": transfer.reason,
        "rejection_reason": transfer.rejection_reason,
        "transfer_fee": transfer.transfer_fee,
        "payment_status": transfer.payment_status,
        "payment_invoice_id": (
            payment_invoice.invoice_id
            if payment_invoice
            else None
        ),
        "payment_reference": transfer.payment_reference,
        "requested_at": transfer.requested_at,
        "accepted_at": transfer.accepted_at,
        "completed_at": transfer.completed_at,
        "created_at": transfer.created_at,
        "updated_at": transfer.updated_at,
        "product": product_data,
    }


@router.get(
    "",
    response_model=list[dict],
)
def list_customer_transfers(
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_current_customer(
        db,
        current_user,
    )

    transfers = db.execute(
        select(ProductTransfer)
        .where(
            or_(
                ProductTransfer.from_customer_id
                == customer.id,
                ProductTransfer.to_customer_id
                == customer.id,
            )
        )
        .order_by(
            ProductTransfer.requested_at.desc(),
            ProductTransfer.created_at.desc(),
        )
    ).scalars().all()

    return [
        transfer_to_response(db, transfer)
        for transfer in transfers
    ]


@router.get(
    "/owned-products",
    response_model=list[dict],
)
def list_owned_transfer_products(
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_current_customer(
        db,
        current_user,
    )

    rows = db.execute(
        select(
            ProductUnit,
            ProductVariant,
            Product,
        )
        .join(
            ProductOwnership,
            ProductOwnership.product_unit_id
            == ProductUnit.id,
        )
        .join(
            ProductVariant,
            ProductVariant.id
            == ProductUnit.product_variant_id,
        )
        .join(
            Product,
            Product.id
            == ProductVariant.product_id,
        )
        .where(
            ProductOwnership.customer_id == customer.id,
            ProductOwnership.ownership_status == "active",
            ProductUnit.status == "sold",
        )
        .order_by(
            ProductUnit.serial_number.asc()
        )
    ).all()

    return [
        {
            "product_unit_id": str(unit.id),
            "serial_number": unit.serial_number,
            "product_variant_id": str(variant.id),
            "sku": variant.sku,
            "variant_name": variant.variant_name,
            "product_name": product.name,
        }
        for unit, variant, product in rows
    ]


@router.get(
    "/incoming",
    response_model=list[dict],
)
def list_incoming_transfers(
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_current_customer(
        db,
        current_user,
    )

    transfers = db.execute(
        select(ProductTransfer)
        .where(
            ProductTransfer.to_customer_id == customer.id,
            ProductTransfer.status
            == "pending_acceptance",
        )
        .order_by(
            ProductTransfer.requested_at.desc()
        )
    ).scalars().all()

    return [
        transfer_to_response(db, transfer)
        for transfer in transfers
    ]


@router.get(
    "/{transfer_id}",
    response_model=dict,
)
def get_customer_transfer(
    transfer_id: str,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_current_customer(
        db,
        current_user,
    )

    transfer = get_transfer(
        db,
        transfer_id,
    )

    if customer.id not in {
        transfer.from_customer_id,
        transfer.to_customer_id,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this transfer.",
        )

    return transfer_to_response(
        db,
        transfer,
    )


@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_transfer(
    request: CustomerTransferCreateRequest,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    sender = get_current_customer(
        db,
        current_user,
    )

    try:
        product_unit_id = uuid.UUID(
            request.product_unit_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product unit not found.",
        )

    product_unit = db.execute(
        select(ProductUnit).where(
            ProductUnit.id == product_unit_id
        )
    ).scalar_one_or_none()

    if product_unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product unit not found.",
        )

    if product_unit.status != "sold":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only sold products can be transferred.",
        )

    ownership = db.execute(
        select(ProductOwnership).where(
            ProductOwnership.product_unit_id
            == product_unit.id,
            ProductOwnership.customer_id
            == sender.id,
            ProductOwnership.ownership_status
            == "active",
        )
    ).scalar_one_or_none()

    if ownership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not currently own this product.",
        )

    receiver = get_customer_by_identifier(
        db,
        request.to_customer_identifier,
    )

    if receiver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination customer not found.",
        )

    if receiver.id == sender.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot transfer a product to yourself.",
        )

    if receiver.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Destination customer is not active.",
        )

    existing_pending = db.execute(
        select(ProductTransfer).where(
            ProductTransfer.product_unit_id
            == product_unit.id,
            ProductTransfer.status
            == "pending_acceptance",
        )
    ).scalar_one_or_none()

    if existing_pending is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This product already has a pending transfer.",
        )

    existing_active = db.execute(
        select(ProductOwnership).where(
            ProductOwnership.product_unit_id
            == product_unit.id,
            ProductOwnership.ownership_status
            == "active",
        )
    ).scalar_one_or_none()

    if (
        existing_active is None
        or existing_active.customer_id != sender.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product ownership changed. Refresh and try again.",
        )

    subscription = get_active_subscription_for_customer(
        db,
        receiver.id,
    )

    if subscription is not None:
        transfer_fee = Decimal("0.00")
        payment_status = "not_required"
    else:
        configuration = get_payment_configuration(db)
        transfer_fee = Decimal(
            configuration.customer_transfer_fee
        )

        if transfer_fee <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Transfer fee is not configured.",
            )

        payment_status = "unpaid"

    transfer = ProductTransfer(
        transfer_id=(
            f"TRF-{uuid.uuid4().hex[:10].upper()}"
        ),
        product_unit_id=product_unit.id,
        from_customer_id=sender.id,
        to_customer_id=receiver.id,
        requested_by_user_id=current_user.id,
        approved_by_user_id=None,
        status="pending_acceptance",
        reason=request.reason,
        rejection_reason=None,
        transfer_fee=transfer_fee,
        payment_status=payment_status,
        payment_invoice_id=None,
        payment_reference=None,
        requested_at=__import__(
            "datetime"
        ).datetime.now(
            __import__("datetime").timezone.utc
        ),
        approved_at=None,
        accepted_at=None,
        completed_at=None,
    )

    db.add(transfer)
    db.flush()

    if transfer_fee > Decimal("0.00"):
        now = __import__(
            "datetime"
        ).datetime.now(
            __import__("datetime").timezone.utc
        )

        invoice = Invoice(
            invoice_id=generate_invoice_id(),
            retailer_id=None,
            employee_id=None,
            customer_id=receiver.id,
            invoice_number=transfer.transfer_id,
            invoice_date=now,
            subtotal=transfer_fee,
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=transfer_fee,
            payment_status="unpaid",
            status="active",
            subscription_id=None,
            billing_period_start=None,
            billing_period_end=None,
            notes=(
                f"Transfer fee for "
                f"{transfer.transfer_id}"
            ),
        )

        db.add(invoice)
        db.flush()

        transfer.payment_invoice_id = invoice.id

    db.commit()
    db.refresh(transfer)

    return transfer_to_response(
        db,
        transfer,
    )


@router.post(
    "/{transfer_id}/pay",
    response_model=dict,
)
def pay_transfer_fee(
    transfer_id: str,
    request: CustomerTransferPayRequest,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_current_customer(
        db,
        current_user,
    )

    transfer = get_transfer(
        db,
        transfer_id,
    )

    if transfer.to_customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the receiving customer can pay this transfer.",
        )

    if transfer.status != "pending_acceptance":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This transfer is no longer awaiting acceptance.",
        )

    if transfer.payment_status == "not_required":
        return transfer_to_response(
            db,
            transfer,
        )

    if transfer.payment_invoice_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transfer payment invoice not found.",
        )

    invoice = db.execute(
        select(Invoice).where(
            Invoice.id == transfer.payment_invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer payment invoice not found.",
        )

    if invoice.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Payment invoice does not belong to you.",
        )

    if invoice.payment_status == "paid":
        transfer.payment_status = "paid"
        db.commit()
        db.refresh(transfer)

        return transfer_to_response(
            db,
            transfer,
        )

    try:
        payment = create_payment(
            db=db,
            invoice=invoice,
            amount=invoice.total_amount,
            payment_method=request.payment_method,
            transaction_reference=(
                request.transaction_reference
                or None
            ),
            notes=(
                f"Transfer fee payment for "
                f"{transfer.transfer_id}"
            ),
            retailer_id=None,
            user_id=current_user.id,
        )

        transfer.payment_status = "paid"
        transfer.payment_reference = payment.payment_id

        db.commit()
        db.refresh(transfer)

        return transfer_to_response(
            db,
            transfer,
        )

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{transfer_id}/accept",
    response_model=dict,
)
def accept_customer_transfer(
    transfer_id: str,
    request: CustomerTransferAcceptRequest,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_current_customer(
        db,
        current_user,
    )

    transfer = get_transfer(
        db,
        transfer_id,
    )

    if transfer.to_customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the receiving customer can accept this transfer.",
        )

    if transfer.status != "pending_acceptance":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending transfers can be accepted.",
        )

    if transfer.payment_status != "not_required":
        if transfer.payment_status != "paid":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Transfer fee must be paid before acceptance.",
            )

    product_unit = db.execute(
        select(ProductUnit)
        .where(
            ProductUnit.id == transfer.product_unit_id
        )
        .with_for_update()
    ).scalar_one_or_none()

    if product_unit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product unit not found.",
        )

    source_ownership = db.execute(
        select(ProductOwnership)
        .where(
            ProductOwnership.product_unit_id
            == product_unit.id,
            ProductOwnership.customer_id
            == transfer.from_customer_id,
            ProductOwnership.ownership_status
            == "active",
        )
        .with_for_update()
    ).scalar_one_or_none()

    if source_ownership is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Source customer no longer owns this product.",
        )

    destination_ownership = db.execute(
        select(ProductOwnership)
        .where(
            ProductOwnership.product_unit_id
            == product_unit.id,
            ProductOwnership.ownership_status
            == "active",
        )
        .with_for_update()
    ).scalar_one_or_none()

    now = __import__(
        "datetime"
    ).datetime.now(
        __import__("datetime").timezone.utc
    )

    if destination_ownership is not None:
        destination_ownership.ownership_status = "released"
        destination_ownership.released_at = now

    source_ownership.ownership_status = "released"
    source_ownership.released_at = now

    new_ownership = ProductOwnership(
        product_unit_id=product_unit.id,
        customer_id=transfer.to_customer_id,
        ownership_status="active",
        acquired_at=now,
        released_at=None,
        source="transfer",
    )

    db.add(new_ownership)

    from app.models.ownership_history import OwnershipHistory

    history = OwnershipHistory(
        product_unit_id=product_unit.id,
        from_customer_id=transfer.from_customer_id,
        to_customer_id=transfer.to_customer_id,
        event_type="transfer",
        reference_type="product_transfer",
        reference_id=transfer.id,
        notes=transfer.reason,
        transferred_at=now,
    )

    db.add(history)

    transfer.status = "completed"
    transfer.accepted_at = now
    transfer.completed_at = now

    db.commit()
    db.refresh(transfer)

    return transfer_to_response(
        db,
        transfer,
    )


@router.post(
    "/{transfer_id}/reject",
    response_model=dict,
)
def reject_customer_transfer(
    transfer_id: str,
    request: CustomerTransferRejectRequest,
    current_user: User = Depends(
        require_permission("customer.view")
    ),
    db: Session = Depends(get_db),
):
    customer = get_current_customer(
        db,
        current_user,
    )

    transfer = get_transfer(
        db,
        transfer_id,
    )

    if transfer.to_customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the receiving customer can reject this transfer.",
        )

    if transfer.status != "pending_acceptance":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending transfers can be rejected.",
        )

    if not request.rejection_reason.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rejection reason is required.",
        )

    transfer.status = "rejected"
    transfer.rejection_reason = (
        request.rejection_reason.strip()
    )

    db.commit()
    db.refresh(transfer)

    return transfer_to_response(
        db,
        transfer,
    )
