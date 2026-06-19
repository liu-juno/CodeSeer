"""
TDD tests for MCP HTTP SSE endpoint.
All tests written BEFORE production code.
"""
import pytest
import pytest_asyncio
import json
from httpx import AsyncClient



class TestMcpHttpAuth:
    @pytest.mark.asyncio
    async def test_missing_auth_header_returns_401(self, client):
        """没有 Authorization 头时返回 401"""
        resp = await client.post("/api/mcp/http", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client):
        """无效 Token 返回 401"""
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": "Bearer invalid_token_xyz"},
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_non_bearer_scheme_returns_401(self, client):
        """非 Bearer 方案返回 401"""
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_token_returns_200(self, client, token_and_user):
        """有效 Token 能访问端点，返回 200"""
        token, _ = token_and_user
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": f"Bearer {token}"},
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        )
        assert resp.status_code == 200


class TestMcpHttpToolsList:
    @pytest.mark.asyncio
    async def test_tools_list_returns_jsonrpc_result(self, client, token_and_user):
        """tools/list 返回合法的 JSON-RPC 2.0 响应"""
        token, _ = token_and_user
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": f"Bearer {token}"},
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
        )
        data = resp.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        assert "tools" in data["result"]

    @pytest.mark.asyncio
    async def test_tools_list_contains_expected_tools(self, client, token_and_user):
        """tools/list 包含核心 MCP 工具"""
        token, _ = token_and_user
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": f"Bearer {token}"},
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 2},
        )
        tool_names = [t["name"] for t in resp.json()["result"]["tools"]]
        assert "list_my_projects" in tool_names
        assert "list_my_requirements" in tool_names
        assert "start_brainstorming" in tool_names


class TestMcpHttpInitialize:
    @pytest.mark.asyncio
    async def test_initialize_returns_server_info(self, client, token_and_user):
        """initialize 握手返回 protocolVersion 和 serverInfo"""
        token, _ = token_and_user
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": f"Bearer {token}"},
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                  "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                             "clientInfo": {"name": "opencode", "version": "1.0"}}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        assert data["result"]["protocolVersion"] == "2024-11-05"
        assert "serverInfo" in data["result"]
        assert "capabilities" in data["result"]
        assert "instructions" in data["result"]
        # initialize 只安装命令，不做完整环境初始化
        assert "setup_cs_env" in data["result"]["instructions"]
        assert ".claude/commands" in data["result"]["instructions"]

    @pytest.mark.asyncio
    async def test_initialized_notification_returns_empty(self, client, token_and_user):
        """initialized 通知（无 id）返回 null 或空"""
        token, _ = token_and_user
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": f"Bearer {token}"},
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        )
        assert resp.status_code == 200


class TestMcpHttpUnknownMethod:
    @pytest.mark.asyncio
    async def test_unknown_method_returns_error(self, client, token_and_user):
        """未知 method 返回 JSON-RPC error（-32601 Method not found）"""
        token, _ = token_and_user
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": f"Bearer {token}"},
            json={"jsonrpc": "2.0", "method": "nonexistent/method", "id": 9},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32601
