import asyncio
import io
import uuid
from datetime import timedelta

from minio import Minio
from minio.error import S3Error  

from bot.config import settings

_client: Minio | None = None


def get_s3_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
        )
        if not _client.bucket_exists(settings.minio_bucket):
            _client.make_bucket(settings.minio_bucket)
    return _client


async def upload_photo(file_bytes: bytes, content_type: str = "image/jpeg") -> str:
    s3_key = f"photos/{uuid.uuid4()}.jpg"

    def _upload() -> None:
        client = get_s3_client()
        client.put_object(
            bucket_name=settings.minio_bucket,
            object_name=s3_key,
            data=io.BytesIO(file_bytes),
            length=len(file_bytes),
            content_type=content_type,
        )

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _upload)
    return s3_key


def get_photo_url(s3_key: str, expires_seconds: int = 3600) -> str:
    client = get_s3_client()
    return client.presigned_get_object(
        settings.minio_bucket,
        s3_key,
        expires=timedelta(seconds=expires_seconds),
    )


async def download_photo(s3_key: str) -> bytes:
    def _download() -> bytes:
        client = get_s3_client()
        response = client.get_object(settings.minio_bucket, s3_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _download)
