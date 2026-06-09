import pandas as pd
import re
from html import unescape
from bs4 import BeautifulSoup

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
def _clean_text(text: str) -> str:

    # Decode HTML entities (&rsquo; -> ', etc.)
    text = unescape(text)

    # Remove HTML tags
    soup = BeautifulSoup(text, "html.parser")
    cleaned = soup.get_text(separator=" ")

    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


# This function returns a dictionary of data of the collection we want to add
# Input
# - Raw data
# Output
# - data of the collection in dictionary format
def prepare_collection_data(raw_json_dict_data, _, remote):
    collection_json = raw_json_dict_data["collection"][0]
    series_json = raw_json_dict_data["series"]
    print(f"Name is ok: {collection_json.get('collectionName')}")

    clean_collection_data = {
        "collection_name": safe_str(collection_json.get("collectionName")),
        "type": "dicom",
        "description": _clean_text(safe_str(collection_json.get("description"))),
        "license_name": safe_str(series_json[0]["LicenseName"]),
        "license_uri": safe_str(series_json[0]["LicenseURI"]),
        "data_description_uri": safe_str(series_json[0]["DataDescriptionURI"]),
        "remote": remote,
    }
    print("Collection data has been cleaned")
    return clean_collection_data


# This function returns a dictionary of data of the patients we want to add
# We used a dictionary so as to avoid duplicated patients being added to the DB
# Input
# - Raw data
# Output
# - data of the patients in dictionary format. Each key is a different patient.
def prepare_patients_data(raw_json_dict_data):
    print(raw_json_dict_data.keys())

    list_of_patients = raw_json_dict_data["patients"]
    list_of_series = raw_json_dict_data["series"]

    patients = {}

    for patient in list_of_patients:
        patient_id = safe_str(patient.get("PatientId"))

        if patient_id not in patients:
            # filter related series for this patient
            patient_series = [
                s for s in list_of_series if s.get("PatientID") == patient_id
            ]

            # SEX
            sex = (
                safe_str(patient_series[0].get("PatientSex"))
                if patient_series
                else "Missing"
            )

            # AGE
            age_raw = (
                patient_series[0].get("PatientAge")
                if patient_series and patient_series[0].get("PatientAge")
                else None
            )

            if age_raw:
                match = re.search(r"(\d+)", str(age_raw))
                age = int(match.group(1)) if match else -1
            else:
                age = -1

            # ETHNIC GROUP (from patient-level data)
            ethnic_group = safe_str(patient.get("EthnicGroup", "Missing"))

            patients[patient_id] = {
                "patient_id": patient_id,
                "patient_sex": sex,
                "patient_age": age,
                "ethnic_group": ethnic_group,
            }

    return list(patients.values())


# This function returns a dictionary of data of the studies we want to add
# We used a dictionary so as to avoid duplicated studies being added to the DB
# Input
# - Raw data
# Output
# - data of the studies in dictionary format. Each key is a different study.
def prepare_studies_data(raw_json_dict_data):
    studies_df = pd.DataFrame(raw_json_dict_data["studies"])
    series_df = pd.DataFrame(raw_json_dict_data["series"])

    studies = {}

    for _, row in studies_df.iterrows():
        study_uid = row.get("StudyInstanceUID")

        # safely get DateReleased from series_df
        match = series_df.loc[
            series_df["StudyInstanceUID"] == study_uid, "DateReleased"
        ].dropna()

        date_released = match.iloc[0] if not match.empty else None

        studies[study_uid] = {
            "study_instance_uid": study_uid,
            "collection_name_study": safe_str(row.get("Collection", "Missing")),
            "study_date": safe_date(row.get("StudyDate")),
            "date_released": safe_date(date_released),
            "study_description": safe_str(row.get("StudyDescription", "Missing")),
            "series_count": safe_int(row.get("SeriesCount")),
            "patient_id_study": safe_str(row.get("PatientID", "Missing")),
            "longitudinal_temporal_event_type": safe_str(
                row.get("LongitudinalTemporalEventType", "Missing")
            ),
            "longitudinal_temporal_offset_from_event": safe_int(
                row.get("LongitudinalTemporalOffsetFromEvent")
            ),
        }

    return list(studies.values())


# This function returns a dictionary of data of the series we want to add
# We used a dictionary so as to avoid duplicated series being added to the DB
# Input
# - Raw data
# Output
# - data of the series in dictionary format. Each key is a different series.
def prepare_series_data(raw_json_dict_data):
    print(raw_json_dict_data.keys())
    list_of_series = raw_json_dict_data["series"]
    series_list = {}
    for series in list_of_series:
        instance_uid = safe_str(series["SeriesInstanceUID"])

        if instance_uid not in series_list:
            series_list[instance_uid] = {
                "series_instance_uid": instance_uid,
                "study_instance_uid_series": safe_str(
                    series.get("StudyInstanceUID", "Missing")
                ),
                "modality": safe_str(series.get("Modality", "Missing")),
                "body_part_examined": safe_str(
                    series.get("BodyPartExamined", "Missing")
                ),
                "protocol_name": safe_str(series.get("ProtocolName", "Missing")),
                "series_date": safe_date(series.get("StudyDate")),
                "series_description": safe_str(
                    series.get("SeriesDescription", "Missing")
                ),
                "site": safe_str(series.get("Site", "Missing")),
                "manufacturer": safe_str(series.get("Manufacturer", "Missing")),
                "manufacturer_model_name": safe_str(
                    series.get("ManufacturerModelName", "Missing")
                ),
                "software_versions": safe_str(
                    series.get("SoftwareVersions", "Missing")
                ),
                "image_count": safe_int(series.get("ImageCount")),
                "max_submission_timestamp": safe_time(
                    series.get("MaxSubmissionTimestamp")
                ),
                "file_size": safe_int(series.get("FileSize")),
                "third_party_analysis": safe_bool(series.get("ThirdPartyAnalysis")),
            }

    return list(series_list.values())
