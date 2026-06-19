"""
TDD tests for MCP HTTP Token Auth feature.
All tests here were written BEFORE production code.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient


# ── Task 1: AccessToken model ─────────────────────────────────────────────────

class TestAccessTokenModel:
    @pytest.mark.asyncio
    async def test_access_token_can_be_created(self, db, test_user):
        """AccessToken 可以用必填字段创建并持久化"""
        from app.models.models import AccessToken
        token = AccessToken(
            user_id=test_user.id,
            token_hash="abc123hash",
            token_prefix="codeseer_ab",
            name="My Dev Token",
        )
        db.add(token)
        await db.commit()
        await db.refresh(token)

        assert token.id is not None
        assert token.is_active is True
        assert token.expires_at is None
        assert token.last_used_at is None

    @pytest.mark.asyncio
    async def test_access_token_with_expiry(self, db, test_user):
        """AccessToken 可以设置过期时间"""
        from app.models.models import AccessToken
        expires = datetime.utcnow() + timedelta(days=30)
        token = AccessToken(
            user_id=test_user.id,
            token_hash="xyz456hash",
            token_prefix="codeseer_xy",
            name="Expiring Token",
            expires_at=expires,
        )
        db.add(token)
        await db.commit()
        await db.refresh(token)

        assert token.expires_at is not None


# ── Task 2: Config ────────────────────────────────────────────────────────────

class TestTokenConfig:
    def test_config_has_token_secret_key(self):
        """Settings 包含 ACCESS_TOKEN_SECRET_KEY"""
        from app.core.config import settings
        assert hasattr(settings, "ACCESS_TOKEN_SECRET_KEY")
        assert settings.ACCESS_TOKEN_SECRET_KEY != ""

    def test_config_has_token_expiry_days(self):
        """Settings 包含 ACCESS_TOKEN_EXPIRY_DAYS，默认 30"""
        from app.core.config import settings
        assert hasattr(settings, "ACCESS_TOKEN_EXPIRY_DAYS")
        assert settings.ACCESS_TOKEN_EXPIRY_DAYS == 30

    def test_config_has_token_length(self):
        """Settings 包含 ACCESS_TOKEN_LENGTH，默认 32"""
        from app.core.config import settings
        assert hasattr(settings, "ACCESS_TOKEN_LENGTH")
        assert settings.ACCESS_TOKEN_LENGTH == 32


# ── Task 3: Token 生成与验证逻辑 ──────────────────────────────────────────────

class TestTokenGeneration:
    def test_generate_token_returns_codeseer_prefix(self):
        """生成的 Token 以 codeseer_ 开头"""
        from app.api.mcp_tokens import generate_token
        token, token_hash, prefix = generate_token()
        assert token.startswith("codeseer_")

    def test_generate_token_hash_differs_from_token(self):
        """Token 哈希值与原始 Token 不同（安全存储）"""
        from app.api.mcp_tokens import generate_token
        token, token_hash, prefix = generate_token()
        assert token != token_hash
        assert len(token_hash) == 64  # SHA-256 hex

    def test_generate_token_prefix_matches_start(self):
        """返回的 prefix 是 Token 的前 12 个字符"""
        from app.api.mcp_tokens import generate_token
        token, token_hash, prefix = generate_token()
        assert token.startswith(prefix)
        assert len(prefix) == 12

    def test_generate_token_unique_each_call(self):
        """每次生成的 Token 唯一"""
        from app.api.mcp_tokens import generate_token
        token1, _, _ = generate_token()
        token2, _, _ = generate_token()
        assert token1 != token2

    @pytest.mark.asyncio
    async def test_verify_token_returns_user_for_valid_token(self, db, test_user):
        """有效 Token 验证返回对应用户"""
        from app.api.mcp_tokens import generate_token, verify_token
        from app.models.models import AccessToken

        token, token_hash, prefix = generate_token()
        at = AccessToken(
            user_id=test_user.id,
            token_hash=token_hash,
            token_prefix=prefix,
            name="Valid Token",
        )
        db.add(at)
        await db.commit()

        user = await verify_token(token, db)
        assert user is not None
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_verify_token_returns_none_for_wrong_token(self, db, test_user):
        """错误 Token 验证返回 None"""
        from app.api.mcp_tokens import verify_token
        user = await verify_token("wrong_token_value", db)
        assert user is None

    @pytest.mark.asyncio
    async def test_verify_token_returns_none_for_revoked_token(self, db, test_user):
        """已撤销 Token 验证返回 None"""
        from app.api.mcp_tokens import generate_token, verify_token
        from app.models.models import AccessToken

        token, token_hash, prefix = generate_token()
        at = AccessToken(
            user_id=test_user.id,
            token_hash=token_hash,
            token_prefix=prefix,
            name="Revoked Token",
            is_active=False,
        )
        db.add(at)
        await db.commit()

        user = await verify_token(token, db)
        assert user is None

    @pytest.mark.asyncio
    async def test_verify_token_returns_none_for_expired_token(self, db, test_user):
        """已过期 Token 验证返回 None"""
        from app.api.mcp_tokens import generate_token, verify_token
        from app.models.models import AccessToken

        token, token_hash, prefix = generate_token()
        at = AccessToken(
            user_id=test_user.id,
            token_hash=token_hash,
            token_prefix=prefix,
            name="Expired Token",
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        db.add(at)
        await db.commit()

        user = await verify_token(token, db)
        assert user is None

    @pytest.mark.asyncio
    async def test_verify_token_updates_last_used_at(self, db, test_user):
        """验证成功后 last_used_at 被更新"""
        from app.api.mcp_tokens import generate_token, verify_token
        from app.models.models import AccessToken
        from sqlalchemy import select

        token, token_hash, prefix = generate_token()
        at = AccessToken(
            user_id=test_user.id,
            token_hash=token_hash,
            token_prefix=prefix,
            name="Track Usage Token",
        )
        db.add(at)
        await db.commit()

        assert at.last_used_at is None
        await verify_token(token, db)

        await db.refresh(at)
        assert at.last_used_at is not None


# ── Task 3: Token 管理 API ────────────────────────────────────────────────────

class TestTokenManagementAPI:
    @pytest.mark.asyncio
    async def test_create_token_returns_201_with_token(self, client, test_user):
        """POST /api/mcp/tokens 创建 Token，返回 201 和明文 Token（仅此一次）"""
        resp = await client.post(
            "/api/mcp/tokens",
            json={"name": "CI Token", "user_id": test_user.id},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "token" in data
        assert data["token"].startswith("codeseer_")
        assert "token_id" in data
        assert "prefix" in data

    @pytest.mark.asyncio
    async def test_create_token_with_expiry(self, client, test_user):
        """POST /api/mcp/tokens 支持设置过期天数"""
        resp = await client.post(
            "/api/mcp/tokens",
            json={"name": "Short Token", "user_id": test_user.id, "days": 7},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_list_tokens_returns_user_tokens(self, client, test_user):
        """GET /api/mcp/tokens?user_id=xxx 返回该用户的 Token 列表（不含明文）"""
        # 先创建两个 Token
        await client.post("/api/mcp/tokens", json={"name": "T1", "user_id": test_user.id})
        await client.post("/api/mcp/tokens", json={"name": "T2", "user_id": test_user.id})

        resp = await client.get(f"/api/mcp/tokens?user_id={test_user.id}")
        assert resp.status_code == 200
        tokens = resp.json()["tokens"]
        assert len(tokens) == 2
        # 明文 Token 不在列表中
        for t in tokens:
            assert "token" not in t
            assert "token_hash" not in t

    @pytest.mark.asyncio
    async def test_revoke_token(self, client, test_user):
        """DELETE /api/mcp/tokens/{id} 撤销 Token"""
        create_resp = await client.post(
            "/api/mcp/tokens",
            json={"name": "To Revoke", "user_id": test_user.id},
        )
        token_id = create_resp.json()["token_id"]

        revoke_resp = await client.delete(f"/api/mcp/tokens/{token_id}",
                                          params={"user_id": test_user.id})
        assert revoke_resp.status_code == 200

        list_resp = await client.get(f"/api/mcp/tokens?user_id={test_user.id}")
        tokens = list_resp.json()["tokens"]
        assert all(t["id"] != token_id for t in tokens)


# ── Code review fixes ─────────────────────────────────────────────────────────

class TestSecurityFixes:
    @pytest.mark.asyncio
    async def test_revoke_requires_user_id_ownership(self, client, test_user, db):
        """Critical #1: DELETE 需要 user_id 参数，且只能撤销自己的 Token"""
        from app.models.models import User, UserRole, AccessToken
        from app.api.mcp_tokens import generate_token

        # 建另一个用户并创建他的 Token
        other_user = User(id="other-user-001", email="other@example.com",
                          name="Other", role=UserRole.DEVELOPER)
        db.add(other_user)
        await db.commit()

        token_str, token_hash, prefix = generate_token()
        at = AccessToken(user_id="other-user-001", token_hash=token_hash,
                         token_prefix=prefix, name="Other Token")
        db.add(at)
        await db.commit()

        # test_user 尝试撤销 other_user 的 token → 应返回 404
        resp = await client.delete(
            f"/api/mcp/tokens/{at.id}",
            params={"user_id": test_user.id},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_revoke_own_token_with_user_id_succeeds(self, client, test_user):
        """Critical #1: 携带正确 user_id 撤销自己的 Token 成功"""
        create_resp = await client.post(
            "/api/mcp/tokens",
            json={"name": "Mine", "user_id": test_user.id},
        )
        token_id = create_resp.json()["token_id"]

        resp = await client.delete(f"/api/mcp/tokens/{token_id}",
                                   params={"user_id": test_user.id})
        assert resp.status_code == 200

    def test_token_hash_uses_hmac_not_plain_sha256(self):
        """Critical #2: generate_token 使用 HMAC-SHA256，不是裸 SHA-256"""
        import hashlib, hmac as hmac_mod
        from app.api.mcp_tokens import generate_token
        from app.core.config import settings

        token, token_hash, _ = generate_token()
        expected = hmac_mod.new(
            settings.ACCESS_TOKEN_SECRET_KEY.encode(),
            token.encode(),
            hashlib.sha256,
        ).hexdigest()
        assert token_hash == expected, "token_hash 应使用 HMAC-SHA256"

    @pytest.mark.asyncio
    async def test_days_zero_creates_expired_token_not_never_expiring(self, client, test_user):
        """Important #3: days=0 应创建立即过期的 Token，而非永不过期"""
        resp = await client.post(
            "/api/mcp/tokens",
            json={"name": "Zero Days", "user_id": test_user.id, "days": 0},
        )
        assert resp.status_code == 201
        # days=0 → expires_at 应该不为 None（而是过去/现在的时间）
        assert resp.json()["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_token_hash_column_is_unique(self, db, test_user):
        """Important #5: token_hash 列有唯一约束，重复插入应失败"""
        from app.models.models import AccessToken
        import sqlalchemy.exc

        at1 = AccessToken(user_id=test_user.id, token_hash="same_hash_value",
                          token_prefix="codeseer_sa", name="T1")
        at2 = AccessToken(user_id=test_user.id, token_hash="same_hash_value",
                          token_prefix="codeseer_sa", name="T2")
        db.add(at1)
        await db.commit()
        db.add(at2)
        with pytest.raises(Exception):  # IntegrityError
            await db.commit()
