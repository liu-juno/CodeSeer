from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Module, Document, Skill, Project
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


class GenerateSkillRequest(BaseModel):
    name: str
    description: Optional[str] = None
    document_ids: List[str]


@router.post("/{module_id}/generate-skill", response_model=SkillResponse)
async def generate_skill(module_id: str, body: GenerateSkillRequest, db: AsyncSession = Depends(get_db)):
    """基于手动勾选的归档文档创建 Skill"""
    mod = (await db.execute(select(Module).where(Module.id == module_id))).scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")

    if not body.document_ids:
        raise HTTPException(status_code=400, detail="请至少勾选一份文档")

    docs = (await db.execute(
        select(Document).where(
            Document.id.in_(body.document_ids),
            Document.module_id == module_id,
            Document.status == "archived",
        )
    )).scalars().all()

    if not docs:
        raise HTTPException(status_code=400, detail="未找到有效的归档文档")

    # 查询项目名，拼接 Skill 全名：{项目名}_{模块名}_{用户输入功能名}
    project_name = ""
    if mod.project_id:
        proj = (await db.execute(select(Project).where(Project.id == mod.project_id))).scalar_one_or_none()
        if proj:
            project_name = proj.name
    skill_name = f"{project_name}_{mod.name}_{body.name}".strip("_")

    doc_refs = "\n".join(
        f"- {d.title}（id: `{d.id}`）" for d in docs
    )

    prompt = f"""你是 {mod.name} 模块的领域专家。

## 知识库文档（{len(docs)} 份）

{doc_refs}

## 使用说明

当你需要查阅某份文档的具体内容时，调用 MCP 工具：

```
get_document(document_id="<上方对应的 id>")
```

工具会返回该文档的完整 Markdown 正文，请基于返回内容回答问题。

## 你的职责

当用户处理 {mod.name} 模块相关需求时：
1. 根据问题判断需要查阅哪份文档，调用 get_document 获取内容
2. 基于文档内容给出准确回答，并引用具体章节
3. 在代码建议中体现文档中描述的架构规范与约束
"""
    skill = Skill(
        name=skill_name,
        module_id=module_id,
        description=body.description or f"基于 {len(docs)} 份归档文档",
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
