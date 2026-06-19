from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List

from app.core.database import get_db
from app.models.models import Skill, Module

router = APIRouter(prefix="/mcp/skills", tags=["mcp-skills"])


@router.get("/{project_id}")
async def get_skills_by_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取指定项目的所有 Skill（公共 Skill + 模块 Skill）

    - 公共 Skill：module_id 为空，status = 'active'
    - 模块 Skill：关联该项目下的模块，status = 'active'
    """

    # 查询公共 Skill（module_id 为空，status = 'active'）
    common_skills_result = await db.execute(
        select(Skill).where(
            Skill.module_id == None,
            Skill.status == "active"
        )
    )
    common_skills = common_skills_result.scalars().all()

    # 查询该项目下的模块（用于获取模块信息）
    modules_result = await db.execute(
        select(Module).where(Module.project_id == project_id)
    )
    modules = modules_result.scalars().all()
    module_ids = [m.id for m in modules]

    # 查询模块 Skill（关联该项目下的模块，status = 'active'）
    module_skills_result = await db.execute(
        select(Skill).where(
            Skill.module_id.in_(module_ids) if module_ids else False,
            Skill.status == "active"
        )
    )
    module_skills = module_skills_result.scalars().all()

    # 构建 module_id -> module_name 映射
    module_name_map = {m.id: m.name for m in modules}

    return {
        "project_id": project_id,
        "common_skills": [
            {
                "skill_id": str(s.id),
                "name": s.name,
                "description": s.description or "",
                "summary": s.summary or ""
            }
            for s in common_skills
        ],
        "module_skills": [
            {
                "module_id": str(s.module_id),
                "module_name": module_name_map.get(s.module_id, ""),
                "name": s.name,
                "description": s.description or "",
                "summary": s.summary or "",
                "knowledge_base_url": s.knowledge_base_url or ""
            }
            for s in module_skills
        ]
    }