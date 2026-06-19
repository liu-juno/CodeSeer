"""
TDD tests for authentication: /api/auth/login and /api/auth/me
Written BEFORE production code.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.models.models import User, UserRole


@pytest_asyncio.fixture
async def user_with_password(db):
    """创建一个有密码的用户"""
    from app.core.auth import hash_password
    u = User(
        id="auth-user-001",
        email="dev@codeseer.io",
        name="Dev User",
        role=UserRole.DEVELOPER,
        password_hash=hash_password("secret123"),
    )
    db.add(u)
    await db.commit()
    return u


# ── /api/auth/login ────────────────────────────────────────────────────────────

class TestLogin:
    @pytest.mark.asyncio
    async def test_login_with_valid_credentials_returns_token(
            self, client, user_with_password):
        resp = await client.post("/api/auth/login",
            json={"email": "dev@codeseer.io", "password": "secret123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "dev@codeseer.io"
        assert data["user"]["role"] == "developer"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client, user_with_password):
        resp = await client.post("/api/auth/login",
            json={"email": "dev@codeseer.io", "password": "wrong"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_email_returns_401(self, client):
        resp = await client.post("/api/auth/login",
            json={"email": "nobody@x.com", "password": "secret123"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user_returns_401(self, db, client):
        from app.core.auth import hash_password
        u = User(
            id="inactive-001",
            email="inactive@codeseer.io",
            name="Inactive",
            role=UserRole.VIEWER,
            password_hash=hash_password("pass"),
            is_active=False,
        )
        db.add(u)
        await db.commit()
        resp = await client.post("/api/auth/login",
            json={"email": "inactive@codeseer.io", "password": "pass"})
        assert resp.status_code == 401


# ── /api/auth/me ───────────────────────────────────────────────────────────────

class TestMe:
    @pytest.mark.asyncio
    async def test_me_returns_current_user(self, client, user_with_password):
        login = await client.post("/api/auth/login",
            json={"email": "dev@codeseer.io", "password": "secret123"})
        token = login.json()["access_token"]

        resp = await client.get("/api/auth/me",
            headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "dev@codeseer.io"
        assert data["id"] == "auth-user-001"

    @pytest.mark.asyncio
    async def test_me_without_token_returns_401(self, client):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_invalid_token_returns_401(self, client):
        resp = await client.get("/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401


# ── JWT token 内容验证 ─────────────────────────────────────────────────────────

class TestTokenContent:
    @pytest.mark.asyncio
    async def test_token_contains_user_id_and_role(self, client, user_with_password):
        from jose import jwt
        from app.core.config import settings

        login = await client.post("/api/auth/login",
            json={"email": "dev@codeseer.io", "password": "secret123"})
        token = login.json()["access_token"]

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "auth-user-001"
        assert payload["role"] == "developer"
