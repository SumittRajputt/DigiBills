import uuid

from app.models.access_control import user_roles
from app.models.audit_log import AuditLog
from app.models.retailer import Retailer
from app.models.role import Role
from app.models.user import User
from app.services.auth_service import create_user_token


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_audit_log_api_context(db):
    user = User(
        phone_number=f"7{uuid.uuid4().hex[:9]}",
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
    db.flush()

    retailer = Retailer(
        retailer_id=f"RET-AUD-API-{uuid.uuid4().hex[:6].upper()}",
        owner_user_id=user.id,
        business_name="Audit Log API Retailer",
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


def create_audit_log(
    db,
    retailer_id,
    user_id=None,
    action="CREATE",
    entity_type="product",
    entity_id=None,
    description="API audit log test",
    ip_address="127.0.0.1",
    user_agent="pytest",
):
    audit_log = AuditLog(
        retailer_id=retailer_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def test_list_audit_logs_api(client, db):
    context = create_audit_log_api_context(db)

    first = create_audit_log(
        db=db,
        retailer_id=context["retailer"].id,
        user_id=context["user"].id,
        action="CREATE",
        entity_type="product",
        description="Created product",
    )

    second = create_audit_log(
        db=db,
        retailer_id=context["retailer"].id,
        user_id=context["user"].id,
        action="UPDATE",
        entity_type="invoice",
        description="Updated invoice",
    )

    response = client.get(
        "/audit-logs",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    returned_ids = {
        item["id"]
        for item in data
    }

    assert str(first.id) in returned_ids
    assert str(second.id) in returned_ids


def test_list_audit_logs_api_returns_expected_fields(
    client,
    db,
):
    context = create_audit_log_api_context(db)

    audit_log = create_audit_log(
        db=db,
        retailer_id=context["retailer"].id,
        user_id=context["user"].id,
        action="CREATE",
        entity_type="customer",
        entity_id=uuid.uuid4(),
        description="Created customer",
        ip_address="192.168.1.10",
        user_agent="TestAgent",
    )

    response = client.get(
        "/audit-logs",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    item = data[0]

    assert item["id"] == str(audit_log.id)
    assert item["retailer_id"] == str(
        context["retailer"].id
    )
    assert item["user_id"] == str(
        context["user"].id
    )
    assert item["action"] == "CREATE"
    assert item["entity_type"] == "customer"
    assert item["entity_id"] == str(
        audit_log.entity_id
    )
    assert item["description"] == "Created customer"
    assert item["ip_address"] == "192.168.1.10"
    assert item["user_agent"] == "TestAgent"
    assert item["created_at"]


def test_list_audit_logs_api_returns_empty_list(
    client,
    db,
):
    context = create_audit_log_api_context(db)

    response = client.get(
        "/audit-logs",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_audit_logs_api_is_scoped_to_current_retailer(
    client,
    db,
):
    context = create_audit_log_api_context(db)

    other_user = User(
        phone_number=f"8{uuid.uuid4().hex[:9]}",
        status="active",
    )
    db.add(other_user)
    db.flush()

    other_retailer = Retailer(
        retailer_id=f"RET-AUD-OTHER-{uuid.uuid4().hex[:6].upper()}",
        owner_user_id=other_user.id,
        business_name="Other Audit Retailer",
        phone_number=other_user.phone_number,
        status="active",
    )
    db.add(other_retailer)
    db.flush()

    own_log = create_audit_log(
        db=db,
        retailer_id=context["retailer"].id,
        user_id=context["user"].id,
        description="Own retailer log",
    )

    other_log = create_audit_log(
        db=db,
        retailer_id=other_retailer.id,
        user_id=other_user.id,
        description="Other retailer log",
    )

    response = client.get(
        "/audit-logs",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    returned_ids = {
        item["id"]
        for item in data
    }

    assert str(own_log.id) in returned_ids
    assert str(other_log.id) not in returned_ids


def test_get_audit_log_api(client, db):
    context = create_audit_log_api_context(db)

    audit_log = create_audit_log(
        db=db,
        retailer_id=context["retailer"].id,
        user_id=context["user"].id,
        action="DELETE",
        entity_type="product",
        description="Deleted product",
    )

    response = client.get(
        f"/audit-logs/{audit_log.id}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(audit_log.id)
    assert data["retailer_id"] == str(
        context["retailer"].id
    )
    assert data["user_id"] == str(
        context["user"].id
    )
    assert data["action"] == "DELETE"
    assert data["entity_type"] == "product"
    assert data["description"] == "Deleted product"


def test_get_audit_log_api_returns_404_for_unknown_log(
    client,
    db,
):
    context = create_audit_log_api_context(db)

    response = client.get(
        f"/audit-logs/{uuid.uuid4()}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Audit log not found."


def test_get_audit_log_api_rejects_invalid_id(
    client,
    db,
):
    context = create_audit_log_api_context(db)

    response = client.get(
        "/audit-logs/not-a-uuid",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid audit log ID."


def test_get_audit_log_api_is_scoped_to_current_retailer(
    client,
    db,
):
    context = create_audit_log_api_context(db)

    other_user = User(
        phone_number=f"8{uuid.uuid4().hex[:9]}",
        status="active",
    )
    db.add(other_user)
    db.flush()

    other_retailer = Retailer(
        retailer_id=f"RET-AUD-OTHER-{uuid.uuid4().hex[:6].upper()}",
        owner_user_id=other_user.id,
        business_name="Other Audit Retailer",
        phone_number=other_user.phone_number,
        status="active",
    )
    db.add(other_retailer)
    db.flush()

    other_log = create_audit_log(
        db=db,
        retailer_id=other_retailer.id,
        user_id=other_user.id,
        description="Private other retailer log",
    )

    response = client.get(
        f"/audit-logs/{other_log.id}",
        headers=auth_headers(context["token"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Audit log not found."


def test_list_audit_logs_api_requires_authentication(client):
    response = client.get("/audit-logs")

    assert response.status_code == 401


def test_get_audit_log_api_requires_authentication(client):
    response = client.get(
        f"/audit-logs/{uuid.uuid4()}"
    )

    assert response.status_code == 401
