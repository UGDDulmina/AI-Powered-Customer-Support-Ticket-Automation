import os
import pytest

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.main import app
from app.db.dependencies import get_db

from sqlalchemy.engine import make_url

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not configured")

parsed_url = make_url(TEST_DATABASE_URL)

if parsed_url.database != "ai_support_test_db":
    raise RuntimeError("Refusing to test against a non-test database")

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

def override_get_db():

    database_session = TestingSessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()

@pytest.fixture
def db_session():

    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(
        bind=connection,
        join_transaction_mode="create_savepoint"
    )

    try:
        yield session

    finally:
        session.close()
        transaction.rollback()
        connection.close()

    

@pytest.fixture
def client(db_session):

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def sample_customer():
    return{
    "name": "John Smith",
    "email": "john.smith@example.com",
    "phone": "0771234567"
}

@pytest.fixture
def created_customer(client, sample_customer):

    response = client.post(
        "/api/v1/customers",
        json=sample_customer
    )

    assert response.status_code == 201

    return response.json()

@pytest.fixture
def created_ticket(client, created_customer):

    ticket_data = {
        "customer_id": created_customer["id"],
        "subject": "Unable to log in",
        "description": "I cannot access my account.",
        "priority": "medium"
    }

    response = client.post(
        "/api/v1/tickets",
        json=ticket_data
    )

    assert response.status_code == 201

    return response.json()

 