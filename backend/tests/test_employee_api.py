from uuid import uuid4

from app.models.access_control import user_roles
from app.models.employee import Employee
from app.models.retailer import Retailer
from app.models.role import Role
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.services.auth_service import create_user_token
from app.services.retailer_plan_service import ensure_retailer_plans


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_retailer_owner_context(db):
    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
        status="active",
    )
    db.add(user)
    db.flush()

    role = db.query(Role).filter(
        Role.name == "retailer_owner"
    ).one()

    db.execute(
        user_roles.insert().values(
            user_id=user.id,
            role_id=role.id,
        )
    )

    retailer = Retailer(
        retailer_id=f"RET-EMP-{uuid4().hex[:8].upper()}",
        owner_user_id=user.id,
        business_name="Employee Test Retailer",
        phone_number=user.phone_number,
        status="active",
    )
    db.add(retailer)
    db.flush()

    db.commit()

    return {
        "user": user,
        "retailer": retailer,
        "token": create_user_token(user),
    }


def get_retailer_plan(db, plan_id="retailer_basic"):
    ensure_retailer_plans(db)

    return db.query(SubscriptionPlan).filter(
        SubscriptionPlan.plan_id == plan_id
    ).one()


def create_subscription_for_retailer(
    db,
    retailer,
    plan,
):
    subscription = Subscription(
        subscription_id=f"SUB-EMP-{uuid4().hex[:8].upper()}",
        plan_id=plan.id,
        retailer_id=retailer.id,
        customer_id=None,
        status="active",
        started_at=plan.created_at,
        current_period_start=plan.created_at,
        current_period_end=plan.created_at,
        trial_ends_at=None,
        auto_renew=True,
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


def test_employee_creation_requires_authentication(client):
    response = client.post(
        "/employees",
        json={
            "name": "Test Employee",
            "phone_number": f"8{uuid4().hex[:9]}",
            "password": "password123",
            "employee_type": "cashier",
        },
    )

    assert response.status_code == 401


def test_employee_creation_requires_permission(
    client,
    db,
):
    user = User(
        phone_number=f"7{uuid4().hex[:9]}",
        status="active",
    )
    db.add(user)
    db.flush()

    role = db.query(Role).filter(
        Role.name == "customer"
    ).one()

    db.execute(
        user_roles.insert().values(
            user_id=user.id,
            role_id=role.id,
        )
    )

    db.commit()

    token = create_user_token(user)

    response = client.post(
        "/employees",
        headers=auth_headers(token),
        json={
            "name": "Test Employee",
            "phone_number": f"8{uuid4().hex[:9]}",
            "password": "password123",
            "employee_type": "cashier",
        },
    )

    assert response.status_code == 403


def test_create_employee(
    client,
    db,
):
    context = create_retailer_owner_context(db)

    plan = get_retailer_plan(
        db,
        "retailer_basic",
    )

    plan.limits = (
        '{"invoices":{"unlimited":false,"limit":100},'
        '"employees":{"unlimited":false,"limit":2},'
        ''
        '"products":{"unlimited":false,"limit":10}}'
    )

    db.commit()

    create_subscription_for_retailer(
        db,
        context["retailer"],
        plan,
    )

    phone = f"8{uuid4().hex[:9]}"

    response = client.post(
        "/employees",
        headers=auth_headers(context["token"]),
        json={
            "name": "Cashier One",
            "phone_number": phone,
            "password": "password123",
            "employee_type": "cashier",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["employee_id"].startswith("EMP-")
    assert data["name"] == "Cashier One"
    assert data["phone_number"] == phone
    assert data["employee_type"] == "cashier"
    assert data["status"] == "active"
    assert data["retailer_id"] == str(
        context["retailer"].id
    )

    employee = db.query(Employee).filter(
        Employee.employee_id == data["employee_id"]
    ).one()

    assert employee.retailer_id == context["retailer"].id


def test_employee_limit_blocks_creation(
    client,
    db,
):
    context = create_retailer_owner_context(db)

    plan = get_retailer_plan(
        db,
        "retailer_basic",
    )

    plan.limits = (
        '{"invoices":{"unlimited":false,"limit":100},'
        '"employees":{"unlimited":false,"limit":1},'
        ''
        '"products":{"unlimited":false,"limit":10}}'
    )

    db.commit()

    create_subscription_for_retailer(
        db,
        context["retailer"],
        plan,
    )

    first_response = client.post(
        "/employees",
        headers=auth_headers(context["token"]),
        json={
            "name": "First Employee",
            "phone_number": f"8{uuid4().hex[:9]}",
            "password": "password123",
            "employee_type": "cashier",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/employees",
        headers=auth_headers(context["token"]),
        json={
            "name": "Second Employee",
            "phone_number": f"8{uuid4().hex[:9]}",
            "password": "password123",
            "employee_type": "cashier",
        },
    )

    assert second_response.status_code == 403
    assert "Employee limit of 1" in (
        second_response.json()["detail"]
    )


def test_unlimited_employee_plan_allows_creation(
    client,
    db,
):
    context = create_retailer_owner_context(db)

    plan = get_retailer_plan(
        db,
        "retailer_pro",
    )

    plan.limits = (
        '{"invoices":{"unlimited":true,"limit":1},'
        '"employees":{"unlimited":true,"limit":1},'
        ''
        '"products":{"unlimited":true,"limit":1}}'
    )

    db.commit()

    create_subscription_for_retailer(
        db,
        context["retailer"],
        plan,
    )

    for employee_type in (
        "cashier",
        "inventory_manager",
        "retailer_manager",
    ):
        response = client.post(
            "/employees",
            headers=auth_headers(context["token"]),
            json={
                "name": f"{employee_type} Employee",
                "phone_number": f"8{uuid4().hex[:9]}",
                "password": "password123",
                "employee_type": employee_type,
            },
        )

        assert response.status_code == 201


def test_list_employees(
    client,
    db,
):
    context = create_retailer_owner_context(db)

    plan = get_retailer_plan(
        db,
        "retailer_basic",
    )

    plan.limits = (
        '{"invoices":{"unlimited":false,"limit":100},'
        '"employees":{"unlimited":false,"limit":2},'
        ''
        '"products":{"unlimited":false,"limit":10}}'
    )

    db.commit()

    create_subscription_for_retailer(
        db,
        context["retailer"],
        plan,
    )

    response = client.post(
        "/employees",
        headers=auth_headers(context["token"]),
        json={
            "name": "List Test Employee",
            "phone_number": f"8{uuid4().hex[:9]}",
            "password": "password123",
            "employee_type": "cashier",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/employees",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "List Test Employee"
    assert data[0]["employee_type"] == "cashier"
