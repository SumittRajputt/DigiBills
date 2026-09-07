import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.authorization import require_role
from app.api.dependencies import get_db
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.schemas.retailer_plan import (
    RetailerPlanResponse,
    RetailerPlanUpdateRequest,
)
from app.services.retailer_plan_service import (
    RETAILER_CUSTOMER_TYPE,
    ensure_retailer_plans,
    parse_json,
)


router = APIRouter(
    prefix="/admin/retailer-plans",
    tags=["Admin Retailer Plans"],
)


def to_response(
    plan: SubscriptionPlan,
) -> RetailerPlanResponse:
    return RetailerPlanResponse(
        id=str(plan.id),
        plan_id=plan.plan_id,
        name=plan.name,
        description=plan.description,
        billing_type=plan.billing_type,
        monthly_price=plan.monthly_price,
        yearly_price=plan.yearly_price,
        trial_days=plan.trial_days,
        features=parse_json(plan.features, []),
        limits=parse_json(plan.limits, {}),
        is_active=plan.is_active,
    )


@router.get(
    "",
    response_model=list[RetailerPlanResponse],
)
def list_retailer_plans(
    current_user: User = Depends(
        require_role("super_admin")
    ),
    db: Session = Depends(get_db),
):
    ensure_retailer_plans(db)

    plans = list(
        db.execute(
            select(SubscriptionPlan)
            .where(
                SubscriptionPlan.customer_type
                == RETAILER_CUSTOMER_TYPE
            )
            .order_by(SubscriptionPlan.name.asc())
        ).scalars()
    )

    return [
        to_response(plan)
        for plan in plans
    ]


@router.put(
    "/{plan_id}",
    response_model=RetailerPlanResponse,
)
def update_retailer_plan(
    plan_id: str,
    request: RetailerPlanUpdateRequest,
    current_user: User = Depends(
        require_role("super_admin")
    ),
    db: Session = Depends(get_db),
):
    plan = db.execute(
        select(SubscriptionPlan).where(
            SubscriptionPlan.plan_id == plan_id,
            SubscriptionPlan.customer_type
            == RETAILER_CUSTOMER_TYPE,
        )
    ).scalar_one_or_none()

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="Retailer subscription plan not found.",
        )

    plan.name = request.name
    plan.description = request.description
    plan.billing_type = request.billing_type
    plan.monthly_price = request.monthly_price
    plan.yearly_price = request.yearly_price
    plan.trial_days = request.trial_days
    plan.features = json.dumps(
        request.features
    )
    plan.limits = json.dumps(
        {
            key: value.model_dump()
            for key, value in request.limits.items()
        }
    )
    plan.is_active = request.is_active

    db.commit()
    db.refresh(plan)

    return to_response(plan)
