from fastapi import APIRouter

from app.api.routes.audit_log import (
    router as audit_log_router,
)
from app.api.routes.admin_dashboard import (
    router as admin_dashboard_router,
)
from app.api.routes.admin_purchase_return import (
    router as admin_purchase_return_router,
)
from app.api.routes.auth import (
    router as auth_router,
)
from app.api.routes.customer import (
    router as customer_router,
)
from app.api.routes.health import (
    router as health_router,
)
from app.api.routes.inventory import (
    router as inventory_router,
)
from app.api.routes.inventory_location import (
    router as inventory_location_router,
)
from app.api.routes.invoice import (
    router as invoice_router,
)
from app.api.routes.payment import (
    router as payment_router,
)
from app.api.routes.product import (
    router as product_router,
)
from app.api.routes.product_ownership import (
    router as product_ownership_router,
)
from app.api.routes.product_unit import (
    router as product_unit_router,
)
from app.api.routes.product_transfer import (
    router as product_transfer_router,
)
from app.api.routes.product_variant import (
    router as product_variant_router,
)
from app.api.routes.purchase_order import (
    router as purchase_order_router,
)
from app.api.routes.purchase_return import (
    router as purchase_return_router,
)
from app.api.routes.retailer import (
    router as retailer_router,
)
from app.api.routes.role import (
    router as role_router,
)
from app.api.routes.sales_return import (
    router as sales_return_router,
)
from app.api.routes.stock_movement import (
    router as stock_movement_router,
)
from app.api.routes.supplier import (
    router as supplier_router,
)
from app.api.routes.subscription import (
    router as subscription_router,
)
from app.api.routes.warranty import (
    router as warranty_router,
)
from app.api.routes.user import (
    router as user_router,
)


api_router = APIRouter()


api_router.include_router(
    health_router
)

api_router.include_router(
    auth_router
)

api_router.include_router(
    customer_router
)

api_router.include_router(
    retailer_router
)

api_router.include_router(
    role_router
)

api_router.include_router(
    product_router
)

api_router.include_router(
    product_variant_router
)

api_router.include_router(
    product_ownership_router
)

api_router.include_router(
    product_unit_router
)
api_router.include_router(
    product_transfer_router
)
api_router.include_router(
    inventory_location_router
)

api_router.include_router(
    inventory_router
)

api_router.include_router(
    stock_movement_router
)

api_router.include_router(
    supplier_router
)

api_router.include_router(
    subscription_router
)

api_router.include_router(
    purchase_order_router
)

api_router.include_router(
    purchase_return_router
)

api_router.include_router(
    invoice_router
)

api_router.include_router(
    sales_return_router
)

api_router.include_router(
    payment_router
)

api_router.include_router(
    audit_log_router
)

api_router.include_router(
    admin_dashboard_router
)

api_router.include_router(
    admin_purchase_return_router
)

api_router.include_router(
    warranty_router
)

api_router.include_router(
    user_router
)
