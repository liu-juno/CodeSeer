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
        """保存文件到 FTP（使用本地文件系统模拟）"""
        # 使用本地临时目录模拟 FTP
        import os
        import aiofiles

        local_base = "/tmp/codeseer-storage"
        full_path = f"{local_base}/{path}"
        logger.info(f"Saving to FTP (local): {full_path}, size: {len(data)} bytes")

        # 确保目录存在
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)

        # 写入文件
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(data)

        return full_path

    async def load(self, path: str) -> bytes:
        """从 FTP 加载文件（使用本地文件系统模拟）"""
        import os
        import aiofiles

        local_base = "/tmp/codeseer-storage"
        full_path = f"{local_base}/{path}"
        logger.info(f"Loading from FTP (local): {full_path}")

        async with aiofiles.open(full_path, 'rb') as f:
            data = await f.read()
        return data

    async def delete(self, path: str) -> bool:
        """从 FTP 删除文件（使用本地文件系统模拟）"""
        import os

        local_base = "/tmp/codeseer-storage"
        full_path = f"{local_base}/{path}"
        logger.info(f"Deleting from FTP (local): {full_path}")

        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    async def exists(self, path: str) -> bool:
        """检查 FTP 文件是否存在（使用本地文件系统模拟）"""
        import os

        local_base = "/tmp/codeseer-storage"
        full_path = f"{local_base}/{path}"
        return os.path.exists(full_path)