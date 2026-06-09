import os

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import config
from app.services.object_storage_service import ObjectStorageService

router = APIRouter(prefix="/api/object-storage", tags=["object-storage"])

object_storage_service = ObjectStorageService(
    config.object_storage_endpoint,
    config.object_storage_access_key,
    config.object_storage_secret_key,
    config.object_storage_secure,
)


def _resolve_bucket(bucket: str | None) -> str:
    return bucket or config.object_storage_bucket


def _serialize_object(storage_object: object) -> dict[str, str | int | None]:
    last_modified = getattr(storage_object, "last_modified", None)
    return {
        "object_name": getattr(storage_object, "object_name", None),
        "size": getattr(storage_object, "size", None),
        "etag": getattr(storage_object, "etag", None),
        "last_modified": last_modified.isoformat() if last_modified else None,
        "content_type": getattr(storage_object, "content_type", None),
    }


@router.get("/buckets")
def list_buckets() -> dict[str, list[str]]:
    return {"buckets": object_storage_service.list_buckets()}


@router.get("/health")
def object_storage_health() -> dict[str, str]:
    object_storage_service.ensure_bucket(config.object_storage_bucket)
    return {"status": "ok", "bucket": config.object_storage_bucket}


@router.get("/objects")
def list_objects(
    prefix: str | None = None,
    limit: int | None = None,
    recursive: bool = True,
    bucket: str | None = None,
) -> dict[str, list[dict[str, str | int | None]] | str]:
    resolved_bucket = _resolve_bucket(bucket)
    objects = object_storage_service.list_objects(resolved_bucket, prefix, recursive, limit)
    return {
        "bucket": resolved_bucket,
        "objects": [_serialize_object(storage_object) for storage_object in objects],
    }


@router.get("/objects/search")
def search_objects(
    query: str,
    prefix: str | None = None,
    limit: int | None = None,
    bucket: str | None = None,
) -> dict[str, list[dict[str, str | int | None]] | str]:
    resolved_bucket = _resolve_bucket(bucket)
    objects = object_storage_service.list_objects(resolved_bucket, prefix, True, None)
    filtered_objects = [
        storage_object
        for storage_object in objects
        if storage_object.object_name and query.lower() in storage_object.object_name.lower()
    ]
    if limit is not None:
        filtered_objects = filtered_objects[:limit]
    return {
        "bucket": resolved_bucket,
        "objects": [_serialize_object(storage_object) for storage_object in filtered_objects],
    }


@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    object_name: str | None = None,
    bucket: str | None = None,
) -> dict[str, str | int | None]:
    resolved_object_name = object_name or file.filename
    if not resolved_object_name:
        raise HTTPException(status_code=400, detail="object_name is required when filename is missing")

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    resolved_bucket = _resolve_bucket(bucket)

    result = object_storage_service.upload_file(
        resolved_bucket,
        resolved_object_name,
        file.file,
        file_size,
        file.content_type,
    )

    return {
        "bucket": resolved_bucket,
        "object_name": resolved_object_name,
        "size": file_size,
        "etag": result.etag,
    }
