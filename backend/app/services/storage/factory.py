from typing import Optional

from app.core.config import settings
from .base import StorageBackend
from .ftp import FTPStorageBackend
from .oss import OSSStorageBackend


class StorageFactory:
    """存储后端工厂（单例）"""

    _backend: Optional[StorageBackend] = None

    @staticmethod
    def get_backend() -> StorageBackend:
        """获取存储后端实例"""
        if StorageFactory._backend is not None:
            return StorageFactory._backend

        storage_type = settings.STORAGE_TYPE

        if storage_type == "oss":
            StorageFactory._backend = OSSStorageBackend(
                endpoint=settings.OSS_ENDPOINT,
                access_key_id=settings.OSS_ACCESS_KEY_ID,
                access_key_secret=settings.OSS_ACCESS_KEY_SECRET,
                bucket_name=settings.OSS_BUCKET_NAME,
            )
        else:  # default to FTP
            StorageFactory._backend = FTPStorageBackend(
                host=settings.FTP_HOST,
                port=settings.FTP_PORT,
                username=settings.FTP_USERNAME,
                password=settings.FTP_PASSWORD,
                base_path=settings.FTP_REMOTE_BASE_PATH,
            )

        return StorageFactory._backend

    @staticmethod
    def reset():
        """重置后端实例（用于测试）"""
        StorageFactory._backend = None