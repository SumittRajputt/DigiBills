import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.api.dependencies import get_current_salesman, get_db
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.schemas.subscription import (
    BillingUsageCreateRequest,
    BillingUsageResponse,
    SubscriptionCancelResponse,
    SalesmanSubscriptionCreateRequest,
    SubscriptionCreateRequest,
    SubscriptionPlanResponse,
    SubscriptionPaymentRequest,
    SubscriptionResponse,
)
from app.services.retailer_service import get_retailer_by_owner
from app.services.customer_service import (
    get_customer_by_user_id,
)

from app.services.payment_service import (
    create_subscription_payment,
)

from app.services.subscription_service import (
    cancel_subscription,
    create_billing_usage,
    create_subscription,
    get_active_subscription_for_customer,
    get_current_subscription_for_customer,
    get_active_subscription_for_retailer,
    get_plan_by_reference,
    get_subscription_by_reference,
)


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
)


def plan_to_response(
    plan: SubscriptionPlan,
) -> SubscriptionPlanResponse:
    return SubscriptionPlanResponse(
        id=str(plan.id),
        plan_id=plan.plan_id,
        name=plan.name,
        description=plan.description,
        customer_type=plan.customer_type,
        billing_type=plan.billing_type,
        monthly_price=plan.monthly_price,
        yearly_price=plan.yearly_price,
        per_bill_price=plan.per_bill_price,
        trial_days=plan.trial_days,
        features=plan.features,
        limits=plan.limits,
        is_active=plan.is_active,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def subscription_to_response(
    subscription: Subscription,
) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=str(subscription.id),
        subscription_id=subscription.subscription_id,
        plan_id=str(subscription.plan_id),
        retailer_id=(
            str(subscription.retailer_id)
            if subscription.retailer_id
            else None
        ),
        customer_id=(
            str(subscription.customer_id)
            if subscription.customer_id
            else None
        ),
        salesman_id=(
            str(subscription.salesman_id)
            if subscription.salesman_id
            else None
        ),
        status=subscription.status,
        started_at=subscription.started_at,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        trial_ends_at=subscription.trial_ends_at,
        auto_renew=subscription.auto_renew,
        cancelled_at=subscription.cancelled_at,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )


@router.get(
    "/plans",
    response_model=list[SubscriptionPlanResponse],
)
def list_subscription_plans_endpoint(
    customer_type: str,
    current_user: User = Depends(
        require_permission("subscription.view")
    ),
    db: Session = Depends(get_db),
):
    customer_type = customer_type.strip().lower()

    if customer_type not in {"retailer", "customer"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customer_type must be 'retailer' or 'customer'.",
        )

    statement = (
        select(SubscriptionPlan)
        .where(
            SubscriptionPlan.customer_type == customer_type,
            SubscriptionPlan.is_active.is_(True),
        )
        .order_by(SubscriptionPlan.name.asc())
    )

    plans = list(
        db.execute(statement).scalars().all()
    )

    return [
        plan_to_response(plan)
        for plan in plans
    ]


@router.get(
    "/me",
    response_model=SubscriptionResponse,
)
def get_my_subscription_endpoint(
    current_user: User = Depends(
        require_permission("subscription.view")
    ),
    db: Session = Depends(get_db),
):
    retailer = get_retailer_by_owner(
        db,
        current_user.id,
    )

    if retailer is not None:
        subscription = get_active_subscription_for_retailer(
            db,
            retailer.id,
        )
    else:
        customer = db.execute(
            select(Customer).where(
                Customer.user_id == current_user.id
            )
        ).scalar_one_or_none()

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer or retailer account not found.",
            )

        subscription = get_current_subscription_for_customer(
            db,
            customer.id,
        )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found.",
        )

    return subscription_to_response(subscription)


@router.post(
    "/salesman",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_salesman_subscription_endpoint(
    request: SalesmanSubscriptionCreateRequest,
    salesman=Depends(get_current_salesman),
    db: Session = Depends(get_db),
):
    plan = get_plan_by_reference(
        db,
        request.plan_id,
    )

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found.",
        )

    if plan.customer_type != "customer":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Salesmen can only sell customer subscription plans.",
        )

    try:
        customer_id = uuid.UUID(request.customer_id)

        customer = db.execute(
            select(Customer).where(
                Customer.id == customer_id
            )
        ).scalar_one_or_none()

        if customer is None:
            raise ValueError(
                "Customer not found."
            )

        if customer.status != "active":
            raise ValueError(
                "Customer account is not active."
            )

        subscription = create_subscription(
            db=db,
            plan=plan,
            customer_id=customer.id,
            salesman_id=salesman.id,
        )

        return subscription_to_response(subscription)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_subscription_endpoint(
    request: SubscriptionCreateRequest,
    current_user: User = Depends(
        require_permission("subscription.manage")
    ),
    db: Session = Depends(get_db),
):
    plan = get_plan_by_reference(
        db,
        request.plan_id,
    )

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found.",
        )

    retailer = get_retailer_by_owner(
        db,
        current_user.id,
    )

    try:
        if retailer is not None:
            if retailer.status != "active":
                raise ValueError(
                    "Retailer is not active."
                )

            subscription = create_subscription(
                db=db,
                plan=plan,
                retailer_id=retailer.id,
            )

        else:
            customer = db.execute(
                select(Customer).where(
                    Customer.user_id == current_user.id
                )
            ).scalar_one_or_none()

            if customer is None:
                raise ValueError(
                    "Customer account not found."
                )

            if customer.status != "active":
                raise ValueError(
                    "Customer account is not active."
                )

            subscription = create_subscription(
                db=db,
                plan=plan,
                customer_id=customer.id,
            )

        return subscription_to_response(subscription)

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/billing-usage",
    response_model=BillingUsageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_billing_usage_endpoint(
    request: BillingUsageCreateRequest,
    current_user: User = Depends(
        require_permission("subscription.manage")
    ),
    db: Session = Depends(get_db),
):
    subscription = get_subscription_by_reference(
        db,
        request.subscription_id,
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found.",
        )

    invoice_statement = select(Invoice).where(
        Invoice.invoice_id == request.invoice_id
    )

    invoice = db.execute(
        invoice_statement
    ).scalar_one_or_none()

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    customer = db.execute(
        select(Customer).where(
            Customer.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer account not found.",
        )

    if subscription.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found.",
        )

    try:
        usage = create_billing_usage(
            db=db,
            subscription=subscription,
            invoice=invoice,
        )

        return BillingUsageResponse(
            id=str(usage.id),
            usage_id=usage.usage_id,
            subscription_id=str(usage.subscription_id),
            customer_id=str(usage.customer_id),
            invoice_id=str(usage.invoice_id),
            billing_period_start=usage.billing_period_start,
            billing_period_end=usage.billing_period_end,
            quantity=usage.quantity,
            unit_price=usage.unit_price,
            amount=usage.amount,
            created_at=usage.created_at,
        )

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/invoices/{invoice_id}/pay",
)
def pay_subscription_invoice_endpoint(
    invoice_id: str,
    request: SubscriptionPaymentRequest,
    current_user: User = Depends(
        require_permission("subscription.manage")
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
            detail="Customer account not found.",
        )

    invoice = db.execute(
        select(Invoice).where(
            Invoice.invoice_id == invoice_id
        )
    ).scalar_one_or_none()

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if invoice.subscription_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invoice is not a subscription invoice.",
        )

    if invoice.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    try:
        payment = create_subscription_payment(
            db=db,
            invoice=invoice,
            amount=request.amount,
            payment_method=request.payment_method,
            transaction_reference=request.transaction_reference,
            notes=request.notes,
            customer_id=customer.id,
        )

        return {
            "payment_id": payment.payment_id,
            "invoice_id": invoice.invoice_id,
            "amount": payment.amount,
            "payment_status": payment.payment_status,
            "invoice_status": invoice.payment_status,
        }

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/{subscription_id}/cancel",
    response_model=SubscriptionCancelResponse,
)
def cancel_my_subscription_endpoint(
    subscription_id: str,
    current_user: User = Depends(
        require_permission("subscription.cancel")
    ),
    db: Session = Depends(get_db),
):
    subscription = get_subscription_by_reference(
        db,
        subscription_id,
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found.",
        )

    retailer = get_retailer_by_owner(
        db,
        current_user.id,
    )

    owns_subscription = False

    if retailer is not None:
        owns_subscription = (
            subscription.retailer_id == retailer.id
        )
    else:
        customer = db.execute(
            select(Customer).where(
                Customer.user_id == current_user.id
            )
        ).scalar_one_or_none()

        if customer is not None:
            owns_subscription = (
                subscription.customer_id == customer.id
            )

    if not owns_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found.",
        )

    try:
        subscription = cancel_subscription(
            db,
            subscription,
        )

        return SubscriptionCancelResponse(
            subscription_id=subscription.subscription_id,
            status=subscription.status,
            cancelled_at=subscription.cancelled_at,
        )

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
