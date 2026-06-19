import json as _json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

_SKILLS_DIR = Path(__file__).parent.parent.parent.parent / "aicode" / "skills"

from app.core.database import get_db
from app.api.mcp_tokens import verify_token
from app.models.models import (
    Iteration, Project, Requirement, RequirementStatus, Task,
)

router = APIRouter(prefix="/mcp/http", tags=["mcp-http"])

TOOLS = [
    {
        "name": "list_my_projects",
        "description": "列出当前开发者有未完成需求的项目",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_iterations",
        "description": "列出指定项目下的迭代",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "list_my_requirements",
        "description": "列出指定迭代中指派给当前开发者的需求",
        "inputSchema": {
            "type": "object",
            "properties": {
                "iteration_id": {"type": "string", "description": "迭代 ID"},
            },
            "required": ["iteration_id"],
        },
    },
    {
        "name": "start_brainstorming",
        "description": "锁定需求并返回头脑风暴所需的完整上下文",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
            },
            "required": ["requirement_id"],
        },
    },
    {
        "name": "list_skills_by_project",
        "description": "获取指定项目的所有 Skill",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "get_requirement_detail",
        "description": "获取需求完整详情（含任务列表）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
            },
            "required": ["requirement_id"],
        },
    },
    {
        "name": "sync_tasks",
        "description": "将任务列表同步到平台（替换已有任务）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
                "tasks": {
                    "type": "array",
                    "description": "任务列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "priority": {"type": "string"},
                        },
                        "required": ["title"],
                    },
                },
            },
            "required": ["requirement_id", "tasks"],
        },
    },
    {
        "name": "update_task_status",
        "description": "更新任务状态和 TDD 进度",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "任务 ID"},
                "status": {"type": "string", "description": "新状态"},
            },
            "required": ["task_id", "status"],
        },
    },
    {
        "name": "submit_test_result",
        "description": "提交单元测试执行结果",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
                "total_count": {"type": "integer"},
                "passed_count": {"type": "integer"},
                "failed_count": {"type": "integer"},
            },
            "required": ["requirement_id", "total_count", "passed_count", "failed_count"],
        },
    },
    {
        "name": "update_requirement_status",
        "description": "更新需求状态（触发状态流转）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
                "action": {"type": "string", "description": "目标状态，如 claimed / in_progress / pending_review"},
            },
            "required": ["requirement_id", "action"],
        },
    },
    {
        "name": "setup_dev_environment",
        "description": "安装 superpowers 技能包和 CodeSeer 专属技能到本地 AI 工具",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
]

_ACTIVE_STATUSES = ["assigned", "claimed", "in_progress"]

_TRANSITIONS: dict[str, list[str]] = {
    "draft":            ["pending_analysis"],
    "pending_analysis": ["analyzed"],
    "analyzed":         ["assigned"],
    "assigned":         ["claimed", "analyzed"],
    "claimed":          ["in_progress"],
    "in_progress":      ["pending_review"],
    "pending_review":   ["review_approved", "review_rejected"],
    "review_approved":  ["completed"],
    "review_rejected":  ["in_progress"],
    "completed":        [],
}

_KNOWN_TOOLS = {t["name"] for t in TOOLS}


def _text(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


def _err(code: int, msg: str, req_id) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": msg}}


async def _authenticate(
    authorization: Optional[str],
    db: AsyncSession,
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization[len("Bearer "):]
    user = await verify_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


# ── tool handlers ─────────────────────────────────────────────────────────────

async def _list_my_projects(args: dict, user, db: AsyncSession) -> dict:
    proj_ids_q = await db.execute(
        select(Requirement.project_id)
        .where(
            Requirement.assignee_id == str(user.id),
            Requirement.status.in_(_ACTIVE_STATUSES),
        )
        .distinct()
    )
    project_ids = [row[0] for row in proj_ids_q.all()]
    if not project_ids:
        return _text("暂无有效项目")

    proj_result = await db.execute(
        select(Project).where(Project.id.in_(project_ids)).order_by(Project.name)
    )
    projects = proj_result.scalars().all()
    lines = [f"- {p.name} (id={p.id}, status={p.status.value if hasattr(p.status, 'value') else p.status})"
             for p in projects]
    return _text("你的项目：\n" + "\n".join(lines))


async def _list_iterations(args: dict, user, db: AsyncSession) -> dict:
    project_id = args.get("project_id")
    if not project_id:
        return None  # caller returns -32602
    result = await db.execute(
        select(Iteration).where(Iteration.project_id == project_id).order_by(Iteration.created_at.desc())
    )
    iterations = result.scalars().all()
    if not iterations:
        return _text("该项目下暂无迭代")
    lines = [f"- {it.name} (id={it.id}, status={it.status.value if hasattr(it.status, 'value') else it.status})"
             for it in iterations]
    return _text("迭代列表：\n" + "\n".join(lines))


async def _list_my_requirements(args: dict, user, db: AsyncSession) -> dict:
    iteration_id = args.get("iteration_id")
    if not iteration_id:
        return None  # caller returns -32602
    result = await db.execute(
        select(Requirement)
        .where(
            Requirement.iteration_id == iteration_id,
            Requirement.assignee_id == str(user.id),
        )
        .order_by(Requirement.priority.asc())
    )
    reqs = result.scalars().all()
    if not reqs:
        return _text("该迭代下暂无分配给你的需求")
    lines = [f"- [{r.priority.value if hasattr(r.priority, 'value') else r.priority}] {r.title} "
             f"(id={r.id}, status={r.status.value if hasattr(r.status, 'value') else r.status})"
             for r in reqs]
    return _text("需求列表：\n" + "\n".join(lines))


async def _get_requirement_detail(args: dict, user, db: AsyncSession) -> dict:
    req_id = args.get("requirement_id")
    if not req_id:
        return None
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        return {"__not_found__": True}
    tasks_result = await db.execute(
        select(Task).where(Task.requirement_id == req_id).order_by(Task.order)
    )
    tasks = tasks_result.scalars().all()
    status = req.status.value if hasattr(req.status, "value") else req.status
    priority = req.priority.value if hasattr(req.priority, "value") else req.priority
    task_lines = "\n".join(
        f"  {i+1}. {t.title} [{t.status.value if hasattr(t.status, 'value') else t.status}]"
        for i, t in enumerate(tasks)
    ) or "  （暂无任务）"
    text = (
        f"需求详情\n"
        f"标题: {req.title}\n"
        f"状态: {status}\n"
        f"优先级: {priority}\n"
        f"描述: {req.description or '无'}\n"
        f"验收标准: {req.acceptance_criteria or '无'}\n"
        f"任务列表:\n{task_lines}"
    )
    return _text(text)


async def _sync_tasks(args: dict, user, db: AsyncSession) -> dict:
    req_id = args.get("requirement_id")
    tasks_data = args.get("tasks")
    if not req_id or tasks_data is None:
        return None
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    if not result.scalar_one_or_none():
        return {"__not_found__": True}

    existing = await db.execute(select(Task).where(Task.requirement_id == req_id))
    for t in existing.scalars().all():
        await db.delete(t)

    for i, td in enumerate(tasks_data):
        t = Task(
            requirement_id=req_id,
            title=td.get("title", ""),
            description=td.get("description"),
            order=i,
        )
        db.add(t)
    await db.commit()
    return _text(f"已同步 {len(tasks_data)} 个任务到需求 {req_id}")


async def _update_requirement_status(args: dict, user, db: AsyncSession) -> dict:
    req_id = args.get("requirement_id")
    action = args.get("action")
    if not req_id or not action:
        return None
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        return {"__not_found__": True}

    current = req.status.value if hasattr(req.status, "value") else str(req.status)
    allowed = _TRANSITIONS.get(current, [])
    if action not in allowed:
        return _text(f"状态流转失败：{current} → {action} 不允许（允许: {allowed}）")

    req.status = RequirementStatus(action)
    req.updated_at = datetime.utcnow()
    await db.commit()
    return _text(f"需求 {req_id} 状态已更新：{current} → {action}")


_COMMANDS_DIR = Path(__file__).parent.parent.parent.parent / "aicode" / "commands"

_HARNESS_SETUP = {
    "claude_code": {
        "name": "Claude Code",
        "superpowers_check_paths": [
            "~/.claude/plugins/installed_plugins.json（确认包含 superpowers 条目）",
            "~/.claude/plugins/cache/superpowers-marketplace",
        ],
        "superpowers_install": "claude plugin install superpowers@superpowers-marketplace",
        "skill_path": ".claude/skills/codeseer-integration/SKILL.md",
        "command_path": ".claude/commands/setup_cs_env.md",
    },
    "opencode": {
        "name": "OpenCode",
        "superpowers_check_paths": [
            "~/.opencode/opencode.json（确认 plugin 数组包含 superpowers）",
            "~/.config/opencode/opencode.json",
        ],
        "superpowers_install": (
            '在 opencode.json 的 plugin 数组中添加：\n'
            '"superpowers@git+https://github.com/obra/superpowers.git"'
        ),
        "skill_path": ".opencode/skills/codeseer-integration/SKILL.md",
        "command_path": ".opencode/commands/setup_cs_env.md",
    },
    "cursor": {
        "name": "Cursor",
        "superpowers_check_paths": [
            "~/.cursor/plugins/superpowers",
        ],
        "superpowers_install": "cursor plugin install superpowers@superpowers-marketplace",
        "skill_path": ".cursor/skills/codeseer-integration/SKILL.md",
        "command_path": ".cursor/skills-cursor/setup_cs_env/SKILL.md",
    },
}


async def _setup_dev_environment(args: dict, user, db: AsyncSession) -> dict:
    skill_path = _SKILLS_DIR / "codeseer-integration.md"
    skill_content = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""

    command_path = _COMMANDS_DIR / "setup_cs_env.md"
    command_content = command_path.read_text(encoding="utf-8") if command_path.exists() else ""

    sections = ["## CodeSeer 开发环境安装指南\n"]
    sections.append("请根据你使用的 AI 工具，按对应步骤操作：\n")

    for harness in _HARNESS_SETUP.values():
        check_paths = "\n".join(f"  - `{p}`" for p in harness["superpowers_check_paths"])
        sections.append(
            f"### {harness['name']}\n\n"
            f"**第 1 步：检查 superpowers 是否已安装**\n{check_paths}\n\n"
            f"**第 2 步：未安装时执行**\n```\n{harness['superpowers_install']}\n```\n\n"
            f"**第 3 步：安装 CodeSeer 专属技能**\n"
            f"将【技能文件】内容写入 `{harness['skill_path']}`（目录不存在时先创建）\n\n"
            f"**第 4 步：安装 /setup_cs_env 斜杠命令**\n"
            f"将【命令文件】内容写入 `{harness['command_path']}`（目录不存在时先创建）\n"
        )

    return {
        "content": [
            {"type": "text", "text": "\n".join(sections)},
            {"type": "text", "text": f"【技能文件】codeseer-integration\n\n{skill_content}"},
            {"type": "text", "text": f"【命令文件】setup_cs_env\n\n{command_content}"},
        ]
    }


_TOOL_HANDLERS = {
    "list_my_projects": _list_my_projects,
    "list_iterations": _list_iterations,
    "list_my_requirements": _list_my_requirements,
    "get_requirement_detail": _get_requirement_detail,
    "sync_tasks": _sync_tasks,
    "update_requirement_status": _update_requirement_status,
    "setup_dev_environment": _setup_dev_environment,
}


# ── endpoint ──────────────────────────────────────────────────────────────────

@router.post("")
async def mcp_http_endpoint(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """MCP HTTP 端点：JSON-RPC 2.0 over HTTP"""
    user = await _authenticate(authorization, db)

    body = await request.json()
    method = body.get("method", "")
    req_id = body.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "codeseer", "version": "1.0.0"},
                "instructions": (
                    "连接 CodeSeer 成功。请立即执行以下操作：\n"
                    "调用 setup_dev_environment 工具获取 setup_cs_env 命令文件内容，"
                    "将【命令文件】写入当前项目目录下的 .claude/commands/setup_cs_env.md"
                    "（OpenCode 写入 .opencode/commands/setup_cs_env.md）。"
                    "目录不存在时先创建。文件已存在则跳过。"
                    "完成后告知用户可以使用 /setup_cs_env 初始化开发环境。"
                ),
            },
        }

    if method in ("notifications/initialized", "initialized"):
        return {}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        params = body.get("params")
        if params is None:
            return _err(-32602, "Missing params", req_id)

        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name not in _KNOWN_TOOLS:
            return _err(-32601, f"Unknown tool: {tool_name}", req_id)

        handler = _TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return _err(-32601, f"Tool not implemented: {tool_name}", req_id)

        result = await handler(arguments, user, db)

        if result is None:
            return _err(-32602, f"Missing required argument for {tool_name}", req_id)
        if result.get("__not_found__"):
            return _err(-32602, "Resource not found", req_id)

        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }
