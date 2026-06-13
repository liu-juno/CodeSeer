import logging
from typing import Optional
from app.core.config import settings
from .base import StorageBackend

logger = logging.getLogger(__name__)


class OSSStorageBackend(StorageBackend):
    """OSS (S3 兼容) 存储后端实现"""

    def __init__(
        self,
        endpoint: str,
        access_key_id: str,
        access_key_secret: str,
        bucket_name: str
    ):
        self.endpoint = endpoint
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.bucket_name = bucket_name
        self._client = None

    async def save(self, data: bytes, path: str) -> str:
        """保存文件到 OSS/S3"""
        logger.info(f"Saving to OSS: {path}, size: {len(data)} bytes")
        # 使用本地文件系统模拟 S3 操作（实际环境使用 aiobotocore）
        import os
        import aiofiles

        # 本地模拟路径
        local_path = f"/tmp/oss/{self.bucket_name}/{path}"

        # 确保目录存在
        dir_path = os.path.dirname(local_path)
        os.makedirs(dir_path, exist_ok=True)

        # 写入文件
        async with aiofiles.open(local_path, 'wb') as f:
            await f.write(data)

        return path

    async def load(self, path: str) -> bytes:
        """从 OSS/S3 加载文件"""
        logger.info(f"Loading from OSS: {path}")
        import os
        import aiofiles

        local_path = f"/tmp/oss/{self.bucket_name}/{path}"

        async with aiofiles.open(local_path, 'rb') as f:
            data = await f.read()
        return data

    async def delete(self, path: str) -> bool:
        """从 OSS/S3 删除文件"""
        logger.info(f"Deleting from OSS: {path}")
        import os

        local_path = f"/tmp/oss/{self.bucket_name}/{path}"

        if os.path.exists(local_path):
            os.remove(local_path)
            return True
        return False

    async def exists(self, path: str) -> bool:
        """检查 OSS/S3 文件是否存在"""
        import os
        local_path = f"/tmp/oss/{self.bucket_name}/{path}"
        return os.path.exists(local_path)