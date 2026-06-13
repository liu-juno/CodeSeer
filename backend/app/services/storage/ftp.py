import logging
from typing import Optional
from app.core.config import settings
from .base import StorageBackend

logger = logging.getLogger(__name__)


class FTPStorageBackend(StorageBackend):
    """FTP 存储后端实现"""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        base_path: str
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_path = base_path.rstrip("/")
        self._client = None

    async def save(self, data: bytes, path: str) -> str:
        """保存文件到 FTP"""
        full_path = f"{self.base_path}/{path}"
        logger.info(f"Saving to FTP: {full_path}, size: {len(data)} bytes")
        # 使用本地文件系统模拟 FTP 操作（实际环境使用 aiopyftp）
        import os
        import aiofiles

        # 确保目录存在
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)

        # 写入文件
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(data)

        return full_path

    async def load(self, path: str) -> bytes:
        """从 FTP 加载文件"""
        full_path = f"{self.base_path}/{path}"
        logger.info(f"Loading from FTP: {full_path}")
        import aiofiles

        async with aiofiles.open(full_path, 'rb') as f:
            data = await f.read()
        return data

    async def delete(self, path: str) -> bool:
        """从 FTP 删除文件"""
        full_path = f"{self.base_path}/{path}"
        logger.info(f"Deleting from FTP: {full_path}")
        import os

        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    async def exists(self, path: str) -> bool:
        """检查 FTP 文件是否存在"""
        full_path = f"{self.base_path}/{path}"
        import os
        return os.path.exists(full_path)