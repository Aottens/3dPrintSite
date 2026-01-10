"""
File storage service with local and S3-compatible backend support.
"""

import hashlib
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

import aiofiles

from app.core.settings import settings


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def save(self, file: BinaryIO, filename: str) -> str:
        """Save a file and return the storage path."""
        pass

    @abstractmethod
    async def get(self, path: str) -> bytes:
        """Retrieve file contents."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete a file."""
        pass

    @abstractmethod
    def get_url(self, path: str) -> str:
        """Get a URL or path for the file."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, file: BinaryIO, filename: str) -> str:
        # Create a unique subdirectory to avoid collisions
        unique_id = str(uuid4())[:8]
        sub_dir = self.base_path / unique_id
        sub_dir.mkdir(parents=True, exist_ok=True)

        file_path = sub_dir / filename
        content = file.read()

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        return str(file_path.relative_to(self.base_path))

    async def get(self, path: str) -> bytes:
        file_path = self.base_path / path
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete(self, path: str) -> bool:
        file_path = self.base_path / path
        if file_path.exists():
            file_path.unlink()
            # Clean up empty parent directory
            parent = file_path.parent
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
            return True
        return False

    def get_url(self, path: str) -> str:
        return f"/uploads/{path}"


class S3StorageBackend(StorageBackend):
    """S3-compatible storage backend (placeholder for production use)."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
    ):
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        # In production, initialize boto3 client here

    async def save(self, file: BinaryIO, filename: str) -> str:
        # Placeholder - implement with boto3 for production
        unique_id = str(uuid4())[:8]
        key = f"{unique_id}/{filename}"
        # await self._upload_to_s3(file, key)
        return key

    async def get(self, path: str) -> bytes:
        # Placeholder - implement with boto3 for production
        # return await self._download_from_s3(path)
        raise NotImplementedError("S3 backend not fully implemented")

    async def delete(self, path: str) -> bool:
        # Placeholder - implement with boto3 for production
        # await self._delete_from_s3(path)
        return True

    def get_url(self, path: str) -> str:
        # Return presigned URL in production
        return f"{self.endpoint_url}/{self.bucket_name}/{path}"


def get_storage_backend() -> StorageBackend:
    """Factory function to get the appropriate storage backend."""
    if settings.s3_enabled:
        return S3StorageBackend(
            endpoint_url=settings.s3_endpoint_url,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            bucket_name=settings.s3_bucket_name,
        )
    return LocalStorageBackend(settings.upload_dir)


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def validate_file_extension(filename: str) -> bool:
    """Check if file extension is allowed."""
    ext = Path(filename).suffix.lower()
    return ext in settings.allowed_extensions


def get_content_type(filename: str) -> str:
    """Get content type based on file extension."""
    ext = Path(filename).suffix.lower()
    content_types = {
        ".stl": "application/sla",
        ".3mf": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
    }
    return content_types.get(ext, "application/octet-stream")


storage_backend = get_storage_backend()
