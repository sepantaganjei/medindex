from __future__ import annotations

import io
import re
import tempfile
import zipfile
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pydicom
from PIL import Image
from pydicom.multival import MultiValue

from app.core.config import config
from app.db.database import SessionLocal
from app.db.models import Collection, Series, Study
from app.etl import extract
from app.services.object_storage_service import ObjectStorageService


NIFTI_SUFFIXES = (".nii", ".nii.gz")
MAX_NIFTI_VOLUME_CACHE_ITEMS = 3
MAX_NIFTI_SLICE_CACHE_ITEMS = 512
MAX_REMOTE_DICOM_ZIP_FILES = 20_000
MAX_REMOTE_DICOM_UNCOMPRESSED_BYTES = 20 * 1024 * 1024 * 1024
MAX_REMOTE_DICOM_SINGLE_FILE_BYTES = 2 * 1024 * 1024 * 1024


@dataclass(frozen=True)
class ViewerSeriesContext:
    collection: str
    patient_id: str
    study_uid: str
    series_uid: str
    modality: str | None
    collection_type: str | None = None
    remote: bool = False


@dataclass(frozen=True)
class CachedNiftiVolume:
    array: np.ndarray
    size: tuple[int, ...]


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

nifti_volume_cache: OrderedDict[str, CachedNiftiVolume] = OrderedDict()
nifti_slice_png_cache: OrderedDict[tuple[str, str, int], bytes] = OrderedDict()


def get_series_context(
    series_uid: str,
    collection: str | None = None,
    patient_id: str | None = None,
    study_uid: str | None = None,
    collection_type: str | None = None,
    remote: bool = False,
) -> ViewerSeriesContext:
    session = SessionLocal()
    try:
        query = session.query(Series).filter(Series.series_instance_uid == series_uid)
        if collection:
            query = query.join(Series.study).filter(Study.collection_name_study == collection)
        series = query.first()

        if not series and remote and collection and patient_id and study_uid:
            return ViewerSeriesContext(
                collection=collection,
                patient_id=patient_id,
                study_uid=study_uid,
                series_uid=series_uid,
                modality="DICOM",
                collection_type=collection_type or "dicom",
                remote=True,
            )

        if not series or not series.study:
            raise ViewerSeriesNotFound("Series not found in the local database.")
        if not series.study.collection_name_study:
            raise ViewerSeriesNotFound("Series collection is missing.")
        if not series.study.patient_id_study:
            raise ViewerSeriesNotFound("Series patient is missing.")

        collection_record = (
            session
            .query(Collection)
            .filter(Collection.collection_name == series.study.collection_name_study)
            .first()
        )

        return ViewerSeriesContext(
            collection=series.study.collection_name_study,
            patient_id=series.study.patient_id_study,
            study_uid=series.study_instance_uid_series,
            series_uid=series.series_instance_uid,
            modality=series.modality,
            collection_type=collection_record.type if collection_record else collection_type,
            remote=bool(collection_record.remote) if collection_record else remote,
        )
    finally:
        session.close()


def series_object_prefix(context: ViewerSeriesContext) -> str:
    return "/".join([
        context.collection,
        context.patient_id,
        context.study_uid,
        context.series_uid,
        "",
    ])


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


def _render_url(base_url: str, path: str, object_name: str, **params) -> str:
    query_parts = [f"object_name={quote(object_name, safe='')}"]
    query_parts.extend(
        f"{key}={quote(str(value), safe='')}" for key, value in params.items()
    )
    return f"{base_url.rstrip('/')}{path}?{'&'.join(query_parts)}"


def _safe_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_object_segment(value: str | None, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip())
    return cleaned.strip("._-") or fallback


def _looks_like_dicom_dataset(dataset) -> bool:
    return any(
        hasattr(dataset, field)
        for field in (
            "SOPClassUID",
            "SOPInstanceUID",
            "PatientID",
            "StudyInstanceUID",
            "SeriesInstanceUID",
        )
    )


def _is_zip_symlink(info: zipfile.ZipInfo) -> bool:
    return (info.external_attr >> 16) & 0o170000 == 0o120000


def _validate_remote_dicom_zip(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = [info for info in archive.infolist() if not info.is_dir()]
    if len(members) > MAX_REMOTE_DICOM_ZIP_FILES:
        raise ViewerAssetError("Remote DICOM ZIP contains too many files.")

    total_size = 0
    for info in members:
        if _is_zip_symlink(info):
            raise ViewerAssetError("Remote DICOM ZIP contains unsupported symlinks.")
        if info.file_size > MAX_REMOTE_DICOM_SINGLE_FILE_BYTES:
            raise ViewerAssetError("Remote DICOM ZIP contains a file that is too large.")
        total_size += info.file_size
        if total_size > MAX_REMOTE_DICOM_UNCOMPRESSED_BYTES:
            raise ViewerAssetError("Remote DICOM ZIP is too large.")

    return members


def _upload_remote_dicom_series(context: ViewerSeriesContext) -> list[str]:
    try:
        response = extract.getZip(context.series_uid)
    except Exception as exc:
        raise ViewerAssetError("Remote DICOM series download failed.") from exc

    uploaded_objects: list[str] = []
    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            for info in _validate_remote_dicom_zip(archive):
                payload = archive.read(info)
                try:
                    dataset = pydicom.dcmread(
                        io.BytesIO(payload),
                        stop_before_pixels=True,
                        force=True,
                    )
                except Exception:
                    continue

                if not _looks_like_dicom_dataset(dataset):
                    continue
                if str(getattr(dataset, "SeriesInstanceUID", "")).strip() != context.series_uid:
                    continue

                sop_uid = _safe_object_segment(
                    str(getattr(dataset, "SOPInstanceUID", "") or ""),
                    _safe_object_segment(Path(info.filename).stem, "instance"),
                )
                object_name = "/".join(
                    [
                        context.collection,
                        context.patient_id,
                        context.study_uid,
                        context.series_uid,
                        f"{sop_uid}.dcm",
                    ]
                )
                object_storage_service.upload_bytes(
                    config.object_storage_bucket,
                    object_name,
                    payload,
                    "application/dicom",
                )
                uploaded_objects.append(object_name)
    except zipfile.BadZipFile as exc:
        raise ViewerAssetError("Remote DICOM response was not a valid ZIP file.") from exc
    except Exception:
        for object_name in uploaded_objects:
            try:
                object_storage_service.delete_object(config.object_storage_bucket, object_name)
            except Exception:
                pass
        raise

    if not uploaded_objects:
        raise ViewerAssetError("Remote DICOM ZIP did not contain files for this series.")

    return sorted(uploaded_objects)


def _dicom_instance_sort_key(object_name: str) -> tuple[bool, int, str]:
    try:
        payload = object_storage_service.get_object_bytes(
            config.object_storage_bucket, object_name
        )
        dataset = pydicom.dcmread(
            io.BytesIO(payload), stop_before_pixels=True, force=True
        )
        instance_number = _safe_int(getattr(dataset, "InstanceNumber", None))
    except Exception:
        instance_number = None
    return (instance_number is None, instance_number or 0, object_name)


def build_series_viewer(
    series_uid: str,
    collection: str | None,
    base_url: str,
    patient_id: str | None = None,
    study_uid: str | None = None,
    collection_type: str | None = None,
    remote: bool = False,
) -> dict:
    context = get_series_context(
        series_uid,
        collection,
        patient_id,
        study_uid,
        collection_type,
        remote,
    )
    if context.remote and str(context.collection_type or "").strip().lower() == "dicom":
        object_names = _upload_remote_dicom_series(context)
    else:
        object_names = _list_series_object_names(context)
        if not object_names:
            if str(context.modality or "").strip().upper() == "NIFTI":
                raise ViewerAssetError("No uploaded files found for this NIfTI series.")
            object_names = _upload_remote_dicom_series(context)

    nifti_objects = [
        object_name for object_name in object_names if _is_nifti_object(object_name)
    ]
    dicom_objects = [
        object_name for object_name in object_names if _is_dicom_object(object_name)
    ]

    if str(context.modality or "").strip().upper() == "NIFTI" or nifti_objects:
        if not nifti_objects:
            raise ViewerAssetError(
                "Series is marked as NIfTI but no NIfTI file was found."
            )
        object_name = sorted(nifti_objects)[0]
        slice_count = get_nifti_slice_count(object_name)
        return {
            "source": "NIfTI",
            "collection": context.collection,
            "series_uid": context.series_uid,
            "axis": "z",
            "objects": [
                {
                    "object_name": object_name,
                    "slice": slice_index,
                    "url": _render_url(
                        base_url,
                        "/api/viewer/nifti/render",
                        object_name,
                        axis="z",
                        slice=slice_index,
                    ),
                }
                for slice_index in range(slice_count)
            ],
        }

    if dicom_objects:
        instances = [
            {
                "object_name": object_name,
                "url": _render_url(base_url, "/api/viewer/dicom/render", object_name),
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


def _normalize_array_to_image(array: np.ndarray) -> Image.Image:
    array = array.astype(np.float32)
    low = float(np.nanmin(array))
    high = float(np.nanmax(array))
    if high <= low:
        pixels = np.zeros(array.shape, dtype=np.uint8)
    else:
        pixels = np.clip((array - low) / (high - low), 0, 1)
        pixels = (pixels * 255).astype(np.uint8)
    return Image.fromarray(pixels, mode="L")


def _get_cached_nifti_volume(object_name: str) -> CachedNiftiVolume:
    cached = nifti_volume_cache.get(object_name)
    if cached is not None:
        nifti_volume_cache.move_to_end(object_name)
        return cached

    volume = _load_nifti_volume(object_name)
    nifti_volume_cache[object_name] = volume
    _evict_lru(nifti_volume_cache, MAX_NIFTI_VOLUME_CACHE_ITEMS)
    return volume


def _load_nifti_volume(object_name: str) -> CachedNiftiVolume:
    try:
        import SimpleITK as sitk
    except ImportError as exc:
        raise ViewerAssetError("SimpleITK is not installed.") from exc

    payload = object_storage_service.get_object_bytes(
        config.object_storage_bucket, object_name
    )
    with tempfile.NamedTemporaryFile(suffix=_object_suffix(object_name)) as temp_file:
        temp_file.write(payload)
        temp_file.flush()
        image = sitk.ReadImage(temp_file.name)

    return CachedNiftiVolume(
        array=sitk.GetArrayFromImage(image),
        size=tuple(int(value) for value in image.GetSize()),
    )


def _evict_lru(cache: OrderedDict, max_items: int) -> None:
    while len(cache) > max_items:
        cache.popitem(last=False)


def get_nifti_slice_count(object_name: str, axis: str = "z") -> int:
    volume = _get_cached_nifti_volume(object_name)
    axis_index = _axis_index(axis)
    return int(volume.size[axis_index]) if len(volume.size) > axis_index else 1


def render_nifti_png(object_name: str, axis: str = "z", slice_index: int = 0) -> bytes:
    volume = _get_cached_nifti_volume(object_name)
    safe_slice = _safe_nifti_slice_index(volume, axis, slice_index)
    cache_key = (object_name, axis.lower(), safe_slice)
    cached_png = nifti_slice_png_cache.get(cache_key)
    if cached_png is not None:
        nifti_slice_png_cache.move_to_end(cache_key)
        return cached_png

    array = _slice_nifti_array(volume, axis, safe_slice)
    output = io.BytesIO()
    _normalize_array_to_image(array).save(output, format="PNG")
    payload = output.getvalue()
    nifti_slice_png_cache[cache_key] = payload
    _evict_lru(nifti_slice_png_cache, MAX_NIFTI_SLICE_CACHE_ITEMS)
    return payload


def _slice_nifti_array(
    volume: CachedNiftiVolume, axis: str, slice_index: int
) -> np.ndarray:
    axis_index = _axis_index(axis)
    safe_slice = _safe_nifti_slice_index(volume, axis, slice_index)
    if axis_index == 0:
        return volume.array[:, :, safe_slice]
    if axis_index == 1:
        return volume.array[:, safe_slice, :]
    return volume.array[safe_slice, :, :]


def _safe_nifti_slice_index(
    volume: CachedNiftiVolume,
    axis: str,
    slice_index: int,
) -> int:
    axis_index = _axis_index(axis)
    if len(volume.size) <= axis_index:
        raise ViewerAssetError("Requested NIfTI axis is not available.")
    return max(0, min(slice_index, int(volume.size[axis_index]) - 1))


def _axis_index(axis: str) -> int:
    axis_map = {"x": 0, "y": 1, "z": 2}
    try:
        return axis_map[axis.lower()]
    except KeyError as exc:
        raise ViewerAssetError("axis must be x, y, or z.") from exc


def _object_suffix(object_name: str) -> str:
    return (
        ".nii.gz"
        if object_name.lower().endswith(".nii.gz")
        else Path(object_name).suffix
    )


def render_dicom_png(object_name: str, frame: int = 0) -> bytes:
    payload = object_storage_service.get_object_bytes(
        config.object_storage_bucket, object_name
    )

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
