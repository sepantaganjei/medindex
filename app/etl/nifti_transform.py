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

# This function returns a dictionary of data of the collection we want to add
# Input
# - Raw data
# Output
# - data of the collection in dictionary format
def prepare_collection_data(raw_data):
    raw_df = pd.read_excel(raw_data)
    row = raw_df.iloc[0]

    clean_collection_data = {
        "name": safe_str(row.get("Project")),
        "description": safe_str(row.get("Description", "Missing")),
        "license_name": safe_str(row.get("License Name", "Missing")),
        "license_uri": safe_str(row.get("License URI", "Missing")),
        "description_uri": safe_str(row.get("Collection URI", "Missing")),
    }

    return clean_collection_data


# This function returns a dictionary of data of the patients we want to add
# We used a dictionary so as to avoid duplicated patients being added to the DB
# Input
# - Raw data
# Output
# - data of the patients in dictionary format. Each key is a different patient.
def prepare_patients_data(raw_data):
    raw_df = pd.read_excel(raw_data)
    patients = {}

    for _, row in raw_df.iterrows():
        patient_id = safe_str(row.get("Patient ID"))

        # age extraction
        match = re.search(r"0(\d+)", str(row.get("Patient Age", "")))
        age = int(match.group(1)) if match else -1

        if patient_id not in patients:
            patients[patient_id] = {
                "id": patient_id,
                "sex": safe_str(row.get("Patient Sex", "Missing")),
                "age": age,
                "ethnic_group": safe_str(row.get("Ethnic Group", "Missing")),
            }

    return list(patients.values())


# This function returns a dictionary of data of the studies we want to add
# We used a dictionary so as to avoid duplicated studies being added to the DB
# Input
# - Raw data
# Output
# - data of the studies in dictionary format. Each key is a different study.
def prepare_studies_data(raw_data):
    raw_df = pd.read_excel(raw_data)
    studies = {}

    for _, row in raw_df.iterrows():
        study_id = safe_str(row.get("Study Instance UID"))

        if study_id not in studies:
            studies[study_id] = {
                "instance_uid": study_id,
                "collection": safe_str(row.get("Project", "Missing")),
                "date": safe_date(
                    row.get("Study Date")
                ),  # keep safe_str unless you truly parse dates
                "date_released": safe_date(row.get("Date Released")),
                "description": safe_str(row.get("Study Description", "Missing")),
                "series_count": safe_int(row.get("Series Number")),
                "patient_id": safe_str(row.get("Patient ID", "Missing")),
                "LongitudinalTemporalEventType": safe_str(
                    row.get("Longitudinal Temporal Event Type", "Missing")
                ),
                "LongitudinalTemporalOffsetFromEvent": safe_int(
                    row.get("Longitudinal Temporal Offset From Event")
                ),
            }

    return list(studies.values())


# This function returns a dictionary of data of the series we want to add
# We used a dictionary so as to avoid duplicated series being added to the DB
# Input
# - Raw data
# Output
# - data of the series in dictionary format. Each key is a different series.
def prepare_series_data(raw_df):
    series_list = {}

    for _, row in raw_df.iterrows():
        instance_uid = safe_str(row.get("Series Instance UID"))

        if instance_uid not in series_list:
            series_list[instance_uid] = {
                "instance_uid": instance_uid,
                "study_instance_uid": safe_str(
                    row.get("Study Instance UID", "Missing")
                ),
                "modality": safe_str(row.get("Modality", "Missing")),
                "body_part": safe_str(row.get("Body Part Examined", "Missing")),
                "protocol_name": safe_str(row.get("Protocol Name", "Missing")),
                "series_date": safe_date(row.get("Series Date")),
                "series_description": safe_str(
                    row.get("Series Description", "Missing")
                ),
                "site": safe_str(row.get("Site", "Missing")),
                "manufacturer": safe_str(row.get("Manufacturer", "Missing")),
                "manufacturer_model_name": safe_str(
                    row.get("Manufacturer Model Name", "Missing")
                ),
                "software_versions": safe_str(row.get("Software Versions", "Missing")),
                "image_count": safe_int(row.get("Image Count")),
                "max_submission_timestamp": safe_time(
                    row.get("Max Submission Timestamp")
                ),
                "file_size": safe_int(row.get("File Size")),
                "third_party_analysis": safe_bool(row.get("Third Party Analysis")),
            }

    return list(series_list.values())
