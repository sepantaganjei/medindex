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
def prepare_collection_data(raw_json_dict_data, _):
    collection_json = raw_json_dict_data["collection"][0]
    series_json = raw_json_dict_data["series"]

    clean_collection_data = {
        "collectionName": safe_str(collection_json.get("collectionName")),
        "description": _clean_text(safe_str(collection_json.get("description"))),
        "LicenseName": safe_str(series_json[0]["LicenseName"]),
        "LicenseURI": safe_str(series_json[0]["LicenseURI"]),
        "DataDescriptionURI": safe_str(series_json[0]["DataDescriptionURI"]),
    }
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
        patient_id = safe_str(patient.get("PatientID"))

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
                "PatientID": patient_id,
                "PatientSex": sex,
                "PatientAge": age,
                "EthnicGroup": ethnic_group,
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
            "StudyInstanceUID": study_uid,
            "Collection": safe_str(row.get("Collection", "Missing")),
            "StudyDate": safe_date(row.get("StudyDate")),
            "DateReleased": safe_date(date_released),
            "StudyDescription": safe_str(row.get("StudyDescription", "Missing")),
            "SeriesCount": safe_int(row.get("SeriesCount")),
            "PatientID": safe_str(row.get("PatientID", "Missing")),
            "LongitudinalTemporalEventType": safe_str(
                row.get("LongitudinalTemporalEventType", "Missing")
            ),
            "LongitudinalTemporalOffsetFromEvent": safe_int(
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
                "SeriesInstanceUID": instance_uid,
                "StudyInstanceUID": safe_str(series.get("StudyInstanceUID", "Missing")),
                "Modality": safe_str(series.get("Modality", "Missing")),
                "BodyPartExamined": safe_str(series.get("BodyPartExamined", "Missing")),
                "ProtocolName": safe_str(series.get("ProtocolName", "Missing")),
                "SeriesDate": safe_date(series.get("StudyDate")),
                "SeriesDescription": safe_str(
                    series.get("SeriesDescription", "Missing")
                ),
                "Site": safe_str(series.get("Site", "Missing")),
                "Manufacturer": safe_str(series.get("Manufacturer", "Missing")),
                "ManufacturerModelName": safe_str(
                    series.get("ManufacturerModelName", "Missing")
                ),
                "SoftwareVersions": safe_str(series.get("SoftwareVersions", "Missing")),
                "ImageCount": safe_int(series.get("ImageCount")),
                "MaxSubmissionTimestamp": safe_time(
                    series.get("MaxSubmissionTimestamp")
                ),
                "FileSize": safe_int(series.get("FileSize")),
                "ThirdPartyAnalysis": safe_bool(series.get("ThirdPartyAnalysis")),
            }

    return list(series_list.values())
