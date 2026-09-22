import os

import pytest
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.api.dependencies import get_db
from app.services.seed_service import seed_authorization_data


TEST_DATABASE_URL = (
    "postgresql+psycopg://"
    "digibills:digibills_dev_password"
    "@localhost:5432/digibills_test"
)

engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture
def db():
    session = TestingSessionLocal()

    try:
        seed_authorization_data(session)
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_razorpay_order(monkeypatch):
    class MockOrder:
        def create(self, payload):
            return {
                "id": f"order_test_{uuid4().hex[:16]}",
                "amount": payload["amount"],
                "currency": payload["currency"],
                "receipt": payload["receipt"],
            }

    class MockRazorpayClient:
        def __init__(self):
            self.order = MockOrder()

    monkeypatch.setattr(
        "app.api.routes.customer_uploaded_bills._get_razorpay_client",
        lambda: MockRazorpayClient(),
    )

    return MockRazorpayClient
