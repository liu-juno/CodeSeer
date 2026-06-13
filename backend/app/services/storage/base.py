from abc import ABC, abstractmethod
from typing import Optional


class StorageBackend(ABC):
    """存储后端抽象接口"""

    @abstractmethod
    async def save(self, data: bytes, path: str) -> str:
        """
        保存文件到存储后端
        Args:
            data: 文件内容
            path: 相对路径（如 'diff/2024-06-13/xxx.diff'）
        Returns:
            实际存储路径
        """
        pass

    @abstractmethod
    async def load(self, path: str) -> bytes:
        """
        从存储后端加载文件
        Args:
            path: 相对路径
        Returns:
            文件内容
        """
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """
        从存储后端删除文件
        Args:
            path: 相对路径
        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """
        检查文件是否存在
        Args:
            path: 相对路径
        Returns:
            是否存在
        """
        pass