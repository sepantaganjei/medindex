import csv
import hashlib
import json
import mimetypes
import re
import stat
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import config
from app.db.database import SessionLocal
from app.db.models import Collection, Patient, Series, Study
from app.services.object_storage_service import ObjectStorageService


ALLOWED_DATASET_TYPES = {"dicom", "nifti"}
NIFTI_SUFFIXES = (".nii", ".nii.gz")
METADATA_SUFFIXES = (".xlsx", ".csv")
MAX_ZIP_FILES = 20_000
MAX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024 * 1024
MAX_SINGLE_FILE_BYTES = 2 * 1024 * 1024 * 1024


class ZipIngestionError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class FileIdentity:
    source_path: Path
    object_name: str
    patient_id: str
    study_uid: str
    series_uid: str
    sop_uid: str | None = None


def ingest_zip_dataset(
    *,
    dataset_type: str,
    zip_file,
    metadata_file=None,
    collection_name: str | None = None,
    description: str | None = None,
    column_mapping: str | dict[str, str] | None = None,
<<<<<<< HEAD
    remote: bool,
=======
    allow_description_series_matching: bool = False,
>>>>>>> 99e30145e94da514db13e92472dc3f464f3a276e
) -> dict[str, Any]:
    dataset_type = dataset_type.lower().strip()
    if dataset_type not in ALLOWED_DATASET_TYPES:
        raise ZipIngestionError("dataset_type must be 'dicom' or 'nifti'", 400)

    parsed_column_mapping = _parse_column_mapping(column_mapping)

    with tempfile.TemporaryDirectory(prefix="bioimages_zip_") as temp_dir:
        temp_root = Path(temp_dir)
        extract_root = temp_root / "extracted"
        _safe_extract_zip(zip_file, extract_root)
        metadata_path = None
        if dataset_type == "nifti":
            metadata_path = _save_external_metadata_file(metadata_file, temp_root)
        resolved_collection = resolve_collection_name(
            getattr(zip_file, "filename", None), extract_root, collection_name
        )
        _raise_if_collection_exists(resolved_collection)

        if dataset_type == "dicom":
            result = _ingest_dicom_zip(
                extract_root,
                resolved_collection,
                description,
                remote,
            )
        else:
            result = _ingest_nifti_zip(
                extract_root,
                resolved_collection,
                description,
                parsed_column_mapping,
                metadata_path,
<<<<<<< HEAD
                remote,
=======
                allow_description_series_matching,
>>>>>>> 99e30145e94da514db13e92472dc3f464f3a276e
            )

    return result


def resolve_collection_name(
    zip_file_name: str | None,
    extracted_root: Path,
    collection_name: str | None,
) -> str:
    if collection_name and collection_name.strip():
        return sanitize_path_segment(collection_name)

    top_level = {
        path.relative_to(extracted_root).parts[0]
        for path in extracted_root.rglob("*")
        if path.relative_to(extracted_root).parts
    }
    if len(top_level) == 1:
        return sanitize_path_segment(next(iter(top_level)))

    if zip_file_name:
        name = Path(zip_file_name).name
        if name.lower().endswith(".zip"):
            name = name[:-4]
        return sanitize_path_segment(name)

    return "dataset"


def discover_dicom_files(root: Path) -> tuple[list[tuple[Path, Any]], dict[str, int]]:
    try:
        import pydicom
    except ImportError as exc:
        raise ZipIngestionError(
            "pydicom is required for DICOM ZIP ingestion", 500
        ) from exc

    valid_files: list[tuple[Path, Any]] = []
    skipped = {"non_dicom": 0, "missing_required_ids": 0}

    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        try:
            dataset = pydicom.dcmread(path, stop_before_pixels=True, force=True)
        except Exception:
            skipped["non_dicom"] += 1
            continue

        if not _looks_like_dicom(dataset):
            skipped["non_dicom"] += 1
            continue

        if not all(
            _dicom_str(dataset, field, "")
            for field in ("PatientID", "StudyInstanceUID", "SeriesInstanceUID")
        ):
            skipped["missing_required_ids"] += 1
            continue

        valid_files.append((path, dataset))

    return valid_files, skipped


def build_dicom_records_from_files(
    files: list[tuple[Path, Any]],
    collection_name: str,
    description: str | None,
    remote: bool,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[FileIdentity],
]:
    patients: dict[str, dict[str, Any]] = {}
    studies: dict[str, dict[str, Any]] = {}
    series: dict[str, dict[str, Any]] = {}
    series_studies: dict[str, set[str]] = {}
    series_file_counts: dict[str, int] = {}
    series_file_sizes: dict[str, int] = {}
    identities: list[FileIdentity] = []

    for path, dataset in files:
        patient_id = sanitize_path_segment(_dicom_str(dataset, "PatientID"))
        study_uid = sanitize_path_segment(_dicom_str(dataset, "StudyInstanceUID"))
        series_uid = sanitize_path_segment(_dicom_str(dataset, "SeriesInstanceUID"))
        sop_uid_raw = _dicom_str(dataset, "SOPInstanceUID", "")
        sop_uid = (
            sanitize_path_segment(sop_uid_raw)
            if sop_uid_raw
            else _fallback_sop_name(path)
        )
        file_size = path.stat().st_size

        patients.setdefault(
            patient_id,
            {
                "patient_id": patient_id,
                "patient_sex": _dicom_str(dataset, "PatientSex"),
                "patient_age": _extract_age(_dicom_str(dataset, "PatientAge", "")),
                "ethnic_group": _dicom_str(dataset, "EthnicGroup"),
            },
        )

        studies.setdefault(
            study_uid,
            {
                "study_instance_uid": study_uid,
                "collection_name_study": collection_name,
                "patient_id_study": patient_id,
                "study_date": _parse_date(_dicom_str(dataset, "StudyDate", "")),
                "date_released": None,
                "study_description": _dicom_str(dataset, "StudyDescription"),
                "series_count": 0,
                "longitudinal_temporal_event_type": None,
                "longitudinal_temporal_offset_from_event": None,
            },
        )

        series.setdefault(
            series_uid,
            {
                "series_instance_uid": series_uid,
                "study_instance_uid_series": study_uid,
                "modality": _dicom_str(dataset, "Modality"),
                "body_part_examined": _dicom_str(dataset, "BodyPartExamined"),
                "protocol_name": _dicom_str(dataset, "ProtocolName"),
                "series_date": _parse_date(_dicom_str(dataset, "StudyDate", "")),
                "series_description": _dicom_str(dataset, "SeriesDescription"),
                "site": None,
                "manufacturer": _dicom_str(dataset, "Manufacturer"),
                "manufacturer_model_name": _dicom_str(dataset, "ManufacturerModelName"),
                "software_versions": _dicom_str(dataset, "SoftwareVersions"),
                "image_count": 0,
                "max_submission_timestamp": None,
                "file_size": 0,
                "third_party_analysis": None,
            },
        )

        series_file_counts[series_uid] = series_file_counts.get(series_uid, 0) + 1
        series_file_sizes[series_uid] = series_file_sizes.get(series_uid, 0) + file_size
        series_studies.setdefault(study_uid, set()).add(series_uid)
        identities.append(
            FileIdentity(
                source_path=path,
                object_name="/".join([
                    collection_name,
                    patient_id,
                    study_uid,
                    series_uid,
                    f"{sop_uid}.dcm",
                ]),
                patient_id=patient_id,
                study_uid=study_uid,
                series_uid=series_uid,
                sop_uid=sop_uid,
            )
        )

    for study_uid, study_series in series_studies.items():
        studies[study_uid]["series_count"] = len(study_series)
    for series_uid, record in series.items():
        record["image_count"] = series_file_counts.get(series_uid, 0)
        record["file_size"] = series_file_sizes.get(series_uid, 0)

    collection = {
        "collection_name": collection_name,
        "type": "dicom",
        "description": description,
        "license_name": None,
        "license_uri": None,
        "data_description_uri": None,
        "remote": remote,
    }
    return (
        collection,
        list(patients.values()),
        list(studies.values()),
        list(series.values()),
        identities,
    )


def discover_nifti_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.name.lower().endswith(NIFTI_SUFFIXES)
    )


def load_tabular_metadata_file(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix not in METADATA_SUFFIXES:
        raise ZipIngestionError("metadata_file must be a .csv or .xlsx file.", 400)
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return [_normalize_row(row) for row in csv.DictReader(handle)]
    return [
        _normalize_row(row)
        for row in pd.read_excel(path, engine="openpyxl").to_dict(orient="records")
    ]


def load_optional_tabular_metadata(
    root: Path,
    metadata_path: Path | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    metadata_files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in METADATA_SUFFIXES
    )
    if metadata_path:
        if metadata_files:
            warnings.append(
                "External metadata_file was provided; metadata files inside the ZIP were ignored."
            )
        return load_tabular_metadata_file(metadata_path), warnings

    if not metadata_files:
        return [], warnings
    if len(metadata_files) > 1:
        warnings.append(
            f"Multiple metadata files found; using {metadata_files[0].name} and ignoring {len(metadata_files) - 1} others."
        )

    return load_tabular_metadata_file(metadata_files[0]), warnings


def match_nifti_rows_to_files(
    rows: list[dict[str, Any]],
    files: list[Path],
    column_mapping: dict[str, str],
    root: Path | None = None,
    allow_description_series_matching: bool = False,
) -> tuple[dict[Path, dict[str, Any]], list[Path], list[str]]:
    warnings: list[str] = []
    if not rows:
        return {}, files, warnings

    normalized_rows = [
        _apply_column_mapping(_normalize_row(row), column_mapping) for row in rows
    ]
    matches: dict[Path, dict[str, Any]] = {}
    unresolved: list[Path] = []

    for file_path in files:
        candidates = _candidate_rows_for_file(normalized_rows, file_path, root)
        if len(candidates) == 1:
            matches[file_path] = _row_with_match_scope(candidates[0], "file")
        else:
            patient_candidates = _candidate_rows_for_patient(
                normalized_rows, file_path, root
            )
            if patient_candidates:
                series_candidates = _candidate_rows_for_nifti_series(
                    patient_candidates,
                    file_path,
                    allow_description_series_matching,
                )
                if len(series_candidates) == 1 or (
                    allow_description_series_matching and series_candidates
                ):
                    matches[file_path] = _row_with_match_scope(
                        series_candidates[0], "series"
                    )
                else:
                    matches[file_path] = _row_with_match_scope(
                        patient_candidates[0], "patient"
                    )
            else:
                unresolved.append(file_path)

    if unresolved and rows:
        warnings.append(
            "Some NIfTI files could not be linked unambiguously to metadata rows; folder-derived IDs were used for those files."
        )
    patient_scope_matches = [
        row for row in matches.values() if row.get("__match_scope") == "patient"
    ]
    if patient_scope_matches:
        warnings.append(
            "Some NIfTI files were linked to metadata by Patient ID only; study and patient metadata were used, while series IDs were derived from filenames unless the series was unambiguous."
        )
    return matches, unresolved, warnings


def derive_nifti_identity_from_path(
    file: Path, collection_name: str, root: Path | None = None
) -> tuple[str, str, str]:
    relative = (
        file.relative_to(root)
        if root and file.is_relative_to(root)
        else Path(file.name)
    )
    parts = list(relative.parts[:-1])
    if parts and sanitize_path_segment(parts[0]).lower() == collection_name.lower():
        parts = parts[1:]

    stem = _nifti_stem(file.name)
    patient_source = sanitize_path_segment(parts[0]) if len(parts) >= 1 else "patient"
    patient_id = _collection_scoped_id(collection_name, patient_source)
    study_source = sanitize_path_segment(parts[1]) if len(parts) >= 2 else "study"
    study_uid = _collection_scoped_id(collection_name, study_source)
    series_source = (
        sanitize_path_segment(parts[2])
        if len(parts) >= 3
        else sanitize_path_segment(stem)
    )
    series_uid = _collection_scoped_id(collection_name, series_source)
    return patient_id, study_uid, series_uid


def upload_dataset_files_to_minio(files: list[FileIdentity]) -> list[str]:
    storage = ObjectStorageService(
        config.object_storage_endpoint,
        config.object_storage_access_key,
        config.object_storage_secret_key,
        config.object_storage_secure,
    )
    uploaded_objects = []
    for item in files:
        try:
            size = item.source_path.stat().st_size
            content_type = (
                mimetypes.guess_type(item.source_path.name)[0]
                or "application/octet-stream"
            )
            with item.source_path.open("rb") as handle:
                storage.upload_file(
                    config.object_storage_bucket,
                    item.object_name,
                    handle,
                    size,
                    content_type,
                )
            uploaded_objects.append(item.object_name)
        except Exception:
            cleanup_uploaded_objects(uploaded_objects, storage)
            raise
    return uploaded_objects


def cleanup_uploaded_objects(
    object_names: list[str],
    storage: ObjectStorageService | None = None,
) -> None:
    storage = storage or ObjectStorageService(
        config.object_storage_endpoint,
        config.object_storage_access_key,
        config.object_storage_secret_key,
        config.object_storage_secure,
    )
    for object_name in object_names:
        try:
            storage.delete_object(config.object_storage_bucket, object_name)
        except Exception:
            pass


def persist_uploaded_dataset(
    collection: dict[str, Any],
    patients: list[dict[str, Any]],
    studies: list[dict[str, Any]],
    series: list[dict[str, Any]],
    identities: list[FileIdentity],
) -> tuple[int, dict[str, int]]:
    uploaded_objects = upload_dataset_files_to_minio(identities)
    try:
        inserted_counts = _insert_records(collection, patients, studies, series)
    except Exception:
        cleanup_uploaded_objects(uploaded_objects)
        raise
    return len(uploaded_objects), inserted_counts


def sanitize_path_segment(value: Any) -> str:
    text = str(value).strip() if value is not None else ""
    text = text.replace("\\", "/").split("/")[-1]
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("._-")
    return text or "missing"


def _collection_scoped_id(collection_name: str, value: Any) -> str:
    return f"{sanitize_path_segment(collection_name)}__{sanitize_path_segment(value)}"


def _ingest_dicom_zip(
    root: Path, collection_name: str, description: str | None, remote: bool
) -> dict[str, Any]:
    valid_files, skipped = discover_dicom_files(root)
    warnings = []
    if skipped["non_dicom"]:
        warnings.append(f"Skipped {skipped['non_dicom']} non-DICOM file(s).")
    if skipped["missing_required_ids"]:
        warnings.append(
            f"Skipped {skipped['missing_required_ids']} DICOM file(s) missing PatientID, StudyInstanceUID, or SeriesInstanceUID."
        )
    if not valid_files:
        raise ZipIngestionError(
            "No valid DICOM files with required identifiers found.", 422
        )

    collection, patients, studies, series, identities = build_dicom_records_from_files(
        valid_files, collection_name, description
    )
    uploaded, inserted_counts = persist_uploaded_dataset(
        collection,
        patients,
        studies,
        series,
        identities,
    )

    return _response(
        dataset_type="dicom",
        collection_name=collection_name,
        files_discovered=len(valid_files),
        files_uploaded=uploaded,
        patients_inserted=inserted_counts["patients"],
        studies_inserted=inserted_counts["studies"],
        series_inserted=inserted_counts["series"],
        warnings=warnings,
    )


def _ingest_nifti_zip(
    root: Path,
    collection_name: str,
    description: str | None,
    column_mapping: dict[str, str],
    metadata_path: Path | None,
<<<<<<< HEAD
    remote: bool,
=======
    allow_description_series_matching: bool,
>>>>>>> 99e30145e94da514db13e92472dc3f464f3a276e
) -> dict[str, Any]:
    files = discover_nifti_files(root)
    if not files:
        raise ZipIngestionError("No NIfTI files found in ZIP.", 422)

    metadata_rows, warnings = load_optional_tabular_metadata(root, metadata_path)
    if len(metadata_rows) == 1 and len(files) == 1:
        row_matches = {
            files[0]: _row_with_match_scope(
                _apply_column_mapping(metadata_rows[0], column_mapping),
                "file",
            )
        }
        unresolved = []
    else:
        row_matches, unresolved, match_warnings = match_nifti_rows_to_files(
            metadata_rows,
            files,
            column_mapping,
            root,
            allow_description_series_matching,
        )
        warnings.extend(match_warnings)

    if unresolved:
        warnings.append(
            "Some NIfTI files could not be linked unambiguously to spreadsheet rows; folder-derived IDs were used."
        )

    collection, patients, studies, series, identities = _build_nifti_records(
        root,
        files,
        row_matches,
        collection_name,
        description,
        remote,
    )
    uploaded, inserted_counts = persist_uploaded_dataset(
        collection,
        patients,
        studies,
        series,
        identities,
    )

    return _response(
        dataset_type="nifti",
        collection_name=collection_name,
        files_discovered=len(files),
        files_uploaded=uploaded,
        patients_inserted=inserted_counts["patients"],
        studies_inserted=inserted_counts["studies"],
        series_inserted=inserted_counts["series"],
        warnings=warnings,
    )


def _build_nifti_records(
    root: Path,
    files: list[Path],
    row_matches: dict[Path, dict[str, Any]],
    collection_name: str,
    description: str | None,
    remote: bool,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[FileIdentity],
]:
    patients: dict[str, dict[str, Any]] = {}
    studies: dict[str, dict[str, Any]] = {}
    series: dict[str, dict[str, Any]] = {}
    study_series: dict[str, set[str]] = {}
    identities: list[FileIdentity] = []
    for file_path in files:
        row = row_matches.get(file_path)
        fallback_patient, fallback_study, fallback_series = (
            derive_nifti_identity_from_path(file_path, collection_name, root)
        )
        if row:
            use_series_metadata = row.get("__match_scope") in {"file", "series"}
            patient_id = sanitize_path_segment(
                _present_or_fallback(
                    _row_value(
                        row, ["patient id", "patient", "patientid", "patient_id"]
                    ),
                    fallback_patient,
                )
            )
            study_uid = sanitize_path_segment(
                _present_or_fallback(
                    _row_value(
                        row, ["study instance uid", "study uid", "studyinstanceuid"]
                    ),
                    fallback_study,
                )
            )
            if use_series_metadata:
                series_uid = sanitize_path_segment(
                    _present_or_fallback(
                        _row_value(
                            row,
                            ["series instance uid", "series uid", "seriesinstanceuid"],
                        ),
                        fallback_series,
                    )
                )
            else:
                series_uid = fallback_series
            image_count = (
                _safe_int(_row_value(row, ["image count", "images"]))
                if use_series_metadata
                else None
            )
        else:
            patient_id, study_uid, series_uid = (
                fallback_patient,
                fallback_study,
                fallback_series,
            )
            image_count = None
            use_series_metadata = False

        if image_count is None:
            image_count = _nifti_image_count(file_path)

        patients.setdefault(
            patient_id,
            {
                "patient_id": patient_id,
                "patient_sex": _row_value(
                    row, ["patient sex", "patient_sex", "sex", "gender"]
                )
                if row
                else None,
                "patient_age": _extract_age(
                    _row_value(row, ["patient age", "age", "patient_age"])
                    if row
                    else None
                ),
                "ethnic_group": _row_value(row, ["ethnic group", "ethnicity", "race"])
                if row
                else None,
            },
        )
        studies.setdefault(
            study_uid,
            {
                "study_instance_uid": study_uid,
                "collection_name_study": collection_name,
                "patient_id_study": patient_id,
                "study_date": _parse_date(
                    _row_value(row, ["study date", "date"]) if row else None
                ),
                "date_released": _parse_date(
                    _row_value(row, ["date released", "release date"]) if row else None
                ),
                "study_description": _row_value(
                    row, ["study description", "description"]
                )
                if row
                else None,
                "series_count": 0,
                "longitudinal_temporal_event_type": _row_value(
                    row, ["longitudinal temporal event type"]
                )
                if row
                else None,
                "longitudinal_temporal_offset_from_event": _row_value(
                    row, ["longitudinal temporal offset from event"]
                )
                if row
                else None,
            },
        )
        series.setdefault(
            series_uid,
            {
                "series_instance_uid": series_uid,
                "study_instance_uid_series": study_uid,
                "modality": _row_value(row, ["modality"]) if row else "NIFTI",
                "body_part_examined": _row_value(
                    row, ["body part examined", "bodypartexamined", "body part"]
                )
                if row
                else None,
                "protocol_name": _row_value(row, ["protocol name", "protocolname"])
                if use_series_metadata
                else None,
                "series_date": _parse_date(
                    _row_value(row, ["series date"]) if use_series_metadata else None
                ),
                "series_description": _row_value(
                    row, ["series description", "description"]
                )
                if use_series_metadata
                else fallback_series,
                "site": _row_value(row, ["site"]) if row else None,
                "manufacturer": _row_value(row, ["manufacturer"])
                if use_series_metadata
                else None,
                "manufacturer_model_name": _row_value(row, ["manufacturer model name"])
                if use_series_metadata
                else None,
                "software_versions": _row_value(row, ["software versions"])
                if use_series_metadata
                else None,
                "image_count": image_count,
                "max_submission_timestamp": None,
                "file_size": file_path.stat().st_size,
                "third_party_analysis": None,
            },
        )
        study_series.setdefault(study_uid, set()).add(series_uid)
        identities.append(
            FileIdentity(
                source_path=file_path,
                object_name="/".join([
                    collection_name,
                    patient_id,
                    study_uid,
                    series_uid,
                    sanitize_path_segment(file_path.name),
                ]),
                patient_id=patient_id,
                study_uid=study_uid,
                series_uid=series_uid,
            )
        )

    for study_uid, values in study_series.items():
        studies[study_uid]["series_count"] = len(values)

    collection = {
        "collection_name": collection_name,
        "type": "nifti",
        "description": description
        or _first_row_value(row_matches, ["description", "study description"]),
        "license_name": _first_row_value(row_matches, ["license name", "license_name"]),
        "license_uri": _first_row_value(row_matches, ["license uri", "license_uri"]),
        "data_description_uri": _first_row_value(
            row_matches, ["description uri", "collection uri", "collection_uri"]
        ),
        "remote": remote,
    }
    return (
        collection,
        list(patients.values()),
        list(studies.values()),
        list(series.values()),
        identities,
    )


def _insert_records(
    collection: dict[str, Any],
    patients: list[dict[str, Any]],
    studies: list[dict[str, Any]],
    series: list[dict[str, Any]],
) -> dict[str, int]:
    session = SessionLocal()
    try:
        _add_if_missing(session, Collection, "collection_name", collection)
        counts = {"patients": 0, "studies": 0, "series": 0}
        for patient in patients:
            counts["patients"] += int(
                _add_if_missing(session, Patient, "patient_id", patient)
            )
        for study in studies:
            counts["studies"] += int(
                _add_if_missing(session, Study, "study_instance_uid", study)
            )
        for item in series:
            counts["series"] += int(
                _add_if_missing(session, Series, "series_instance_uid", item)
            )
        session.commit()
        return counts
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


MODEL_FIELD_ALIASES = {
    Collection: {
        "name": "collection_name",
        "description_uri": "data_description_uri",
    },
    Patient: {
        "id": "patient_id",
        "sex": "patient_sex",
        "age": "patient_age",
    },
    Study: {
        "instance_uid": "study_instance_uid",
        "collection": "collection_name_study",
        "patient_id": "patient_id_study",
        "date": "study_date",
        "description": "study_description",
    },
    Series: {
        "instance_uid": "series_instance_uid",
        "study_instance_uid": "study_instance_uid_series",
        "body_part": "body_part_examined",
    },
}


def _to_model_fields(model, data: dict[str, Any]) -> dict[str, Any]:
    aliases = MODEL_FIELD_ALIASES.get(model, {})
    model_columns = set(model.__table__.columns.keys())
    normalized: dict[str, Any] = {}

    for key, value in data.items():
        column = aliases.get(key, key)
        if column in model_columns:
            normalized[column] = value

    return normalized


def _add_if_missing(session, model, key: str, data: dict[str, Any]) -> bool:
    model_data = _to_model_fields(model, data)
    if key not in model_data:
        raise KeyError(f"Missing key '{key}' for {model.__name__}")

    if not session.query(model).filter(getattr(model, key) == model_data[key]).first():
        session.add(model(**model_data))
        return True
    return False


def _raise_if_collection_exists(collection_name: str) -> None:
    session = SessionLocal()
    try:
        if (
            session
            .query(Collection)
            .filter(Collection.collection_name == collection_name)
            .first()
        ):
            raise ZipIngestionError(
                f"Collection '{collection_name}' already exists.",
                409,
            )
    finally:
        session.close()


def _safe_extract_zip(upload_file, target_root: Path) -> None:
    target_root.mkdir(parents=True, exist_ok=True)
    try:
        upload_file.file.seek(0)
        with zipfile.ZipFile(upload_file.file) as archive:
            _validate_zip_archive(archive, target_root)
            archive.extractall(target_root)
    except zipfile.BadZipFile as exc:
        raise ZipIngestionError("Malformed ZIP file.", 400) from exc


def _validate_zip_archive(archive: zipfile.ZipFile, target_root: Path) -> None:
    members = archive.infolist()
    if len(members) > MAX_ZIP_FILES:
        raise ZipIngestionError(
            f"ZIP contains too many files; maximum is {MAX_ZIP_FILES}.",
            413,
        )

    total_uncompressed_size = 0
    target_root_resolved = target_root.resolve()
    for member in members:
        _validate_zip_member(member, target_root_resolved)
        total_uncompressed_size += member.file_size
        if member.file_size > MAX_SINGLE_FILE_BYTES:
            raise ZipIngestionError(
                f"ZIP member '{member.filename}' is too large.",
                413,
            )
        if total_uncompressed_size > MAX_UNCOMPRESSED_BYTES:
            raise ZipIngestionError(
                "ZIP uncompressed size exceeds the configured limit.",
                413,
            )


def _validate_zip_member(member: zipfile.ZipInfo, target_root_resolved: Path) -> None:
    member_path = Path(member.filename)
    if member_path.is_absolute():
        raise ZipIngestionError("ZIP contains an absolute path.", 400)
    if _is_zip_symlink(member):
        raise ZipIngestionError("ZIP contains a symlink entry.", 400)

    destination = target_root_resolved / member.filename
    if not destination.resolve().is_relative_to(target_root_resolved):
        raise ZipIngestionError("ZIP contains an unsafe path.", 400)


def _is_zip_symlink(member: zipfile.ZipInfo) -> bool:
    unix_mode = member.external_attr >> 16
    return stat.S_ISLNK(unix_mode)


def _save_external_metadata_file(metadata_file, temp_root: Path) -> Path | None:
    if metadata_file is None:
        return None

    filename = Path(getattr(metadata_file, "filename", "") or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in METADATA_SUFFIXES:
        raise ZipIngestionError("metadata_file must be a .csv or .xlsx file.", 400)

    metadata_path = temp_root / f"external_metadata{suffix}"
    metadata_file.file.seek(0)
    with metadata_path.open("wb") as handle:
        while chunk := metadata_file.file.read(1024 * 1024):
            handle.write(chunk)
    return metadata_path


def _parse_column_mapping(
    column_mapping: str | dict[str, str] | None,
) -> dict[str, str]:
    if not column_mapping:
        return {}
    if isinstance(column_mapping, dict):
        return {
            _normalize_column_name(k): _normalize_column_name(v)
            for k, v in column_mapping.items()
        }
    try:
        parsed = json.loads(column_mapping)
    except json.JSONDecodeError as exc:
        raise ZipIngestionError("column_mapping must be valid JSON.", 400) from exc
    if not isinstance(parsed, dict):
        raise ZipIngestionError("column_mapping must be a JSON object.", 400)
    return {
        _normalize_column_name(k): _normalize_column_name(v) for k, v in parsed.items()
    }


def _looks_like_dicom(dataset: Any) -> bool:
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


def _dicom_str(dataset: Any, field: str, default: str | None = None) -> str | None:
    value = getattr(dataset, field, None)
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip()


def _fallback_sop_name(path: Path) -> str:
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
    return f"{sanitize_path_segment(path.stem)}_{digest}"


def _extract_age(value: Any) -> int:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else -1


def _parse_date(value: Any):
    if value is None or str(value).strip() == "":
        return None
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def _safe_int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {_normalize_column_name(key): value for key, value in row.items()}


def _apply_column_mapping(
    row: dict[str, Any], column_mapping: dict[str, str]
) -> dict[str, Any]:
    if not column_mapping:
        return row
    mapped = dict(row)
    for canonical_field, spreadsheet_header in column_mapping.items():
        canonical_key = _normalize_column_name(canonical_field)
        spreadsheet_key = _normalize_column_name(spreadsheet_header)
        if spreadsheet_key in row:
            mapped[canonical_key] = row[spreadsheet_key]
    return mapped


def _normalize_column_name(value: Any) -> str:
    text = str(value).strip().lower().replace("_", " ")
    return re.sub(r"\s+", " ", text)


def _candidate_rows_for_file(
    rows: list[dict[str, Any]], file_path: Path, root: Path | None
) -> list[dict[str, Any]]:
    targets = {
        _normalized_path(file_path.relative_to(root))
        if root and file_path.is_relative_to(root)
        else "",
        _normalized_path(file_path.name),
        _normalized_path(_nifti_stem(file_path.name)),
        _normalize_text(file_path.name),
        _normalize_text(_nifti_stem(file_path.name)),
    }
    exact_matches = [
        row
        for row in rows
        if any(
            _normalize_text(value) in targets or _normalized_path(value) in targets
            for value in row.values()
            if value is not None and not pd.isna(value)
        )
    ]
    if exact_matches:
        return exact_matches

    file_tokens = _text_tokens(_nifti_stem(file_path.name))
    if not file_tokens:
        return []

    best_score = 0
    best_rows: list[dict[str, Any]] = []
    for row in rows:
        score = _row_token_overlap_score(row, file_tokens)
        if score > best_score:
            best_score = score
            best_rows = [row]
        elif score == best_score and score > 0:
            best_rows.append(row)
    if best_score > 0:
        return best_rows
    return []


def _candidate_rows_for_patient(
    rows: list[dict[str, Any]], file_path: Path, root: Path | None
) -> list[dict[str, Any]]:
    patient_id = _patient_id_from_nifti_path(file_path, root)
    if not patient_id:
        return []
    normalized_patient_id = _normalized_identifier(patient_id)
    return [
        row
        for row in rows
        if any(
            _normalized_identifier(value) == normalized_patient_id
            for value in row.values()
            if value is not None and not pd.isna(value)
        )
    ]


def _candidate_rows_for_nifti_series(
    rows: list[dict[str, Any]],
    file_path: Path,
    allow_description_series_matching: bool = False,
) -> list[dict[str, Any]]:
    tokens = _text_tokens(_nifti_stem(file_path.name))
    if not tokens:
        return []

    if allow_description_series_matching:
        description_candidates = _candidate_rows_for_nifti_description(
            rows,
            tokens,
        )
        if description_candidates:
            return description_candidates

    candidates = []
    best_score = 0
    for row in rows:
        score = _row_token_overlap_score(row, tokens)
        if score > best_score:
            best_score = score
            candidates = [row]
        elif score == best_score and score > 0:
            candidates.append(row)
    return candidates


def _candidate_rows_for_nifti_description(
    rows: list[dict[str, Any]],
    tokens: set[str],
) -> list[dict[str, Any]]:
    candidates = []
    best_score = 0
    for row in rows:
        description_values = [
            _row_value(row, ["series description", "description"]),
            _row_value(row, ["protocol name", "protocolname"]),
        ]
        score = max(
            (len(tokens & _text_tokens(value)) for value in description_values if value),
            default=0,
        )
        if score > best_score:
            best_score = score
            candidates = [row]
        elif score == best_score and score > 0:
            candidates.append(row)
    return candidates


def _row_with_match_scope(row: dict[str, Any], scope: str) -> dict[str, Any]:
    scoped = dict(row)
    scoped["__match_scope"] = scope
    return scoped


def _patient_id_from_nifti_path(file_path: Path, root: Path | None) -> str | None:
    relative = (
        file_path.relative_to(root)
        if root and file_path.is_relative_to(root)
        else file_path
    )
    parts = relative.parts
    if len(parts) >= 3 and str(parts[-2]).lower().endswith(NIFTI_SUFFIXES):
        return parts[-3]
    if len(parts) >= 2:
        return parts[-2]

    match = re.match(
        r"((?:TCGA|BraTS|BRATS)[A-Za-z0-9-]*)[_-]", file_path.name, flags=re.IGNORECASE
    )
    if match:
        return match.group(1)
    return None


def _normalize_text(value: Any) -> str:
    text = str(value or "").replace("\\", "/").strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _text_tokens(value: Any) -> set[str]:
    return {token for token in _normalize_text(value).split() if token}


def _row_token_overlap_score(row: dict[str, Any], tokens: set[str]) -> int:
    best = 0
    for value in row.values():
        if value is None or pd.isna(value):
            continue
        value_tokens = _text_tokens(value)
        if not value_tokens:
            continue
        score = len(tokens & value_tokens)
        if score > best:
            best = score
    return best


def _normalized_identifier(value: Any) -> str:
    return str(value or "").strip().lower()


def _first_row_value(
    row_matches: dict[Path, dict[str, Any]], aliases: list[str]
) -> Any:
    for row in row_matches.values():
        value = _row_value(row, aliases)
        if value is not None:
            return value
    return None


def _normalized_path(value: Any) -> str:
    return str(value or "").replace("\\", "/").strip().lower()


def _nifti_stem(name: str) -> str:
    lowered = name.lower()
    if lowered.endswith(".nii.gz"):
        return name[:-7]
    if lowered.endswith(".nii"):
        return name[:-4]
    return Path(name).stem


def _nifti_image_count(path: Path) -> int:
    try:
        import SimpleITK as sitk

        image = sitk.ReadImage(str(path))
        size = image.GetSize()
        return int(size[2]) if len(size) >= 3 else 1
    except Exception:
        return 1


def _row_value(row: dict[str, Any] | None, aliases: list[str]) -> Any:
    if not row:
        return None
    for alias in aliases:
        value = row.get(_normalize_column_name(alias))
        if value is not None and not pd.isna(value) and str(value).strip() != "":
            return value
    return None


def _present_or_fallback(value: Any, fallback: str) -> Any:
    if value is None or str(value).strip() == "":
        return fallback
    return value


def _response(
    *,
    dataset_type: str,
    collection_name: str,
    files_discovered: int,
    files_uploaded: int,
    patients_inserted: int,
    studies_inserted: int,
    series_inserted: int,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "status_operation": "success",
        "collection_name": collection_name,
        "dataset_type": dataset_type,
        "files_discovered": files_discovered,
        "files_uploaded": files_uploaded,
        "patients_inserted": patients_inserted,
        "studies_inserted": studies_inserted,
        "series_inserted": series_inserted,
        "warnings": warnings,
        "error": None,
    }
