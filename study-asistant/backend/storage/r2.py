"""Cloudflare R2 file storage (S3-compatible)."""
from __future__ import annotations

import boto3
from botocore.exceptions import ClientError

from config import settings

_client = None


def get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
        )
    return _client


def upload_file(local_path: str, key: str) -> str:
    """Upload a local file to R2. Returns the R2 object key."""
    get_client().upload_file(local_path, settings.r2_bucket, key)
    return key


def download_file(key: str, local_path: str) -> None:
    """Download an R2 object to a local path."""
    get_client().download_file(settings.r2_bucket, key, local_path)


def delete_file(key: str) -> None:
    try:
        get_client().delete_object(Bucket=settings.r2_bucket, Key=key)
    except ClientError:
        pass


def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """Generate a temporary download URL."""
    return get_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.r2_bucket, "Key": key},
        ExpiresIn=expires_in,
    )
