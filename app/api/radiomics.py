from __future__ import annotations

from fastapi import APIRouter, HTTPException
from minio.error import S3Error
from pydantic import BaseModel, Field

from app.core.config import config
from app.services.object_storage_service import ObjectStorageService
from app.services.radiomics import create_mask, decode_image_bytes, extract_pyradiomics_features

router = APIRouter(prefix="/api/radiomics", tags=["radiomics"])

object_storage_service = ObjectStorageService(
    config.object_storage_endpoint,
    config.object_storage_access_key,
    config.object_storage_secret_key,
    config.object_storage_secure,
)


class Point(BaseModel):
    x: float
    y: float


class RadiomicsRequest(BaseModel):
    object_key: str = Field(..., min_length=1)
    points: list[Point] = Field(..., min_length=3)


class RadiomicsResponse(BaseModel):
    object_key: str
    features: dict[str, float | None]


def _read_object_bytes(object_key: str) -> bytes:
    response = object_storage_service.get_object(config.object_storage_bucket, object_key)
    try:
        data = response.read()
    finally:
        response.release_conn()
    return data


@router.post("/extract", response_model=RadiomicsResponse)
def extract_features(payload: RadiomicsRequest) -> RadiomicsResponse:
    try:
        image_bytes = _read_object_bytes(payload.object_key)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchBucket"}:
            raise HTTPException(status_code=404, detail="Object not found") from exc
        raise

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Object is empty")

    try:
        image = decode_image_bytes(image_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    points = [(point.x, point.y) for point in payload.points]
    mask = create_mask(points, image.shape)

    try:
        features = extract_pyradiomics_features(image, mask)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RadiomicsResponse(object_key=payload.object_key, features=features)
