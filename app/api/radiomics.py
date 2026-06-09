from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import viewer_assets
from app.services.radiomics import create_mask, decode_image_bytes, extract_pyradiomics_features

router = APIRouter(prefix="/api/radiomics", tags=["radiomics"])


class Point(BaseModel):
    x: float
    y: float


class RenderSource(BaseModel):
    source: str = Field(..., min_length=1)
    object_name: str = Field(..., min_length=1)
    axis: str = "z"
    slice: int = Field(0, ge=0)
    frame: int = Field(0, ge=0)


class RadiomicsRequest(BaseModel):
    render_source: RenderSource
    points: list[Point] = Field(..., min_length=3)


class RadiomicsResponse(BaseModel):
    source: str
    object_name: str
    features: dict[str, float | None]


def _render_source_png(render_source: RenderSource) -> bytes:
    source = render_source.source.strip().upper()

    if source == "NIFTI":
        return viewer_assets.render_nifti_png(
            render_source.object_name,
            render_source.axis,
            render_source.slice,
        )
    if source == "DICOM":
        return viewer_assets.render_dicom_png(
            render_source.object_name,
            render_source.frame,
        )

    raise HTTPException(status_code=400, detail="Unsupported render source")


@router.post("/extract", response_model=RadiomicsResponse)
def extract_features(payload: RadiomicsRequest) -> RadiomicsResponse:
    try:
        image_bytes = _render_source_png(payload.render_source)
    except viewer_assets.ViewerAssetError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

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

    return RadiomicsResponse(
        source=payload.render_source.source,
        object_name=payload.render_source.object_name,
        features=features,
    )
