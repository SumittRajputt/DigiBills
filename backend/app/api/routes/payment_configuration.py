from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.authorization import require_role
from app.api.dependencies import get_db
from app.models.user import User
from app.schemas.payment_configuration import (
    PaymentConfigurationResponse,
    PaymentConfigurationUpdateRequest,
)
from app.services.payment_configuration_service import (
    get_payment_configuration,
    update_payment_configuration,
)


router = APIRouter(
    prefix="/admin/payment-configuration",
    tags=["Admin Payment Configuration"],
)


def configuration_to_response(
    configuration,
) -> PaymentConfigurationResponse:
    return PaymentConfigurationResponse(
        id=str(configuration.id),
        per_bill_charge=configuration.per_bill_charge,
        customer_bill_charge=configuration.customer_bill_charge,
        customer_transfer_fee=configuration.customer_transfer_fee,
        max_cash_due_invoices=configuration.max_cash_due_invoices,
        annual_subscription_price=(
            configuration.annual_subscription_price
        ),
        salesman_commission_percent=(
            configuration.salesman_commission_percent
        ),
    )


@router.get(
    "",
    response_model=PaymentConfigurationResponse,
)
def get_payment_configuration_endpoint(
    current_user: User = Depends(
        require_role("super_admin")
    ),
    db: Session = Depends(get_db),
):
    configuration = get_payment_configuration(db)

    return configuration_to_response(configuration)


@router.put(
    "",
    response_model=PaymentConfigurationResponse,
)
def update_payment_configuration_endpoint(
    request: PaymentConfigurationUpdateRequest,
    current_user: User = Depends(
        require_role("super_admin")
    ),
    db: Session = Depends(get_db),
):
    configuration = update_payment_configuration(
        db,
        per_bill_charge=request.per_bill_charge,
        customer_bill_charge=request.customer_bill_charge,
        customer_transfer_fee=request.customer_transfer_fee,
        max_cash_due_invoices=request.max_cash_due_invoices,
        annual_subscription_price=(
            request.annual_subscription_price
        ),
        salesman_commission_percent=(
            request.salesman_commission_percent
        ),
    )

    return configuration_to_response(configuration)
