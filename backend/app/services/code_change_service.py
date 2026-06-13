import json
import logging
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import CodeChange, CodeChangeStatus
from app.schemas.schemas import CodeChangeCreate, CodeChangeResponse
from app.services.storage import StorageFactory

logger = logging.getLogger(__name__)


class CodeChangeService:
    """CodeChange 业务逻辑"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = StorageFactory.get_backend()

    async def upload(
        self,
        data: CodeChangeCreate,
        created_by: Optional[str] = None
    ) -> CodeChange:
        """
        上传变更数据

        流程：
        1. 创建 CodeChange 记录（status=PENDING）
        2. 保存 diff 文件
        3. 更新记录（status=STORED）
        4. 如果失败，回滚
        """
        # 1. 生成 diff 文件路径
        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        change_id = str(uuid.uuid4())
        diff_filename = f"{change_id}.diff"
        diff_path = f"diff/{date_str}/{diff_filename}"

        # 2. 创建数据库记录
        code_change = CodeChange(
            id=change_id,
            requirement_id=data.requirement_id,
            task_id=data.task_id,
            title=data.title,
            files_changed=data.files_changed,
            lines_added=data.lines_added,
            lines_deleted=data.lines_deleted,
            modules_affected=json.dumps(data.modules_affected),
            exceptions=json.dumps(data.exceptions),
            diff_path=diff_path,
            diff_size=len(data.diff_content.encode()),
            status=CodeChangeStatus.PENDING,
            created_by=created_by,
        )
        self.db.add(code_change)
        await self.db.commit()
        await self.db.refresh(code_change)

        try:
            # 3. 保存 diff 文件
            await self.storage.save(
                data=data.diff_content.encode(),
                path=diff_path
            )

            # 4. 更新状态为 STORED
            code_change.status = CodeChangeStatus.STORED
            await self.db.commit()
            await self.db.refresh(code_change)

            logger.info(f"CodeChange {change_id} saved successfully")
            return code_change

        except Exception as e:
            # 5. 失败处理：回滚
            logger.error(f"Failed to save CodeChange {change_id}: {e}")

            # 尝试删除已存文件
            try:
                await self.storage.delete(diff_path)
            except Exception as delete_error:
                logger.error(f"Failed to delete diff file: {delete_error}")

            # 更新状态为 FAILED
            code_change.status = CodeChangeStatus.FAILED
            await self.db.commit()

            raise

    async def get(self, change_id: str) -> Optional[CodeChange]:
        """获取变更详情"""
        result = await self.db.execute(
            select(CodeChange).where(CodeChange.id == change_id)
        )
        return result.scalar_one_or_none()

    async def get_with_diff(self, change_id: str) -> dict:
        """获取变更详情（含 diff 内容）"""
        change = await self.get(change_id)
        if not change:
            return None

        # 加载 diff 内容
        diff_content = ""
        if change.diff_path and change.status == CodeChangeStatus.STORED:
            try:
                diff_bytes = await self.storage.load(change.diff_path)
                diff_content = diff_bytes.decode()
            except Exception as e:
                logger.error(f"Failed to load diff for {change_id}: {e}")

        return {
            "id": change.id,
            "requirement_id": change.requirement_id,
            "task_id": change.task_id,
            "title": change.title,
            "files_changed": change.files_changed,
            "lines_added": change.lines_added,
            "lines_deleted": change.lines_deleted,
            "modules_affected": json.loads(change.modules_affected or "[]"),
            "exceptions": json.loads(change.exceptions or "[]"),
            "diff_content": diff_content,
            "diff_size": change.diff_size,
            "status": change.status.value,
            "created_by": change.created_by,
            "created_at": change.created_at,
            "updated_at": change.updated_at,
        }

    async def list_by_requirement(
        self,
        requirement_id: str
    ) -> List[CodeChange]:
        """按需求查询变更列表"""
        result = await self.db.execute(
            select(CodeChange)
            .where(CodeChange.requirement_id == requirement_id)
            .order_by(CodeChange.created_at.desc())
        )
        return result.scalars().all()