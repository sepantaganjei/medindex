from __future__ import annotations

import io
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pydicom
from PIL import Image
from pydicom.multival import MultiValue

from app.core.config import config
from app.db.database import SessionLocal
from app.db.models import Series, Study
from app.services.object_storage_service import ObjectStorageService


NIFTI_SUFFIXES = (".nii", ".nii.gz")


@dataclass(frozen=True)
class ViewerSeriesContext:
    collection: str
    patient_id: str
    study_uid: str
    series_uid: str
    modality: str | None


class ViewerAssetError(RuntimeError):
    pass


class ViewerSeriesNotFound(ViewerAssetError):
    pass


object_storage_service = ObjectStorageService(
    config.object_storage_endpoint,
    config.object_storage_access_key,
    config.object_storage_secret_key,
    config.object_storage_secure,
)


def build_object_url(base_url: str, object_name: str) -> str:
    safe_object_name = quote(object_name, safe="/")
    return f"{base_url.rstrip('/')}/api/object-storage/objects/{safe_object_name}"


def upload_nifti_assets(collection_name: str, root_path: str | Path) -> int:
    """Legacy no-op kept for the older /addNIFTIdataset endpoint.

    New ZIP ingestion uploads files through app.etl.zip_pipeline using the
    collection/patient/study/series/file layout that the viewer consumes.
    """
    return 0


def get_series_context(series_uid: str, collection: str | None = None) -> ViewerSeriesContext:
    session = SessionLocal()
    try:
        query = session.query(Series).filter(Series.instance_uid == series_uid)
        if collection:
            query = query.join(Series.study).filter(Study.collection == collection)
        series = query.first()

        if not series or not series.study:
            raise ViewerSeriesNotFound("Series not found in the local database.")
        if not series.study.collection:
            raise ViewerSeriesNotFound("Series collection is missing.")
        if not series.study.patient_id:
            raise ViewerSeriesNotFound("Series patient is missing.")

        return ViewerSeriesContext(
            collection=series.study.collection,
            patient_id=series.study.patient_id,
            study_uid=series.study_instance_uid,
            series_uid=series.instance_uid,
            modality=series.modality,
        )
    finally:
        session.close()


def series_object_prefix(context: ViewerSeriesContext) -> str:
    return "/".join(
        [
            context.collection,
            context.patient_id,
            context.study_uid,
            context.series_uid,
            "",
        ]
    )


def _list_series_object_names(context: ViewerSeriesContext) -> list[str]:
    objects = object_storage_service.list_objects(
        config.object_storage_bucket,
        series_object_prefix(context),
        recursive=True,
        limit=None,
    )
    return sorted(
        object_name
        for object_name in (item.object_name for item in objects)
        if object_name
    )


def _is_nifti_object(object_name: str) -> bool:
    return object_name.lower().endswith(NIFTI_SUFFIXES)


def _is_dicom_object(object_name: str) -> bool:
    return object_name.lower().endswith(".dcm")


def _safe_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _dicom_instance_sort_key(object_name: str) -> tuple[bool, int, str]:
    try:
        payload = object_storage_service.get_object_bytes(config.object_storage_bucket, object_name)
        dataset = pydicom.dcmread(io.BytesIO(payload), stop_before_pixels=True, force=True)
        instance_number = _safe_int(getattr(dataset, "InstanceNumber", None))
    except Exception:
        instance_number = None
    return (instance_number is None, instance_number or 0, object_name)


def build_series_viewer(series_uid: str, collection: str | None, base_url: str) -> dict:
    context = get_series_context(series_uid, collection)
    object_names = _list_series_object_names(context)
    if not object_names:
        raise ViewerAssetError("No uploaded files found for this series.")

    nifti_objects = [object_name for object_name in object_names if _is_nifti_object(object_name)]
    dicom_objects = [object_name for object_name in object_names if _is_dicom_object(object_name)]

    if str(context.modality or "").strip().upper() == "NIFTI" or nifti_objects:
        if not nifti_objects:
            raise ViewerAssetError("Series is marked as NIfTI but no NIfTI file was found.")
        object_name = sorted(nifti_objects)[0]
        return {
            "source": "NIfTI",
            "collection": context.collection,
            "series_uid": context.series_uid,
            "objects": [
                {
                    "object_name": object_name,
                    "url": build_object_url(base_url, object_name),
                }
            ],
        }

    if dicom_objects:
        instances = [
            {
                "object_name": object_name,
                "url": f"{base_url.rstrip('/')}/api/viewer/dicom/render?object_name={quote(object_name, safe='')}",
            }
            for object_name in sorted(dicom_objects, key=_dicom_instance_sort_key)
        ]
        return {
            "source": "DICOM",
            "collection": context.collection,
            "series_uid": context.series_uid,
            "objects": instances,
        }

    raise ViewerAssetError("No DICOM or NIfTI file was found for this series.")


def _first_window_value(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, MultiValue) or isinstance(value, (list, tuple)):
        value = value[0] if value else None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_grayscale(array: np.ndarray, dataset) -> np.ndarray:
    pixels = array.astype(np.float32)

    slope = float(getattr(dataset, "RescaleSlope", 1) or 1)
    intercept = float(getattr(dataset, "RescaleIntercept", 0) or 0)
    pixels = pixels * slope + intercept

    center = _first_window_value(getattr(dataset, "WindowCenter", None))
    width = _first_window_value(getattr(dataset, "WindowWidth", None))
    if center is not None and width and width > 0:
        low = center - width / 2
        high = center + width / 2
    else:
        low = float(np.nanmin(pixels))
        high = float(np.nanmax(pixels))

    if high <= low:
        return np.zeros(pixels.shape, dtype=np.uint8)

    pixels = np.clip((pixels - low) / (high - low), 0, 1)
    pixels = (pixels * 255).astype(np.uint8)

    if getattr(dataset, "PhotometricInterpretation", "") == "MONOCHROME1":
        pixels = 255 - pixels

    return pixels


def _image_from_pixels(pixels: np.ndarray, dataset, frame: int) -> Image.Image:
    if pixels.ndim == 4:
        pixels = pixels[min(frame, pixels.shape[0] - 1)]
    elif pixels.ndim == 3 and int(getattr(dataset, "SamplesPerPixel", 1) or 1) == 1:
        pixels = pixels[min(frame, pixels.shape[0] - 1)]

    if pixels.ndim == 3:
        return Image.fromarray(pixels.astype(np.uint8))
    return Image.fromarray(_normalize_grayscale(pixels, dataset), mode="L")


def _render_dicom_with_pydicom(payload: bytes, frame: int) -> Image.Image:
    dataset = pydicom.dcmread(io.BytesIO(payload), force=True)
    return _image_from_pixels(dataset.pixel_array, dataset, frame)


def _render_dicom_with_simpleitk(payload: bytes, frame: int) -> Image.Image:
    try:
        import SimpleITK as sitk
    except ImportError as exc:
        raise ViewerAssetError("SimpleITK is not installed.") from exc

    with tempfile.NamedTemporaryFile(suffix=".dcm") as temp_file:
        temp_file.write(payload)
        temp_file.flush()
        image = sitk.ReadImage(temp_file.name)

    array = sitk.GetArrayFromImage(image)
    if array.ndim == 3:
        array = array[min(frame, array.shape[0] - 1)]
    elif array.ndim > 3:
        array = array.reshape((-1, *array.shape[-2:]))[min(frame, array.shape[0] - 1)]

    array = array.astype(np.float32)
    low = float(np.nanmin(array))
    high = float(np.nanmax(array))
    if high <= low:
        pixels = np.zeros(array.shape, dtype=np.uint8)
    else:
        pixels = np.clip((array - low) / (high - low), 0, 1)
        pixels = (pixels * 255).astype(np.uint8)

    return Image.fromarray(pixels, mode="L")


def render_dicom_png(object_name: str, frame: int = 0) -> bytes:
    payload = object_storage_service.get_object_bytes(config.object_storage_bucket, object_name)

    try:
        image = _render_dicom_with_pydicom(payload, frame)
    except Exception as pydicom_exc:
        try:
            image = _render_dicom_with_simpleitk(payload, frame)
        except Exception as sitk_exc:
            raise ViewerAssetError(
                "DICOM pixel data could not be decoded. "
                f"pydicom error: {pydicom_exc}; SimpleITK error: {sitk_exc}"
            ) from sitk_exc

    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
