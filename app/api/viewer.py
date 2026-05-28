from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from app.services import viewer_assets

router = APIRouter(prefix="/api/viewer", tags=["viewer"])


@router.get("/series/{series_uid}")
def get_series_viewer(
    series_uid: str,
    request: Request,
    collection: str | None = None,
    base_url: str | None = None,
) -> dict:
    resolved_base_url = (base_url or str(request.base_url)).rstrip("/")
    try:
        return viewer_assets.build_series_viewer(
            series_uid,
            collection,
            resolved_base_url,
        )
    except viewer_assets.ViewerSeriesNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except viewer_assets.ViewerAssetError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
