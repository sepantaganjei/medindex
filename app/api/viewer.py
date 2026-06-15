# Viewer API router for series visualization and medical image rendering (DICOM/NIfTI)

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from app.services import viewer_assets

router = APIRouter(prefix="/api/viewer", tags=["viewer"])


# Builds viewer configuration for a given series UID
@router.get("/series/{series_uid}")
def get_series_viewer(
    series_uid: str,
    request: Request,
    collection: str | None = None,
    base_url: str | None = None,
    patient_id: str | None = None,
    study_uid: str | None = None,
    collection_type: str | None = None,
    remote: bool = False,
) -> dict:
    resolved_base_url = (base_url or str(request.base_url)).rstrip("/")
    try:
        return viewer_assets.build_series_viewer(
            series_uid,
            collection,
            resolved_base_url,
            patient_id,
            study_uid,
            collection_type,
            remote,
        )
    except viewer_assets.ViewerSeriesNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except viewer_assets.ViewerAssetError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# Renders a DICOM frame as a PNG image
@router.get("/dicom/render")
def render_dicom(
    object_name: str = Query(...),
    frame: int = Query(0, ge=0),
) -> Response:
    try:
        payload = viewer_assets.render_dicom_png(object_name, frame)
    except viewer_assets.ViewerAssetError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return Response(content=payload, media_type="image/png")


# Renders a NIfTI slice as a PNG image along a given axis
@router.get("/nifti/render")
def render_nifti(
    object_name: str = Query(...),
    axis: str = Query("z"),
    slice: int = Query(0, ge=0),
) -> Response:
    try:
        payload = viewer_assets.render_nifti_png(object_name, axis, slice)
    except viewer_assets.ViewerAssetError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return Response(content=payload, media_type="image/png")
