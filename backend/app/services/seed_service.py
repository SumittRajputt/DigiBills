from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_control import role_permissions
from app.models.permission import Permission
from app.models.role import Role


ROLES: List[Dict[str, str]] = [
    {
        "name": "super_admin",
        "description": "Full DigiBills platform administration access.",
    },
    {
        "name": "retailer_owner",
        "description": "Full access to the retailer's business.",
    },
    {
        "name": "retailer_manager",
        "description": "Operational management access for a retailer.",
    },
    {
        "name": "cashier",
        "description": "Billing and customer-facing sales access.",
    },
    {
        "name": "inventory_manager",
        "description": "Inventory and purchasing management access.",
    },
    {
        "name": "salesman",
        "description": "Sales access for selling products and DigiBills subscriptions.",
    },
    {
        "name": "customer",
        "description": "Customer account access.",
    },
]


PERMISSIONS: List[Dict[str, str]] = [
    {
        "name": "user.view",
        "description": "View platform user information.",
    },
    {
        "name": "user.manage",
        "description": "Manage platform users and their roles.",
    },
    {
        "name": "retailer.view",
        "description": "View retailer information.",
    },
    {
        "name": "retailer.manage",
        "description": "Manage retailer information.",
    },
    {
        "name": "product.view",
        "description": "View products and product variants.",
    },
    {
        "name": "product.manage",
        "description": "Create and manage products and variants.",
    },
    {
        "name": "inventory.view",
        "description": "View inventory and stock levels.",
    },
    {
        "name": "inventory.manage",
        "description": "Manage inventory and stock movements.",
    },
    {
        "name": "invoice.view",
        "description": "View invoices and billing records.",
    },
    {
        "name": "invoice.create",
        "description": "Create new invoices.",
    },
    {
        "name": "invoice.manage",
        "description": "Manage invoices and billing records.",
    },
    {
        "name": "customer.view",
        "description": "View customer information.",
    },
    {
        "name": "customer.manage",
        "description": "Create and manage customer information.",
    },
    {
        "name": "employee.view",
        "description": "View retailer employees.",
    },
    {
        "name": "employee.manage",
        "description": "Manage retailer employees.",
    },
    {
        "name": "analytics.view",
        "description": "View retailer business analytics and dashboards.",
    },
    {
        "name": "payment.view",
        "description": "View payment records.",
    },
    {
        "name": "payment.manage",
        "description": "Manage payments and refunds.",
    },
    {
        "name": "sales_return.view",
        "description": "View sales returns.",
    },
    {
        "name": "sales_return.manage",
        "description": "Process and manage sales returns.",
    },
    {
        "name": "purchase_order.view",
        "description": "View purchase orders.",
    },
    {
        "name": "purchase_order.manage",
        "description": "Create and manage purchase orders.",
    },
    {
        "name": "supplier.view",
        "description": "View suppliers.",
    },
    {
        "name": "supplier.manage",
        "description": "Create and manage suppliers.",
    },
    {
        "name": "audit_log.view",
        "description": "View retailer audit logs.",
    },
    {
        "name": "subscription.view",
        "description": "View subscription plans and subscription status.",
    },
    {
        "name": "subscription.manage",
        "description": "Create and manage subscriptions.",
    },
    {
        "name": "subscription.cancel",
        "description": "Cancel subscriptions.",
    },
]


ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "super_admin": [
        permission["name"]
        for permission in PERMISSIONS
    ],
    "retailer_owner": [
        permission["name"]
        for permission in PERMISSIONS
    ],
    "retailer_manager": [
        "retailer.view",
        "product.view",
        "product.manage",
        "inventory.view",
        "inventory.manage",
        "invoice.view",
        "invoice.create",
        "invoice.manage",
        "customer.view",
        "customer.manage",
        "employee.view",
        "analytics.view",
        "payment.view",
        "payment.manage",
        "sales_return.view",
        "sales_return.manage",
        "purchase_order.view",
        "purchase_order.manage",
        "supplier.view",
        "supplier.manage",
    ],
    "cashier": [
        "product.view",
        "inventory.view",
        "invoice.view",
        "invoice.create",
        "customer.view",
        "customer.manage",
        "payment.view",
        "payment.manage",
        "sales_return.view",
    ],
    "inventory_manager": [
        "product.view",
        "product.manage",
        "inventory.view",
        "inventory.manage",
        "purchase_order.view",
        "purchase_order.manage",
        "supplier.view",
        "supplier.manage",
    ],
    "salesman": [
        "product.view",
        "inventory.view",
        "invoice.view",
        "invoice.create",
        "customer.view",
        "customer.manage",
        "payment.view",
        "subscription.view",
        "subscription.manage",
    ],
    "customer": [
        "customer.view",
        "invoice.view",
        "subscription.view",
        "subscription.manage",
        "subscription.cancel",
    ],
}


def seed_roles(db: Session) -> Dict[str, Role]:
    roles: Dict[str, Role] = {}

    for role_data in ROLES:
        statement = select(Role).where(
            Role.name == role_data["name"]
        )

        role = db.execute(
            statement
        ).scalar_one_or_none()

        if role is None:
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
            )

            db.add(role)
            db.flush()

        roles[role.name] = role

    return roles


def seed_permissions(
    db: Session,
) -> Dict[str, Permission]:
    permissions: Dict[str, Permission] = {}

    for permission_data in PERMISSIONS:
        statement = select(Permission).where(
            Permission.name == permission_data["name"]
        )

        permission = db.execute(
            statement
        ).scalar_one_or_none()

        if permission is None:
            permission = Permission(
                name=permission_data["name"],
                description=permission_data["description"],
            )

            db.add(permission)
            db.flush()

        permissions[permission.name] = permission

    return permissions


def seed_role_permissions(
    db: Session,
    roles: Dict[str, Role],
    permissions: Dict[str, Permission],
) -> None:
    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role = roles[role_name]

        for permission_name in permission_names:
            permission = permissions[permission_name]

            statement = select(
                role_permissions.c.role_id
            ).where(
                role_permissions.c.role_id == role.id,
                role_permissions.c.permission_id
                == permission.id,
            )

            exists = db.execute(
                statement
            ).first()

            if exists is None:
                db.execute(
                    role_permissions.insert().values(
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                )


def seed_authorization_data(
    db: Session,
) -> None:
    roles = seed_roles(db)
    permissions = seed_permissions(db)

    seed_role_permissions(
        db=db,
        roles=roles,
        permissions=permissions,
    )

    db.commit()