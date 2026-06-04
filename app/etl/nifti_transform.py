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
    "collectionName": ["project", "collection name", "collection"],
    "LicenseName": ["license name", "license_name"],
    "LicenseURI": ["license uri", "license_uri"],
    "DataDescriptionURI": [
        "description uri",
        "description_uri",
        "collection_uri",
        "collection uri",
    ],
}


def prepare_collection_data(tabular_file, description):

    clean_collection_data = {
        "collectionName": None,
        "description": description,
        "LicenseName": None,
        "LicenseURI": None,
        "DataDescriptionURI": None,
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
    "PatientID": ["patient id", "patient", "patientid", "patient_id"],
    "PatientSex": [
        "patient sex",
        "patient_sex",
        "sex",
        "gender",
        "patient gender",
        "patientsex",
    ],
    "PatientAge": ["patient age", "age", "patient_age"],
    "EthnicGroup": ["ethnic group", "ethnicity", "race"],
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
            "PatientID": None,
            "PatientSex": None,
            "PatientAge": None,
            "EthnicGroup": None,
        }

        for field in patient:
            if field in matched_columns:
                patient[field] = safe_str(row.get(matched_columns[field]))

        patient_id = patient["PatientID"]

        # initialize patient if needed
        if patient_id not in patients:
            patients[patient_id] = {
                "PatientID": patient_id,
                "PatientSex": "Missing",
                "PatientAge": -1,
                "EthnicGroup": "Missing",
            }

        # merge logic
        if patient["PatientSex"] and patients[patient_id]["PatientSex"] == "Missing":
            patients[patient_id]["PatientSex"] = patient["PatientSex"]

        if patient["EthnicGroup"] and patients[patient_id]["EthnicGroup"] == "Missing":
            patients[patient_id]["EthnicGroup"] = patient["EthnicGroup"]

        age = extract_age(patient["PatientAge"])
        if patients[patient_id]["PatientAge"] == -1 and age != -1:
            patients[patient_id]["PatientAge"] = age

    return list(patients.values())


# Data preparation for study storage

study_mappings = {
    "StudyInstanceUID": ["study instance uid", "study uid", "studyinstanceuid"],
    "Collection": ["project", "collection", "study project"],
    "StudyDate": ["study date", "date"],
    "DateReleased": ["date released", "release date"],
    "StudyDescription": ["study description", "description"],
    "SeriesCount": ["series number", "series count"],
    "PatientID": ["patient id", "patient"],
    "LongitudinalTemporalEventType": ["longitudinal temporal event type"],
    "LongitudinalTemporalOffsetFromEvent": ["longitudinal temporal offset from event"],
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
            "StudyInstanceUID": None,
            "Collection": None,
            "StudyDate": None,
            "DateReleased": None,
            "StudyDescription": None,
            "SeriesCount": None,
            "PatientID": None,
            "LongitudinalTemporalEventType": None,
            "LongitudinalTemporalOffsetFromEvent": None,
        }

        for field in study:
            if field in matched_columns:
                study[field] = safe_str(row.get(matched_columns[field]))

        study_id = study["instance_uid"]

        if not study_id:
            continue

        # initialize study
        if study_id not in studies:
            studies[study_id] = {
                "StudyInstanceUID": study_id,
                "Collection": "Missing",
                "StudyDate": None,
                "DateReleased": None,
                "StudyDescription": "Missing",
                "SeriesCount": -1,
                "PatientID": "Missing",
                "LongitudinalTemporalEventType": "Missing",
                "LongitudinalTemporalOffsetFromEvent": -99999,
            }

        # merge logic (same philosophy as patients)

        if study["Collection"] and studies[study_id]["Collection"] == "Missing":
            studies[study_id]["Collection"] = study["Collection"]

        if (
            study["StudyDescription"]
            and studies[study_id]["StudyDescription"] == "Missing"
        ):
            studies[study_id]["StudyDescription"] = study["StudyDescription"]

        if study["PatientID"] and studies[study_id]["PatientID"] == "Missing":
            studies[study_id]["PatientID"] = study["PatientID"]

        # dates (only fill if missing)
        if not studies[study_id]["StudyDate"]:
            studies[study_id]["StudyDate"] = safe_date(study["StudyDate"])

        if not studies[study_id]["DateReleased"]:
            studies[study_id]["DateReleased"] = safe_date(study["DateReleased"])

        # numeric fields
        series_count = safe_int(study["SeriesCount"])
        if studies[study_id]["SeriesCount"] == -1 and series_count is not None:
            studies[study_id]["SeriesCount"] = series_count

        event_offset = safe_int(study["LongitudinalTemporalOffsetFromEvent"])
        if (
            studies[study_id]["LongitudinalTemporalOffsetFromEvent"] == -99999
            and event_offset is not None
        ):
            studies[study_id]["LongitudinalTemporalOffsetFromEvent"] = event_offset

        # categorical
        if (
            study["LongitudinalTemporalEventType"]
            and studies[study_id]["LongitudinalTemporalEventType"] == "Missing"
        ):
            studies[study_id]["LongitudinalTemporalEventType"] = study[
                "LongitudinalTemporalEventType"
            ]

    return list(studies.values())


# Data preparation for series storage

series_mappings = {
    "SeriesInstanceUID": ["series instance uid", "seriesinstanceuid", "series uid"],
    "StudyInstanceUID": ["study instance uid", "studyinstanceuid"],
    "Modality": ["modality"],
    "BodyPartExamined": ["body part examined", "bodypartexamined"],
    "ProtocolName": ["protocol name", "protocolname"],
    "SeriesDate": ["series date"],
    "SeriesDescription": ["series description", "description"],
    "Site": ["site", "healthcare facility", "healthcarefacility"],
    "Manufacturer": ["manufacturer"],
    "ManufacturerModelName": ["manufacturer model name"],
    "SoftwareVersions": ["software versions"],
    "ImageCount": ["image count", "images"],
    "MaxSubmissionTimestamp": ["max submission timestamp"],
    "FileSize": ["file size"],
    "ThirdPartyAnalysis": ["third party analysis"],
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

        instance_uid = series["SeriesInstanceUID"]

        if not instance_uid or instance_uid == "Missing":
            continue

        if instance_uid not in series_list:
            series_list[instance_uid] = {
                "SeriesInstanceUID": instance_uid,
                "StudyInstanceUID": "Missing",
                "Modality": "Missing",
                "BodyPartExamined": "Missing",
                "ProtocolName": "Missing",
                "SeriesDate": None,
                "SeriesDescription": "Missing",
                "Site": "Missing",
                "Manufacturer": "Missing",
                "ManufacturerModelName": "Missing",
                "SoftwareVersions": "Missing",
                "ImageCount": -1,
                "MaxSubmissionTimestamp": None,
                "FileSize": -1,
                "ThirdPartyAnalysis": None,
            }

        s = series_list[instance_uid]

        # merge logic (same pattern as patients)

        if series.get("StudyInstanceUID") and s["StudyInstanceUID"] == "Missing":
            s["StudyInstanceUID"] = series["StudyInstanceUID"]

        if series.get("Modality") and s["Modality"] == "Missing":
            s["Modality"] = series["Modality"]

        if series.get("BodyPartExamined") and s["BodyPartExamined"] == "Missing":
            s["BodyPartExamined"] = series["BodyPartExamined"]

        if series.get("ProtocolName") and s["ProtocolName"] == "Missing":
            s["ProtocolName"] = series["ProtocolName"]

        if not s["SeriesDate"]:
            s["SeriesDate"] = safe_date(series.get("SeriesDate"))

        if series.get("SeriesDescription") and s["SeriesDescription"] == "Missing":
            s["SeriesDescription"] = series["SeriesDescription"]

        if series.get("Site") and s["Site"] == "Missing":
            s["Site"] = series["Site"]

        if series.get("Manufacturer") and s["Manufacturer"] == "Missing":
            s["Manufacturer"] = series["Manufacturer"]

        if (
            series.get("ManufacturerModelName")
            and s["ManufacturerModelName"] == "Missing"
        ):
            s["ManufacturerModelName"] = series["ManufacturerModelName"]

        if series.get("SoftwareVersions") and s["SoftwareVersions"] == "Missing":
            s["SoftwareVersions"] = series["SoftwareVersions"]

        img_count = safe_int(series.get("ImageCount"))
        if s["ImageCount"] == -1 and img_count is not None:
            s["ImageCount"] = img_count

        if not s["MaxSubmissionTimestamp"]:
            s["MaxSubmissionTimestamp"] = safe_time(
                series.get("MaxSubmissionTimestamp")
            )

        file_size = safe_int(series.get("FileSize"))
        if s["FileSize"] == -1 and file_size is not None:
            s["FileSize"] = file_size

        if s["ThirdPartyAnalysis"] is None:
            s["ThirdPartyAnalysis"] = safe_bool(series.get("ThirdPartyAnalysis"))

    return list(series_list.values())
