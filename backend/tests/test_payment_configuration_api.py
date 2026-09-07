from decimal import Decimal
from uuid import uuid4

from app.models.access_control import user_roles
from app.models.payment_configuration import PaymentConfiguration
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import create_user_token


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def reset_payment_configuration(db):
    db.query(PaymentConfiguration).delete()
    db.commit()


def create_user_with_role(db, role_name):
    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
        status="active",
    )
    db.add(user)
    db.flush()

    role = db.query(Role).filter(
        Role.name == role_name
    ).one()

    db.execute(
        user_roles.insert().values(
            user_id=user.id,
            role_id=role.id,
        )
    )

    db.commit()
    db.refresh(user)

    return user


def test_payment_configuration_requires_authentication(client):
    response = client.get(
        "/admin/payment-configuration"
    )

    assert response.status_code == 401


def test_payment_configuration_requires_super_admin(
    client,
    db,
):
    user = create_user_with_role(
        db,
        "retailer_owner",
    )

    token = create_user_token(user)

    response = client.get(
        "/admin/payment-configuration",
        headers=auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Role 'super_admin' is required."
    )


def test_super_admin_gets_default_payment_configuration(
    client,
    db,
):
    reset_payment_configuration(db)

    user = create_user_with_role(
        db,
        "super_admin",
    )

    token = create_user_token(user)

    response = client.get(
        "/admin/payment-configuration",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"]
    assert data["per_bill_charge"] == "9.00"
    assert data["max_cash_due_invoices"] == 20
    assert data["annual_subscription_price"] == "0.00"
    assert data["salesman_commission_percent"] == "20.00"


def test_super_admin_can_update_payment_configuration(
    client,
    db,
):
    reset_payment_configuration(db)

    user = create_user_with_role(
        db,
        "super_admin",
    )

    token = create_user_token(user)

    response = client.put(
        "/admin/payment-configuration",
        headers=auth_headers(token),
        json={
            "per_bill_charge": "10.00",
            "max_cash_due_invoices": 25,
            "annual_subscription_price": "999.00",
            "salesman_commission_percent": "20.00",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["per_bill_charge"] == "10.00"
    assert data["max_cash_due_invoices"] == 25
    assert data["annual_subscription_price"] == "999.00"
    assert data["salesman_commission_percent"] == "20.00"


def test_updated_payment_configuration_persists(
    client,
    db,
):
    reset_payment_configuration(db)

    user = create_user_with_role(
        db,
        "super_admin",
    )

    token = create_user_token(user)

    update_response = client.put(
        "/admin/payment-configuration",
        headers=auth_headers(token),
        json={
            "per_bill_charge": "12.50",
            "max_cash_due_invoices": 30,
            "annual_subscription_price": "1499.00",
            "salesman_commission_percent": "18.00",
        },
    )

    assert update_response.status_code == 200

    get_response = client.get(
        "/admin/payment-configuration",
        headers=auth_headers(token),
    )

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["per_bill_charge"] == "12.50"
    assert data["max_cash_due_invoices"] == 30
    assert data["annual_subscription_price"] == "1499.00"
    assert data["salesman_commission_percent"] == "18.00"


def test_payment_configuration_rejects_invalid_values(
    client,
    db,
):
    reset_payment_configuration(db)

    user = create_user_with_role(
        db,
        "super_admin",
    )

    token = create_user_token(user)

    response = client.put(
        "/admin/payment-configuration",
        headers=auth_headers(token),
        json={
            "per_bill_charge": "-1.00",
            "max_cash_due_invoices": 20,
            "annual_subscription_price": "999.00",
            "salesman_commission_percent": "20.00",
        },
    )

    assert response.status_code == 422


def test_payment_configuration_rejects_commission_over_100(
    client,
    db,
):
    reset_payment_configuration(db)

    user = create_user_with_role(
        db,
        "super_admin",
    )

    token = create_user_token(user)

    response = client.put(
        "/admin/payment-configuration",
        headers=auth_headers(token),
        json={
            "per_bill_charge": "9.00",
            "max_cash_due_invoices": 20,
            "annual_subscription_price": "999.00",
            "salesman_commission_percent": "101.00",
        },
    )

    assert response.status_code == 422
