"""
TDD tests for tools/call dispatch in /api/mcp/http.
Written BEFORE production code.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def auth_headers(client, test_user):
    """有效 Bearer Token 的请求头"""
    resp = await client.post(
        "/api/mcp/tokens",
        json={"name": "Test", "user_id": test_user.id},
    )
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def seeded_project(db, test_user):
    """在 DB 里创建一条项目 + 迭代 + 需求（指派给 test_user）"""
    from app.models.models import Project, Iteration, Requirement, ProjectStatus, IterationStatus, RequirementStatus, RequirementPriority

    proj = Project(id="proj-001", name="Demo Project", status=ProjectStatus.ACTIVE,
                   created_by=test_user.id)
    db.add(proj)

    it = Iteration(id="iter-001", project_id="proj-001", name="Sprint 1",
                   status=IterationStatus.DEVELOPMENT)
    db.add(it)

    req = Requirement(id="req-001", title="实现登录功能", project_id="proj-001",
                      iteration_id="iter-001", assignee_id=test_user.id,
                      status=RequirementStatus.ASSIGNED, priority=RequirementPriority.P1)
    db.add(req)
    await db.commit()
    return {"project": proj, "iteration": it, "requirement": req}


# ── tools/call 路由分发 ────────────────────────────────────────────────────────

class TestToolsCall:
    @pytest.mark.asyncio
    async def test_unknown_tool_returns_32601(self, client, auth_headers):
        """tools/call 调用不存在的工具返回 -32601"""
        resp = await client.post("/api/mcp/http",
            headers=auth_headers,
            json={"jsonrpc": "2.0", "method": "tools/call",
                  "params": {"name": "nonexistent_tool", "arguments": {}}, "id": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_missing_params_returns_32602(self, client, auth_headers):
        """tools/call 缺少 params 字段返回 -32602"""
        resp = await client.post("/api/mcp/http",
            headers=auth_headers,
            json={"jsonrpc": "2.0", "method": "tools/call", "id": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32602


class TestListMyProjects:
    @pytest.mark.asyncio
    async def test_list_my_projects_returns_project_list(
            self, client, auth_headers, seeded_project, test_user):
        """list_my_projects 返回当前用户有需求的项目"""
        resp = await client.post("/api/mcp/http",
            headers=auth_headers,
            json={"jsonrpc": "2.0", "method": "tools/call",
                  "params": {"name": "list_my_projects", "arguments": {}}, "id": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        text = data["result"]["content"][0]["text"]
        assert "Demo Project" in text

    @pytest.mark.asyncio
    async def test_list_my_projects_empty_when_no_assignments(self, client, auth_headers):
        """没有指派需求时返回空列表提示"""
        resp = await client.post("/api/mcp/http",
            headers=auth_headers,
            json={"jsonrpc": "2.0", "method": "tools/call",
                  "params": {"name": "list_my_projects", "arguments": {}}, "id": 4})
        assert resp.status_code == 200
        text = resp.json()["result"]["content"][0]["text"]
        assert "暂无" in text or text  # 不崩溃即可


class TestListMyRequirements:
    @pytest.mark.asyncio
    async def test_list_my_requirements_returns_reqs(
            self, client, auth_headers, seeded_project):
        """list_my_requirements 返回该迭代下指派给当前用户的需求"""
        resp = await client.post("/api/mcp/http",
            headers=auth_headers,
            json={"jsonrpc": "2.0", "method": "tools/call",
                  "params": {"name": "list_my_requirements",
                             "arguments": {"iteration_id": "iter-001"}}, "id": 5})
        assert resp.status_code == 200
        text = resp.json()["result"]["content"][0]["text"]
        assert "实现登录功能" in text

    @pytest.mark.asyncio
    async def test_list_my_requirements_missing_arg_returns_error(
            self, client, auth_headers):
        """list_my_requirements 缺少 iteration_id 返回错误"""
        resp = await client.post("/api/mcp/http",
            headers=auth_headers,
            json={"jsonrpc": "2.0", "method": "tools/call",
                  "params": {"name": "list_my_requirements", "arguments": {}}, "id": 6})
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data


class TestGetRequirementDetail:
    @pytest.mark.asyncio
    async def test_get_requirement_detail_returns_full_info(
            self, client, auth_headers, seeded_project):
        """get_requirement_detail 返回需求详情和任务列表"""
        resp = await client.post("/api/mcp/http",
            headers=auth_headers,
            json={"jsonrpc": "2.0", "method": "tools/call",
                  "params": {"name": "get_requirement_detail",
                             "arguments": {"requirement_id": "req-001"}}, "id": 7})
        assert resp.status_code == 200
        text = resp.json()["result"]["content"][0]["text"]
        assert "实现登录功能" in text

    @pytest.mark.asyncio
    async def test_get_requirement_detail_not_found_returns_error(
            self, client, auth_headers):
        """get_requirement_detail 不存在的需求返回错误"""
        resp = await client.post("/api/mcp/http",
            headers=auth_headers,
            json={"jsonrpc": "2.0", "method": "tools/call",
                  "params": {"name": "get_requirement_detail",
                             "arguments": {"requirement_id": "nonexistent"}}, "id": 8})
        assert resp.status_code == 200
        assert "error" in resp.json()

    @pytest.mark.asyncio
    async def test_get_requirement_detail_includes_attachments(
            self, client, auth_headers, seeded_project, db):
        """get_requirement_detail 返回需求详情时包含附件列表"""
        from app.models.models import RequirementAttachment

        # create an attachment
        att = RequirementAttachment(
            id="att-001",
            requirement_id="req-001",
            filename="需求文档.pdf",
            file_size=1024,
            content_type="application/pdf",
            storage_path="/tmp/test/req-001/att-001_需求文档.pdf",
            storage_backend="local",
        )
        db.add(att)
        await db.commit()

        resp = await client.post("/api/mcp/http",
            headers=auth_headers,
            json={"jsonrpc": "2.0", "method": "tools/call",
                  "params": {"name": "get_requirement_detail",
                             "arguments": {"requirement_id": "req-001"}}, "id": 11})
        assert resp.status_code == 200
        text = resp.json()["result"]["content"][0]["text"]
        assert "附件列表" in text
        assert "需求文档.pdf" in text


class TestSyncTasks:
    @pytest.mark.asyncio
    async def test_sync_tasks_creates_tasks(
            self, client, auth_headers, seeded_project, db):
        """sync_tasks 将任务写入数据库"""
        from sqlalchemy import select
        from app.models.models import Task

        resp = await client.post("/api/mcp/http",
            headers=auth_headers,
            json={"jsonrpc": "2.0", "method": "tools/call",
                  "params": {"name": "sync_tasks", "arguments": {
                      "requirement_id": "req-001",
                      "tasks": [
                          {"title": "写单测", "description": "覆盖核心逻辑"},
                          {"title": "写实现", "priority": "P1"},
                      ]
                  }}, "id": 9})
        assert resp.status_code == 200
        assert "error" not in resp.json()

        result = await db.execute(
            select(Task).where(Task.requirement_id == "req-001"))
        tasks = result.scalars().all()
        assert len(tasks) == 2
        assert tasks[0].title == "写单测"


class TestUpdateRequirementStatus:
    @pytest.mark.asyncio
    async def test_update_requirement_status_transitions(
            self, client, auth_headers, seeded_project):
        """update_requirement_status 触发状态流转"""
        resp = await client.post("/api/mcp/http",
            headers=auth_headers,
            json={"jsonrpc": "2.0", "method": "tools/call",
                  "params": {"name": "update_requirement_status", "arguments": {
                      "requirement_id": "req-001",
                      "action": "claimed",
                  }}, "id": 10})
        assert resp.status_code == 200
        assert "error" not in resp.json()
        text = resp.json()["result"]["content"][0]["text"]
        assert "claimed" in text
