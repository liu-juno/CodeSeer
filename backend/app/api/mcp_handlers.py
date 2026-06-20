import re
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Document, Iteration, Project, Requirement, RequirementStatus, Task, TestResult, UnitTestRecord,
)
from app.api.mcp_tools import ACTIVE_STATUSES, TRANSITIONS

_SKILLS_DIR = Path(__file__).parent.parent.parent.parent / "aicode" / "skills"
_COMMANDS_DIR = Path(__file__).parent.parent.parent.parent / "aicode" / "commands"
_TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "aicode" / "templates"


def _text(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:40].strip("-") or "unnamed"


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_cmd(name: str) -> str:
    return _read_file(_COMMANDS_DIR / f"{name}.md")


def _read_template(name: str) -> str:
    return _read_file(_TEMPLATES_DIR / f"{name}.md")


_HARNESS_SETUP = {
    "claude_code": {
        "name": "Claude Code",
        "superpowers_check_paths": [
            "~/.claude/plugins/installed_plugins.json（确认包含 superpowers 条目）",
            "~/.claude/plugins/cache/superpowers-marketplace",
        ],
        "superpowers_install": "claude plugin install superpowers@superpowers-marketplace",
        "skill_path": ".claude/skills/cs_integration/SKILL.md",
        "command_path": ".claude/commands/cs_setup.md",
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
        "skill_path": ".opencode/skills/cs_integration/SKILL.md",
        "command_path": ".opencode/commands/cs_setup.md",
    },
    "cursor": {
        "name": "Cursor",
        "superpowers_check_paths": [
            "~/.cursor/plugins/superpowers",
        ],
        "superpowers_install": "cursor plugin install superpowers@superpowers-marketplace",
        "skill_path": ".cursor/skills/cs_integration/SKILL.md",
        "command_path": ".cursor/skills-cursor/cs_setup/SKILL.md",
    },
}


# ── handlers ──────────────────────────────────────────────────────────────────

async def _list_my_projects(args: dict, user, db: AsyncSession) -> dict:
    proj_ids_q = await db.execute(
        select(Requirement.project_id)
        .where(
            Requirement.assignee_id == str(user.id),
            Requirement.status.in_(ACTIVE_STATUSES),
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
    lines = [
        f"- {p.name}"
        + (f" [{p.identifier}]" if p.identifier else "")
        + f" (id={p.id}, status={p.status.value if hasattr(p.status, 'value') else p.status})"
        for p in projects
    ]
    return _text("你的项目：\n" + "\n".join(lines))


async def _list_iterations(args: dict, user, db: AsyncSession) -> dict:
    project_id = args.get("project_id")
    if not project_id:
        return None
    result = await db.execute(
        select(Iteration).where(Iteration.project_id == project_id).order_by(Iteration.created_at.desc())
    )
    iterations = result.scalars().all()
    if not iterations:
        return _text("该项目下暂无迭代")
    lines = [
        f"- {it.name} (id={it.id}, status={it.status.value if hasattr(it.status, 'value') else it.status})"
        for it in iterations
    ]
    return _text("迭代列表：\n" + "\n".join(lines))


async def _list_my_requirements(args: dict, user, db: AsyncSession) -> dict:
    iteration_id = args.get("iteration_id")
    if not iteration_id:
        return None
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
    lines = [
        f"- [{r.priority.value if hasattr(r.priority, 'value') else r.priority}] {r.title} "
        f"(id={r.id}, status={r.status.value if hasattr(r.status, 'value') else r.status})"
        for r in reqs
    ]
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

    created = []
    for i, td in enumerate(tasks_data):
        t = Task(
            requirement_id=req_id,
            title=td.get("title", ""),
            description=td.get("description"),
            order=i,
        )
        db.add(t)
        created.append(t)
    await db.commit()
    for t in created:
        await db.refresh(t)

    task_lines = "\n".join(
        f"  {i+1}. id={t.id}  [{t.status.value}] {t.title}"
        for i, t in enumerate(created)
    )
    return _text(
        f"已同步 {len(created)} 个任务到需求 {req_id}，任务列表（含 ID，执行时用于更新状态）：\n{task_lines}\n\n"
        f"执行每个任务时：\n"
        f"  开始前调用 update_task_status(task_id=<id>, status=\"in_progress\")\n"
        f"  完成后调用 update_task_status(task_id=<id>, status=\"completed\")"
    )


async def _start_brainstorming(args: dict, user, db: AsyncSession) -> dict:
    req_id = args.get("requirement_id")
    if not req_id:
        return None
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        return {"__not_found__": True}

    proj_key = "project"
    if req.project_id:
        proj_result = await db.execute(select(Project).where(Project.id == req.project_id))
        project = proj_result.scalar_one_or_none()
        if project:
            proj_key = project.identifier or _slugify(project.name)

    iter_slug = "no-iteration"
    if req.iteration_id:
        iter_result = await db.execute(select(Iteration).where(Iteration.id == req.iteration_id))
        iteration = iter_result.scalar_one_or_none()
        if iteration:
            iter_slug = _slugify(iteration.name)

    req_slug = _slugify(req.title)
    doc_base = f"docs/cs/{proj_key}/{iter_slug}/{req_slug}"

    tasks_result = await db.execute(
        select(Task).where(Task.requirement_id == req_id).order_by(Task.order)
    )
    tasks = tasks_result.scalars().all()
    status = req.status.value if hasattr(req.status, "value") else req.status
    priority = req.priority.value if hasattr(req.priority, "value") else req.priority
    task_lines = "\n".join(
        f"  {i+1}. [{t.status.value if hasattr(t.status, 'value') else t.status}] {t.title}"
        for i, t in enumerate(tasks)
    ) or "  （暂无任务）"

    context = (
        f"## 需求上下文\n\n"
        f"**标题**: {req.title}\n"
        f"**优先级**: {priority}\n"
        f"**状态**: {status}\n"
        f"**描述**:\n{req.description or '（无描述）'}\n\n"
        f"**验收标准**:\n{req.acceptance_criteria or '（无验收标准）'}\n\n"
        f"**现有任务**:\n{task_lines}\n"
    )

    template = _read_template("brainstorm_instruction")
    instruction = template.format(req_id=req_id, doc_base=doc_base, context=context)
    return _text(instruction)


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
    allowed = TRANSITIONS.get(current, [])
    if action not in allowed:
        return _text(f"状态流转失败：{current} → {action} 不允许（允许: {allowed}）")

    req.status = RequirementStatus(action)
    req.updated_at = datetime.utcnow()
    await db.commit()
    return _text(f"需求 {req_id} 状态已更新：{current} → {action}")


async def _submit_test_result(args: dict, user, db: AsyncSession) -> dict:
    req_id = args.get("requirement_id")
    if not req_id:
        return None
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    if not result.scalar_one_or_none():
        return {"__not_found__": True}

    total = args.get("total_count", 0)
    passed = args.get("passed_count", 0)
    failed = args.get("failed_count", 0)

    if failed == 0 and passed == total and total > 0:
        test_result = TestResult.ALL_PASSED
    elif failed > 0 and passed > 0:
        test_result = TestResult.PARTIAL
    else:
        test_result = TestResult.FAILED

    tdd_phase = args.get("tdd_phase", "")
    phase_label = {
        "red": "RED（写失败测试）",
        "green": "GREEN（实现通过）",
        "refactor": "REFACTOR（重构）",
    }.get(tdd_phase, tdd_phase)

    record = UnitTestRecord(
        requirement_id=req_id,
        task_id=args.get("task_id"),
        task_title=args.get("task_title") or (f"[{phase_label}]" if phase_label else None),
        test_type=args.get("test_type", "unit"),
        total_count=total,
        passed_count=passed,
        failed_count=failed,
        failed_tests=args.get("failed_tests"),
        coverage=args.get("coverage"),
        result=test_result,
    )
    db.add(record)
    await db.commit()

    status_icon = "✅" if test_result == TestResult.ALL_PASSED else ("⚠️" if test_result == TestResult.PARTIAL else "❌")
    msg = f"{status_icon} 测试记录已上报（{phase_label or 'unit'}）：{passed}/{total} 通过"
    if failed:
        msg += f"，{failed} 失败"
    if args.get("coverage"):
        msg += f"，覆盖率 {args['coverage']}%"
    return _text(msg)


async def _create_document(args: dict, user, db: AsyncSession) -> dict:
    req_id = args.get("requirement_id")
    title = args.get("title", "").strip()
    content = args.get("content", "")
    doc_type = args.get("document_type", "design")
    if not req_id or not title:
        return None
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    if not result.scalar_one_or_none():
        return {"__not_found__": True}
    doc = Document(
        requirement_id=req_id,
        title=title,
        content=content,
        document_type=doc_type,
        created_by=str(user.id),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return _text(f"文档已上传（id={doc.id}，类型={doc_type}）：{title}")


async def _setup_dev_environment(args: dict, user, db: AsyncSession) -> dict:
    skill_content = _read_file(_SKILLS_DIR / "cs_integration.md")
    setup_cmd_content = _read_cmd("cs_setup")
    start_cmd_content = _read_cmd("cs_start")
    cs_doc_content = _read_cmd("cs_doc")

    sections = ["## CodeSeer 开发环境安装指南\n"]
    sections.append("请根据你使用的 AI 工具，按对应步骤操作：\n")

    for harness in _HARNESS_SETUP.values():
        check_paths = "\n".join(f"  - `{p}`" for p in harness["superpowers_check_paths"])
        cmd_dir = harness["command_path"].rsplit("/", 1)[0]
        sections.append(
            f"### {harness['name']}\n\n"
            f"**第 1 步：检查 superpowers 是否已安装**\n{check_paths}\n\n"
            f"**第 2 步：未安装时执行**\n```\n{harness['superpowers_install']}\n```\n\n"
            f"**第 3 步：安装 CodeSeer 专属技能**\n"
            f"将【cs_integration 技能文件】内容写入 `{harness['skill_path']}`（目录不存在时先创建）\n\n"
            f"**第 4 步：安装斜杠命令**\n"
            f"将【cs_setup 命令文件】写入 `{harness['command_path']}`\n"
            f"将【cs_start 命令文件】写入 `{cmd_dir}/cs_start.md`\n"
            f"将【cs_doc 命令文件】写入 `{cmd_dir}/cs_doc.md`\n"
            f"（目录不存在时先创建，文件已存在则覆盖）\n"
        )

    return {
        "content": [
            {"type": "text", "text": "\n".join(sections)},
            {"type": "text", "text": f"【cs_integration 技能文件】\n\n{skill_content}"},
            {"type": "text", "text": f"【cs_setup 命令文件】\n\n{setup_cmd_content}"},
            {"type": "text", "text": f"【cs_start 命令文件】\n\n{start_cmd_content}"},
            {"type": "text", "text": f"【cs_doc 命令文件】\n\n{cs_doc_content}"},
        ]
    }


TOOL_HANDLERS = {
    "list_my_projects": _list_my_projects,
    "list_iterations": _list_iterations,
    "list_my_requirements": _list_my_requirements,
    "start_brainstorming": _start_brainstorming,
    "get_requirement_detail": _get_requirement_detail,
    "sync_tasks": _sync_tasks,
    "submit_test_result": _submit_test_result,
    "update_requirement_status": _update_requirement_status,
    "create_document": _create_document,
    "setup_dev_environment": _setup_dev_environment,
}
