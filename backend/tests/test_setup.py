"""Tests for setup_dev_environment MCP tool."""
import pytest
from httpx import AsyncClient


class TestSetupDevEnvironment:
    @pytest.mark.asyncio
    async def test_returns_superpowers_install_cmd(self, client: AsyncClient, token_and_user):
        token, _ = token_and_user
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "setup_dev_environment", "arguments": {}},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        text = data["result"]["content"][0]["text"]
        assert "superpowers" in text.lower()
        # 每种 harness 各有安装指令
        assert "claude code" in text.lower()
        assert "opencode" in text.lower()

    @pytest.mark.asyncio
    async def test_returns_superpowers_check_paths(self, client: AsyncClient, token_and_user):
        token, _ = token_and_user
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "setup_dev_environment", "arguments": {}},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        text = data["result"]["content"][0]["text"]
        # Claude Code 和 OpenCode 各有自己的检查路径
        assert "installed_plugins.json" in text
        assert "opencode.json" in text

    @pytest.mark.asyncio
    async def test_returns_codeseer_skill_content(self, client: AsyncClient, token_and_user):
        token, _ = token_and_user
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "setup_dev_environment", "arguments": {}},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        content = data["result"]["content"]
        # 4 块：安装指南 + 技能文件 + setup_cs_env 命令 + start_cs 命令
        assert len(content) == 4
        skill_block = content[1]["text"]
        assert "list_my_projects" in skill_block
        setup_cmd_block = content[2]["text"]
        assert "setup_cs_env" in setup_cmd_block
        start_cmd_block = content[3]["text"]
        assert "start_cs" in start_cmd_block
        assert "start_brainstorming" in start_cmd_block

    @pytest.mark.asyncio
    async def test_tool_in_tools_list(self, client: AsyncClient, token_and_user):
        token, _ = token_and_user
        resp = await client.post(
            "/api/mcp/http",
            headers={"Authorization": f"Bearer {token}"},
            json={"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {}},
        )
        assert resp.status_code == 200
        tools = {t["name"] for t in resp.json()["result"]["tools"]}
        assert "setup_dev_environment" in tools
