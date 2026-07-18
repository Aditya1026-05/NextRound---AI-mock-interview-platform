import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.dependencies.providers import get_db
from app.main import app


@pytest_asyncio.fixture
async def client(db):
    """Yield an AsyncClient with mocked database dependency override."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_endpoint_success(client):
    email = f"register_api_{uuid.uuid4().hex}@example.com"
    payload = {
        "email": email,
        "password": "secure_password_123",
        "full_name": "API Candidate",
    }

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["email"] == email
    assert data["user"]["full_name"] == "API Candidate"
    assert data["user"]["is_active"] is True
    assert data["user"]["avatar_url"] is None


@pytest.mark.asyncio
async def test_register_endpoint_duplicate_email(client):
    email = f"duplicate_api_{uuid.uuid4().hex}@example.com"
    payload = {
        "email": email,
        "password": "secure_password_123",
        "full_name": "API Candidate",
    }

    # Register first time
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Register second time
    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert res2.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_login_endpoint_success(client):
    email = f"login_api_{uuid.uuid4().hex}@example.com"
    password = "secure_password_123"

    # Pre-register
    reg_payload = {
        "email": email,
        "password": password,
        "full_name": "Login Test Candidate",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {"username": email, "password": password}
    response = await client.post("/api/v1/auth/login", data=login_payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["email"] == email


@pytest.mark.asyncio
async def test_login_endpoint_invalid_credentials(client):
    email = f"login_fail_api_{uuid.uuid4().hex}@example.com"

    # Pre-register
    reg_payload = {
        "email": email,
        "password": "secure_password_123",
        "full_name": "Login Test Candidate",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Login with incorrect password
    login_payload = {"username": email, "password": "wrong_password"}
    response = await client.post("/api/v1/auth/login", data=login_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_refresh_endpoint_success(client):
    email = f"refresh_api_{uuid.uuid4().hex}@example.com"

    # Register
    reg_payload = {
        "email": email,
        "password": "secure_password_123",
        "full_name": "Refresh Candidate",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    refresh_token = reg_res.json()["refresh_token"]

    # Refresh
    refresh_payload = {"refresh_token": refresh_token}
    response = await client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_refresh_endpoint_invalid_token(client):
    refresh_payload = {"refresh_token": "invalid_refresh_token_string"}
    response = await client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
async def test_me_endpoint_authenticated(client):
    email = f"me_api_{uuid.uuid4().hex}@example.com"

    # Register
    reg_payload = {
        "email": email,
        "password": "secure_password_123",
        "full_name": "Me Candidate",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    access_token = reg_res.json()["access_token"]

    # Get /me
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == "Me Candidate"


@pytest.mark.asyncio
async def test_me_endpoint_unauthenticated(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


@pytest.mark.asyncio
async def test_logout_endpoint_authenticated(client):
    email = f"logout_api_{uuid.uuid4().hex}@example.com"

    # Register
    reg_payload = {
        "email": email,
        "password": "secure_password_123",
        "full_name": "Logout Candidate",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    access_token = reg_res.json()["access_token"]

    # Logout
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_logout_endpoint_unauthenticated(client):
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"
