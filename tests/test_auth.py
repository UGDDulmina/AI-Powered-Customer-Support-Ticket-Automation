from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.support_agent import SupportAgent


def create_test_agent(
    db: Session,
    email: str,
    role: str = "agent",
    password: str = "SecurePassword123!",
):
    agent = SupportAgent(
        name="Test Agent",
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return agent


def get_auth_headers(agent: SupportAgent):
    token = create_access_token(agent.id)

    return {
        "Authorization": f"Bearer {token}"
    }


def test_password_hashing():
    password = "SecurePassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword123!", hashed)


def test_login_success(
    client: TestClient,
    db_session: Session,
):
    create_test_agent(
        db_session,
        email="login@example.com",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(
    client: TestClient,
    db_session: Session,
):
    create_test_agent(
        db_session,
        email="invalid@example.com",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "invalid@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_login_inactive_agent(
    client: TestClient,
    db_session: Session,
):
    agent = create_test_agent(
        db_session,
        email="inactive@example.com",
    )

    agent.is_active = False
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 401


def test_get_current_agent(
    client: TestClient,
    db_session: Session,
):
    agent = create_test_agent(
        db_session,
        email="profile@example.com",
    )

    response = client.get(
        "/api/v1/auth/me",
        headers=get_auth_headers(agent),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == agent.id
    assert data["email"] == "profile@example.com"
    assert data["role"] == "agent"


def test_get_current_agent_without_token(
    client: TestClient,
):
    response = client.get("/api/v1/auth/me")

    assert response.status_code in (401, 403)


def test_get_current_agent_invalid_token(
    client: TestClient,
):
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401


def test_get_current_agent_expired_token(
    client: TestClient,
    db_session: Session,
):
    agent = create_test_agent(
        db_session,
        email="expired@example.com",
    )

    token = create_access_token(
        agent.id,
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 401


def test_admin_can_register_agent(
    client: TestClient,
    db_session: Session,
):
    admin = create_test_agent(
        db_session,
        email="admin@example.com",
        role="admin",
    )

    response = client.post(
        "/api/v1/agents/register",
        headers=get_auth_headers(admin),
        json={
            "name": "New Support Agent",
            "email": "newagent@example.com",
            "password": "SecurePassword123!",
            "role": "agent",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "newagent@example.com"
    assert data["role"] == "agent"
    assert "password_hash" not in data
    assert "password" not in data

    created_agent = db_session.get(
        SupportAgent,
        data["id"],
    )

    assert created_agent is not None
    assert created_agent.password_hash != "SecurePassword123!"
    assert verify_password(
        "SecurePassword123!",
        created_agent.password_hash,
    )


def test_agent_cannot_register_agent(
    client: TestClient,
    db_session: Session,
):
    agent = create_test_agent(
        db_session,
        email="regular@example.com",
        role="agent",
    )

    response = client.post(
        "/api/v1/agents/register",
        headers=get_auth_headers(agent),
        json={
            "name": "Unauthorized Agent",
            "email": "unauthorized@example.com",
            "password": "SecurePassword123!",
            "role": "agent",
        },
    )

    assert response.status_code == 403


def test_registration_requires_authentication(
    client: TestClient,
):
    response = client.post(
        "/api/v1/agents/register",
        json={
            "name": "Unknown Agent",
            "email": "unknown@example.com",
            "password": "SecurePassword123!",
            "role": "agent",
        },
    )

    assert response.status_code in (401, 403)


def test_duplicate_agent_email(
    client: TestClient,
    db_session: Session,
):
    admin = create_test_agent(
        db_session,
        email="duplicate-admin@example.com",
        role="admin",
    )

    create_test_agent(
        db_session,
        email="existing@example.com",
    )

    response = client.post(
        "/api/v1/agents/register",
        headers=get_auth_headers(admin),
        json={
            "name": "Duplicate Agent",
            "email": "existing@example.com",
            "password": "SecurePassword123!",
            "role": "agent",
        },
    )

    assert response.status_code == 409