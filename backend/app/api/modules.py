from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.models import Module, Document, Skill
from app.schemas.schemas import ModuleCreate, ModuleUpdate, ModuleResponse, SkillResponse

router = APIRouter(prefix="/modules", tags=["modules"])


def build_tree(modules: List[Module], doc_counts: dict) -> List[dict]:
    nodes = {m.id: {
        "id": m.id,
        "name": m.name,
        "description": m.description,
        "parent_id": m.parent_id,
        "path": m.path,
        "is_active": m.is_active,
        "skill_id": m.skill_id,
        "created_at": m.created_at,
        "updated_at": m.updated_at,
        "document_count": doc_counts.get(m.id, 0),
        "children": [],
    } for m in modules}
    roots = []
    for m in modules:
        node = nodes[m.id]
        if m.parent_id and m.parent_id in nodes:
            nodes[m.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


@router.get("")
async def list_modules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Module).order_by(Module.created_at))
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


@router.post("", response_model=ModuleResponse)
async def create_module(mod: ModuleCreate, db: AsyncSession = Depends(get_db)):
    data = mod.model_dump()
    if data.get("parent_id"):
        # check parent exists
        parent = await db.execute(select(Module).where(Module.id == data["parent_id"]))
        if not parent.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Parent module not found")
        parent_module = parent.scalar_one()
        data["path"] = f"{parent_module.path or '/'}{parent_module.name}/"
    data["parent_id"] = str(data["parent_id"]) if data.get("parent_id") else None
    db_module = Module(**data)
    db.add(db_module)
    await db.commit()
    await db.refresh(db_module)
    return db_module


@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(module_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Module).where(Module.id == module_id))
    mod = result.scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
    return mod


@router.put("/{module_id}", response_model=ModuleResponse)
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
    return mod


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


@router.post("/{module_id}/generate-skill", response_model=SkillResponse)
async def generate_skill(module_id: str, db: AsyncSession = Depends(get_db)):
    """基于模块归档文档自动生成 Skill"""
    mod = (await db.execute(select(Module).where(Module.id == module_id))).scalar_one_or_none()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")

    docs = (await db.execute(
        select(Document).where(Document.module_id == module_id, Document.status == "archived")
    )).scalars().all()

    if not docs:
        raise HTTPException(status_code=400, detail="模块下无归档文档，无法生成 Skill")

    # 汇总所有归档文档的关键点作为 prompt 模板
    key_points = []
    summaries = []
    for d in docs:
        if d.summary:
            summaries.append(f"## {d.title}\n{d.summary}")
        if d.key_points:
            key_points.extend(d.key_points.split("\n"))

    prompt = f"""你是 {mod.name} 模块的领域专家。
该模块沉淀了 {len(docs)} 份归档文档。

## 文档摘要汇总

{chr(10).join(summaries)}

## 关键要点

{chr(10).join(f"- {p}" for p in key_points[:20])}

## 你的职责

当用户处理 {mod.name} 模块相关需求时：
1. 引用上述沉淀的知识回答问题
2. 提示用户遵循已有的设计规范
3. 在代码建议中体现该模块的架构风格
"""
    skill = Skill(
        name=f"{mod.name} 领域知识",
        module_id=module_id,
        description=f"基于 {len(docs)} 份归档文档自动生成",
        source="auto_generated",
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
