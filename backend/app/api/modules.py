from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Module, Document, Skill, Project, Requirement
from app.schemas.schemas import ModuleCreate, ModuleUpdate, ModuleResponse, SkillResponse

router = APIRouter(prefix="/modules", tags=["modules"])


def _module_dict(m: Module, doc_count: int = 0, children: list = None) -> dict:
    return {
        "id": m.id,
        "name": m.name,
        "description": m.description,
        "parent_id": m.parent_id,
        "path": m.path,
        "project_id": m.project_id,
        "is_active": m.is_active,
        "skill_id": m.skill_id,
        "created_at": m.created_at,
        "updated_at": m.updated_at,
        "document_count": doc_count,
        "children": children if children is not None else [],
    }


def build_tree(modules: List[Module], doc_counts: dict) -> List[dict]:
    nodes = {m.id: _module_dict(m, doc_counts.get(m.id, 0)) for m in modules}
    roots = []
    for m in modules:
        node = nodes[m.id]
        if m.parent_id and m.parent_id in nodes:
            nodes[m.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


@router.get("")
async def list_modules(project_id: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    query = select(Module).order_by(Module.created_at)
    if project_id:
        query = query.where(Module.project_id == project_id)
    result = await db.execute(query)
    modules = result.scalars().all()
    doc_counts = {}
    if modules:
        from sqlalchemy import func
        count_result = await db.execute(
            select(Document.module_id, func.count(Document.id))
            .where(Document.module_id.in_([m.id for m in modules]))
            .group_by(Document.module_id)
        )
        for mid, cnt in count_result.all():
            doc_counts[mid] = cnt
    return build_tree(modules, doc_counts)


@router.post("")
async def create_module(mod: ModuleCreate, db: AsyncSession = Depends(get_db)):
    data = mod.model_dump()
    if data.get("parent_id"):
        parent_result = await db.execute(select(Module).where(Module.id == data["parent_id"]))
        parent_module = parent_result.scalar_one_or_none()
        if not parent_module:
            raise HTTPException(status_code=400, detail="Parent module not found")
        data["path"] = f"{parent_module.path or '/'}{parent_module.name}/"
    data["parent_id"] = str(data["parent_id"]) if data.get("parent_id") else None
    db_module = Module(**data)
    db.add(db_module)
    await db.commit()
    await db.refresh(db_module)
    return _module_dict(db_module)


@router.get("/{module_id}")
async def get_module(module_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Module).where(Module.id == module_id))
    mod = result.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
    return _module_dict(mod)


@router.put("/{module_id}")
async def update_module(module_id: str, update: ModuleUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Module).where(Module.id == module_id))
    mod = result.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
    for k, v in update.model_dump(exclude_unset=True).items():
        if k == "parent_id" and v:
            v = str(v)
        setattr(mod, k, v)
    await db.commit()
    await db.refresh(mod)
    return _module_dict(mod)


@router.delete("/{module_id}")
async def delete_module(module_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Module).where(Module.id == module_id))
    mod = result.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
    # check for children
    children = await db.execute(select(Module).where(Module.parent_id == module_id))
    if children.scalars().all():
        raise HTTPException(status_code=400, detail="Module has children, delete them first")
    await db.delete(mod)
    await db.commit()
    return {"message": "Module deleted"}


@router.get("/{module_id}/documents")
async def list_module_documents(module_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).where(Document.module_id == module_id).order_by(Document.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{module_id}/knowledge")
async def get_module_knowledge(module_id: str, db: AsyncSession = Depends(get_db)):
    """模块知识库汇总：文档 + 关联 Skill"""
    mod_result = await db.execute(select(Module).where(Module.id == module_id))
    mod = mod_result.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
    docs = (await db.execute(
        select(Document).where(Document.module_id == module_id, Document.status == "archived")
        .order_by(Document.updated_at.desc())
    )).scalars().all()
    skills = []
    if mod.skill_id:
        skill = (await db.execute(select(Skill).where(Skill.id == mod.skill_id))).scalar_one_or_none()
        if skill:
            skills.append(skill)
    return {
        "module": mod,
        "documents": docs,
        "skills": skills,
        "document_count": len(docs),
    }


_TYPE_LABELS = {
    "analysis": "需求文档",
    "design":   "设计文档",
    "api":      "API 文档",
    "diagram":  "架构图",
    "other":    "其他文档",
}
_TYPE_ORDER = ["analysis", "design", "api", "diagram", "other"]


@router.get("/{module_id}/project-documents")
async def list_project_documents(module_id: str, db: AsyncSession = Depends(get_db)):
    """返回该模块所属项目下所有需求挂靠的文档，按 document_type 分组"""
    mod = (await db.execute(select(Module).where(Module.id == module_id))).scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")

    grouped: dict = {k: [] for k in _TYPE_ORDER}
    if not mod.project_id:
        return grouped

    reqs = (await db.execute(
        select(Requirement).where(Requirement.project_id == str(mod.project_id))
    )).scalars().all()
    if not reqs:
        return grouped

    req_title_map = {str(r.id): r.title for r in reqs}
    req_ids = list(req_title_map.keys())

    docs = (await db.execute(
        select(Document)
        .where(Document.requirement_id.in_(req_ids))
        .order_by(Document.updated_at.desc())
    )).scalars().all()

    for d in docs:
        dt = d.document_type.value if hasattr(d.document_type, "value") else str(d.document_type)
        key = dt if dt in grouped else "other"
        grouped[key].append({
            "id": str(d.id),
            "title": d.title,
            "document_type": dt,
            "requirement_id": str(d.requirement_id) if d.requirement_id else None,
            "requirement_title": req_title_map.get(str(d.requirement_id), ""),
            "status": d.status,
            "version": d.version,
            "updated_at": str(d.updated_at),
        })

    return grouped


def _build_skill_prompt(module_name: str, docs: list) -> str:
    by_type: dict = {k: [] for k in _TYPE_ORDER}
    for d in docs:
        dt = d.document_type.value if hasattr(d.document_type, "value") else str(d.document_type)
        key = dt if dt in by_type else "other"
        by_type[key].append(d)

    total = len(docs)
    lines = [f"## 知识库文档（{total} 份）"]
    for dtype in _TYPE_ORDER:
        if not by_type[dtype]:
            continue
        lines.append(f"\n### {_TYPE_LABELS[dtype]}")
        for d in by_type[dtype]:
            lines.append(f"- {d.title}（id: `{d.id}`）")

    lines.append("""
## 使用说明

当你需要查阅某份文档的具体内容时，调用 MCP 工具：

get_document(document_id="<上方对应的 id>")

工具会返回该文档的完整 Markdown 正文，请基于返回内容回答问题。

## 你的职责

当用户处理 {module_name} 模块相关需求时：
1. 根据问题判断需要查阅哪份文档，调用 get_document 获取内容
2. 基于文档内容给出准确回答，并引用具体章节
3. 在代码建议中体现文档中描述的架构规范与约束""".format(module_name=module_name))

    return "\n".join(lines)


@router.post("/{module_id}/sync-skill", response_model=SkillResponse)
async def sync_skill(module_id: str, db: AsyncSession = Depends(get_db)):
    """根据模块当前已关联的归档文档自动生成/更新 Skill"""
    mod = (await db.execute(select(Module).where(Module.id == module_id))).scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")

    docs = (await db.execute(
        select(Document)
        .where(Document.module_id == module_id, Document.status == "archived")
        .order_by(Document.updated_at.desc())
    )).scalars().all()

    skill_name = mod.name
    if mod.project_id:
        proj = (await db.execute(select(Project).where(Project.id == mod.project_id))).scalar_one_or_none()
        if proj and proj.identifier:
            skill_name = f"{proj.identifier}_{mod.name}"

    prompt = _build_skill_prompt(mod.name, docs)
    description = f"{mod.name} 模块知识文档（{len(docs)} 份）"

    existing = None
    if mod.skill_id:
        existing = (await db.execute(select(Skill).where(Skill.id == mod.skill_id))).scalar_one_or_none()

    if existing:
        existing.name = skill_name
        existing.description = description
        existing.prompt_template = prompt
        await db.commit()
        await db.refresh(existing)
        return existing

    skill = Skill(
        name=skill_name,
        module_id=module_id,
        description=description,
        source="manual",
        status="active",
        prompt_template=prompt,
        parameters='{"temperature": 0.3, "max_tokens": 4000}',
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    mod.skill_id = skill.id
    await db.commit()
    return skill


class SkillMetaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.patch("/{module_id}/skill", response_model=SkillResponse)
async def update_skill_meta(module_id: str, body: SkillMetaUpdate, db: AsyncSession = Depends(get_db)):
    """更新 Skill 的名称和描述"""
    mod = (await db.execute(select(Module).where(Module.id == module_id))).scalar_one_or_none()
    if not mod or not mod.skill_id:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill = (await db.execute(select(Skill).where(Skill.id == mod.skill_id))).scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    if body.name is not None:
        skill.name = body.name
    if body.description is not None:
        skill.description = body.description
    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/{module_id}/skill")
async def delete_skill(module_id: str, db: AsyncSession = Depends(get_db)):
    """删除模块关联的 Skill"""
    mod = (await db.execute(select(Module).where(Module.id == module_id))).scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
    if not mod.skill_id:
        raise HTTPException(status_code=404, detail="该模块暂无 Skill")
    skill = (await db.execute(select(Skill).where(Skill.id == mod.skill_id))).scalar_one_or_none()
    if skill:
        await db.delete(skill)
    mod.skill_id = None
    await db.commit()
    return {"message": "Skill 已删除"}
