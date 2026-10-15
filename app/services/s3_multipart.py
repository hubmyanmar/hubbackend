import os
import re
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.config import Config


def _client():
    region = os.getenv("AWS_REGION")
    if not region:
        raise RuntimeError("AWS_REGION must be configured")
    # boto3 uses the standard credential chain (IAM role in deployed environments).
    return boto3.client("s3", region_name=region, config=Config(signature_version="s3v4"))


def _bucket() -> str:
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        raise RuntimeError("S3_BUCKET_NAME must be configured")
    return bucket


def build_object_key(user_id: int, meeting_id: int, filename: str) -> str:
    """Generate a safe unique object key scoped to an authenticated user and meeting."""
    basename = filename.replace("\\", "/").split("/")[-1]
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", basename).strip("._") or "audio"
    return f"audio/{user_id}/{meeting_id}/{uuid4().hex}/{safe_name}"


def initiate_multipart_upload(*, object_key: str, content_type: str) -> str:
    response = _client().create_multipart_upload(
        Bucket=_bucket(), Key=object_key, ContentType=content_type
    )
    return response["UploadId"]


def generate_presigned_url_for_part(
    *, object_key: str, upload_id: str, part_number: int, expires_in: int = 900
) -> str:
    return _client().generate_presigned_url(
        "upload_part",
        Params={
            "Bucket": _bucket(), "Key": object_key,
            "UploadId": upload_id, "PartNumber": part_number,
        },
        ExpiresIn=expires_in,
    )


def generate_presigned_get_url(*, object_key: str, expires_in: int = 900) -> str:
    """Create a short-lived URL for reading a private S3 object."""
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": _bucket(), "Key": object_key},
        ExpiresIn=expires_in,
    )


def download_object_to_file(
    *, object_key: str, destination: Path, max_bytes: int | None = None
) -> None:
    """Download a private object using the backend's AWS credential chain."""
    client = _client()
    bucket = _bucket()
    metadata = client.head_object(Bucket=bucket, Key=object_key)
    size = metadata.get("ContentLength", 0)
    if max_bytes is not None and size > max_bytes:
        raise ValueError(f"Audio object exceeds the {max_bytes}-byte processing limit")
    client.download_file(bucket, object_key, str(destination))


def complete_multipart_upload(*, object_key: str, upload_id: str, parts: list[dict]):
    return _client().complete_multipart_upload(
        Bucket=_bucket(), Key=object_key, UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )


def abort_multipart_upload(*, object_key: str, upload_id: str) -> None:
    _client().abort_multipart_upload(
        Bucket=_bucket(), Key=object_key, UploadId=upload_id
    )


def object_url(object_key: str) -> str:
    # This is an object location, not a public download link. Keep the bucket private.
    return f"s3://{_bucket()}/{object_key}"
