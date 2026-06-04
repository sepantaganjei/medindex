# This file handles the transformation of metadata coming from NIFTI datasets

import pandas as pd
import re

# Safe helpers in case of missing data


# Standardizes missing integers
def safe_int(x):
    if pd.isna(x):
        return None
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


# Standardizes missing strings
def safe_str(x, default="Missing"):
    if x is None or pd.isna(x):
        return default
    return str(x)


# Standardizes missing and non missing dates
def safe_date(x):
    if pd.isna(x):
        return None
    try:
        return pd.to_datetime(x).date()
    except (TypeError, ValueError):
        return None


# Standardizes missing and non missing timestamps
def safe_time(x):
    if pd.isna(x):
        return None
    try:
        return pd.to_datetime(x).time()
    except (TypeError, ValueError):
        return None


# Standardizes missing and non missing boolean values
def safe_bool(x):
    if pd.isna(x):
        return None
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return bool(x)

    x = str(x).strip().lower()
    if x in {"true", "t", "yes", "y", "1"}:
        return True
    if x in {"false", "f", "no", "n", "0"}:
        return False

    return None


# ==========================
# Data preparation functions
# ==========================


def _find_correspoding_columns_in(table, mapping):
    new_fields = {}
    for field, candidate_columns in mapping.items():
        for candidate_column in candidate_columns:
            if candidate_column in table.columns:
                new_fields[field] = candidate_column
                break

    return new_fields


# Data preparation for collection storage

collection_mappings = {
    "collection_name": ["project", "collection name", "collection", "collectionname"],
    "license_name": ["license name", "license_name"],
    "license_uri": ["license uri", "license_uri"],
    "data_description_uri": [
        "description uri",
        "description_uri",
        "collection_uri",
        "collection uri",
    ],
}


def prepare_collection_data(tabular_file, description):

    clean_collection_data = {
        "collection_name": None,
        "description": description,
        "license_name": None,
        "license_uri": None,
        "data_description_uri": None,
    }

    try:
        # load file
        if tabular_file.endswith(".csv"):
            df = pd.read_csv(tabular_file)
        elif tabular_file.endswith(".xlsx"):
            df = pd.read_excel(tabular_file, engine="openpyxl")
        else:
            return clean_collection_data

        # skip empty files
        if df.empty:
            return clean_collection_data

        # normalize column names
        df.columns = df.columns.str.strip().str.lower()

        row = df.iloc[0]

        # find matching columns once
        matched_columns = _find_correspoding_columns_in(df, collection_mappings)

        # fill fields
        for field in clean_collection_data:
            if not clean_collection_data[field] and field in matched_columns:
                column_name = matched_columns[field]
                clean_collection_data[field] = safe_str(row.get(column_name))

    except Exception as e:
        print(f"Skipping {tabular_file}: {e}")

    # fallback values
    for field in clean_collection_data:
        if not clean_collection_data[field]:
            clean_collection_data[field] = "Missing"

    return clean_collection_data


# Data preparation for patients storage


def extract_age(value):
    if value is None:
        return -1
    match = re.search(r"\d+", str(value))
    return int(match.group(0)) if match else -1


patient_mappings = {
    "patient_id": ["patient id", "patient", "patientid", "patient_id"],
    "patient_sex": [
        "patient sex",
        "patient_sex",
        "sex",
        "gender",
        "patient gender",
        "patientsex",
    ],
    "patient_age": ["patient age", "age", "patient_age"],
    "ethnic_group": ["ethnic group", "ethnicity", "race"],
}


def prepare_patients_data(tabular_files):
    if tabular_files.endswith(".csv"):
        df = pd.read_csv(tabular_files)
    else:
        df = pd.read_excel(tabular_files, engine="openpyxl")

    df.columns = df.columns.str.strip().str.lower()

    patients = {}

    matched_columns = _find_correspoding_columns_in(df, patient_mappings)

    for _, row in df.iterrows():
        patient = {
            "patient_id": None,
            "patient_sex": None,
            "patient_age": None,
            "ethnic_group": None,
        }

        for field in patient:
            if field in matched_columns:
                patient[field] = safe_str(row.get(matched_columns[field]))

        patient_id = patient["patient_id"]

        # initialize patient if needed
        if patient_id not in patients:
            patients[patient_id] = {
                "patient_id": patient_id,
                "patient_sex": "Missing",
                "patient_age": -1,
                "ethnic_group": "Missing",
            }

        # merge logic
        if patient["patient_sex"] and patients[patient_id]["patient_sex"] == "Missing":
            patients[patient_id]["patient_sex"] = patient["patient_sex"]

        if (
            patient["ethnic_group"]
            and patients[patient_id]["ethnic_group"] == "Missing"
        ):
            patients[patient_id]["ethnic_group"] = patient["ethnic_group"]

        age = extract_age(patient["patient_age"])
        if patients[patient_id]["patient_age"] == -1 and age != -1:
            patients[patient_id]["patient_age"] = age

    return list(patients.values())


# Data preparation for study storage

study_mappings = {
    "study_instance_uid": ["study instance uid", "study uid", "studyinstanceuid"],
    "collection_name_study": ["project", "collection", "study project"],
    "study_date": ["study date", "date"],
    "date_released": ["date released", "release date"],
    "study_description": ["study description", "description"],
    "series_count": ["series number", "series count"],
    "patient_id_study": ["patient id", "patient"],
    "longitudinal_temporal_event_type": ["longitudinal temporal event type"],
    "longitudinal_temporal_offset_from_event": [
        "longitudinal temporal offset from event"
    ],
}


def prepare_studies_data(tabular_files):

    if tabular_files.endswith(".csv"):
        df = pd.read_csv(tabular_files)
    else:
        df = pd.read_excel(tabular_files, engine="openpyxl")

    df.columns = df.columns.str.strip().str.lower()

    studies = {}

    matched_columns = _find_correspoding_columns_in(df, study_mappings)

    for _, row in df.iterrows():
        study = {
            "study_instance_uid": None,
            "collection_name_study": None,
            "study_date": None,
            "date_released": None,
            "study_description": None,
            "series_count": None,
            "patient_id_study": None,
            "longitudinal_temporal_event_type": None,
            "longitudinal_temporal_offset_from_event": None,
        }

        for field in study:
            if field in matched_columns:
                study[field] = safe_str(row.get(matched_columns[field]))

        study_id = study["study_instance_uid"]

        if not study_id:
            continue

        # initialize study
        if study_id not in studies:
            studies[study_id] = {
                "study_instance_uid": study_id,
                "collection_name_study": "Missing",
                "study_date": None,
                "date_released": None,
                "study_description": "Missing",
                "series_count": -1,
                "patient_id_study": "Missing",
                "longitudinal_temporal_event_type": "Missing",
                "longitudinal_temporal_offset_from_event": -99999,
            }

        # merge logic (same philosophy as patients)

        if (
            study["collection_name_study"]
            and studies[study_id]["collection_name_study"] == "Missing"
        ):
            studies[study_id]["collection_name_study"] = study["collection_name_study"]

        if (
            study["study_description"]
            and studies[study_id]["study_description"] == "Missing"
        ):
            studies[study_id]["study_description"] = study["study_description"]

        if (
            study["patient_id_study"]
            and studies[study_id]["patient_id_study"] == "Missing"
        ):
            studies[study_id]["patient_id_study"] = study["patient_id_study"]

        # dates (only fill if missing)
        if not studies[study_id]["study_date"]:
            studies[study_id]["study_date"] = safe_date(study["study_date"])

        if not studies[study_id]["date_released"]:
            studies[study_id]["date_released"] = safe_date(study["date_released"])

        # numeric fields
        series_count = safe_int(study["series_count"])
        if studies[study_id]["series_count"] == -1 and series_count is not None:
            studies[study_id]["series_count"] = series_count

        event_offset = safe_int(study["longitudinal_temporal_offset_from_event"])
        if (
            studies[study_id]["longitudinal_temporal_offset_from_event"] == -99999
            and event_offset is not None
        ):
            studies[study_id]["longitudinal_temporal_offset_from_event"] = event_offset

        # categorical
        if (
            study["longitudinal_temporal_event_type"]
            and studies[study_id]["longitudinal_temporal_event_type"] == "Missing"
        ):
            studies[study_id]["longitudinal_temporal_event_type"] = study[
                "longitudinal_temporal_event_type"
            ]

    return list(studies.values())


# Data preparation for series storage

series_mappings = {
    "series_instance_uid": ["series instance uid", "seriesinstanceuid", "series uid"],
    "study_instance_uid_series": ["study instance uid", "studyinstanceuid"],
    "modality": ["modality"],
    "body_part_examined": ["body part examined", "bodypartexamined"],
    "protocol_name": ["protocol name", "protocolname"],
    "series_date": ["series date"],
    "series_description": ["series description", "description"],
    "site": ["site", "healthcare facility", "healthcarefacility"],
    "manufacturer": ["manufacturer"],
    "manufacturer_model_name": ["manufacturer model name"],
    "software_versions": ["software versions"],
    "image_count": ["image count", "images"],
    "max_submission_timestamp": ["max submission timestamp"],
    "file_size": ["file size"],
    "third_party_analysis": ["third party analysis"],
}


def prepare_series_data(tabular_file):
    if tabular_file.endswith(".csv"):
        df = pd.read_csv(tabular_file)
    else:
        df = pd.read_excel(tabular_file, engine="openpyxl")

    series_list = {}

    df.columns = df.columns.str.strip().str.lower()

    matched_columns = _find_correspoding_columns_in(df, series_mappings)

    for _, row in df.iterrows():
        series = {}

        for field in series_mappings:
            if field in matched_columns:
                series[field] = safe_str(row.get(matched_columns[field]))
            else:
                series[field] = None

        instance_uid = series["series_instance_uid"]

        if not instance_uid or instance_uid == "Missing":
            continue

        if instance_uid not in series_list:
            series_list[instance_uid] = {
                "series_instance_uid": instance_uid,
                "study_instance_uid_series": "Missing",
                "modality": "Missing",
                "body_part_examined": "Missing",
                "protocol_name": "Missing",
                "series_date": None,
                "series_description": "Missing",
                "site": "Missing",
                "manufacturer": "Missing",
                "manufacturer_model_name": "Missing",
                "software_versions": "Missing",
                "image_count": -1,
                "max_submission_timestamp": None,
                "file_size": -1,
                "third_party_analysis": None,
            }

        s = series_list[instance_uid]

        # merge logic (same pattern as patients)

        if (
            series.get("study_instance_uid_series")
            and s["study_instance_uid_series"] == "Missing"
        ):
            s["study_instance_uid_series"] = series["study_instance_uid_series"]

        if series.get("modality") and s["modality"] == "Missing":
            s["modality"] = series["modality"]

        if series.get("body_part_examined") and s["body_part_examined"] == "Missing":
            s["body_part_examined"] = series["body_part_examined"]

        if series.get("protocol_name") and s["protocol_name"] == "Missing":
            s["protocol_name"] = series["protocol_name"]

        if not s["series_date"]:
            s["series_date"] = safe_date(series.get("series_date"))

        if series.get("series_description") and s["series_description"] == "Missing":
            s["series_description"] = series["series_description"]

        if series.get("site") and s["site"] == "Missing":
            s["site"] = series["site"]

        if series.get("manufacturer") and s["manufacturer"] == "Missing":
            s["manufacturer"] = series["manufacturer"]

        if (
            series.get("manufacturer_model_name")
            and s["manufacturer_model_name"] == "Missing"
        ):
            s["manufacturer_model_name"] = series["manufacturer_model_name"]

        if series.get("software_versions") and s["software_versions"] == "Missing":
            s["software_versions"] = series["software_versions"]

        img_count = safe_int(series.get("image_count"))
        if s["image_count"] == -1 and img_count is not None:
            s["image_count"] = img_count

        if not s["max_submission_timestamp"]:
            s["max_submission_timestamp"] = safe_time(
                series.get("max_submission_timestamp")
            )

        file_size = safe_int(series.get("file_size"))
        if s["file_size"] == -1 and file_size is not None:
            s["file_size"] = file_size

        if s["third_party_analysis"] is None:
            s["third_party_analysis"] = safe_bool(series.get("third_party_analysis"))

    return list(series_list.values())
