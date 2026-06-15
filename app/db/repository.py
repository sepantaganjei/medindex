# This is where ALL SQL queries live.

# These are the base models that we'll use to instantiate new objects.
from app.db.models import Collection
from app.db.models import Study
from app.db.models import Patient
from app.db.models import Series
from app.db.models import Extraction
from app.db.models import Roi
from app.db.models import FieldMapping
from app.db.models import ValueMapping
from app.db.database import SessionLocal
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import inspect
import requests
import re

_VALUE_MAPPINGS_AVAILABLE = None

# Attribute mappings for metadata uploaded via Zip file
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

# Name mapping for extracted features: from pyradiomics name to internal data model name
RADIOMICS_FEATURE_MAPPING_KEYS = {
    "original_ngtdm_Busyness": "NGTDM Busyness",
    "original_ngtdm_Contrast": "NGTDM Contrast",
    "original_ngtdm_Coarseness": "NGTDM Coarseness",
    "original_glszm_ZoneEntropy": "GLSZM Zone Entropy",
    "original_glrlm_ShortRunEmphasis": "GLRLM Short Run Emphasis",
    "original_glcm_Correlation": "GLCM Correlation",
    "original_glcm_Idm": "GLCM Homogeneity",
    "original_firstorder_Mean": "ROI Mean",
    "original_firstorder_StandardDeviation": "ROI Standard Deviation",
}


# Check on json response
def get_json_or_empty(response):
    response.raise_for_status()

    if not response.text.strip():
        return []

    return response.json()


# Check existence of a value mapping
def value_mappings_available(session):
    global _VALUE_MAPPINGS_AVAILABLE

    if _VALUE_MAPPINGS_AVAILABLE is None:
        _VALUE_MAPPINGS_AVAILABLE = inspect(session.bind).has_table("value_mappings")

    return _VALUE_MAPPINGS_AVAILABLE


# Get mapping for the name of the extracted feature
def get_radiomics_feature_mapping_key(feature_name):
    return RADIOMICS_FEATURE_MAPPING_KEYS.get(feature_name, feature_name)


# Get mapping for the names of the attribtues coming form a dataset uploaded via Zip file
def _to_model_fields(model, data: dict) -> dict:
    aliases = MODEL_FIELD_ALIASES.get(model, {})
    model_columns = set(model.__table__.columns.keys())
    normalized = {}

    for key, value in data.items():
        column = aliases.get(key, key)
        if column in model_columns:
            normalized[column] = value

    return normalized


# Fallback in case collection name is missing
def _add_if_missing(session, model, key: str, data: dict) -> bool:
    model_data = _to_model_fields(model, data)
    if key not in model_data:
        raise KeyError(f"Missing key '{key}' for {model.__name__}")

    if not session.query(model).filter(getattr(model, key) == model_data[key]).first():
        session.add(model(**model_data))
        return True
    return False


# Check existence of collection
def collection_exists(collection_name: str) -> bool:
    session = SessionLocal()
    try:
        return (
            session
            .query(Collection)
            .filter(Collection.collection_name == collection_name)
            .first()
            is not None
        )
    finally:
        session.close()


# Actual insertion into the relational model of the set of metadata associated with a collection
def _insert_dataset_records(
    session,
    collection: dict,
    patients: list[dict],
    studies: list[dict],
    series: list[dict],
) -> dict[str, int]:
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

    return counts


# Main fuction for storage of a dataset uploaded locally
def insert_dataset_records(
    collection: dict,
    patients: list[dict],
    studies: list[dict],
    series: list[dict],
) -> dict[str, int]:
    session = SessionLocal()
    try:
        counts = _insert_dataset_records(session, collection, patients, studies, series)
        session.commit()
        return counts
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# SET OPERATIONS


# this method receives the session object handling all the ORM transactions on our DB and the data related to the object we want to add.
# If the object is already present we simply return it.
# Input:
# - session object
# - collection data in dictionary form
# Output
# - object that we added or that we found
def create_collection(session, data: dict):
    obj = (
        session
        .query(Collection)
        .filter_by(collection_name=data["collection_name"])
        .first()
    )

    if obj:
        return obj

    obj = Collection(**data)  # Python argument unpacking
    session.add(obj)
    session.commit()
    return obj


# This method adds a study to the DB.
# If the study is already present we simply return it.
# Input:
# - session object
# - study data in dictionary form
# Output
# - obejct that we added or that we found
def create_study(session, data: dict):
    obj = (
        session
        .query(Study)
        .filter_by(study_instance_uid=data["study_instance_uid"])
        .first()
    )

    if obj:
        return obj

    obj = Study(**data)
    session.add(obj)
    session.commit()
    return obj


# This method adds a patient to the DB.
# If the patient is already present we simply return it.
# Input:
# - session object
# - patient data in dictionary form
# Output
# - obejct that we added or that we found
def create_patient(session, data: dict):
    obj = session.query(Patient).filter_by(patient_id=data["patient_id"]).first()

    if obj:
        return obj

    obj = Patient(**data)
    session.add(obj)
    session.commit()
    return obj


# This method adds a series to the DB.
# If the series is already present we simply return it.
# Input:
# - session object
# - series data in dictionary form
# Output
# - obejct that we added or that we found
def create_series(session, data: dict):
    obj = (
        session
        .query(Series)
        .filter_by(series_instance_uid=data["series_instance_uid"])
        .first()
    )

    if obj:
        return obj

    obj = Series(**data)
    session.add(obj)
    session.commit()
    return obj


# Creation and storage of a feature extraction object
def create_extraction(session, data: dict):
    obj = Extraction(**data)
    session.add(obj)
    session.commit()
    return obj


# Creation and storage of a roi object
def create_roi(session, data: dict):
    obj = Roi(**data)
    session.add(obj)
    session.commit()
    return obj.id


# GET OPERATIONS
# No comments because name is self-explanatory


def get_all_studies(session):
    return session.query(Study).all()


def get_all_series(session):
    return session.query(Series).options(joinedload(Series.study)).all()


def get_all_patients(session):
    return session.query(Patient).all()


def get_all_collections(session):
    return session.query(Collection).all()


def get_series_on_collection(session, collection_name):
    return (
        session
        .query(Series)
        .join(Series.study)
        .options(joinedload(Series.study))
        .filter(Study.collection_name_study == collection_name)
        .all()
    )


def get_patient_on_id(session, id):
    return session.query(Patient).filter(Patient.patient_id == id).first()


# Get all feature extraction from the relational DB
def get_all_extractions(session):
    rows = (
        session
        .query(Roi, Extraction)
        .join(Extraction, Extraction.roi_id == Roi.id)
        .all()
    )

    mapped_rows = []
    for roi, extraction in rows:
        mapping_key = get_radiomics_feature_mapping_key(extraction.feature_name)
        standardized_value = SNOMED_value_mapping(session, mapping_key)
        if not standardized_value:
            raise ValueError(f"Missing SNOMED mapping for feature '{mapping_key}'")
        mapped_rows.append((roi, extraction, standardized_value))

    return mapped_rows


# Get all medical series belonging to a TCIA collection from the remote archive
def get_series_on_demand(collectionName):
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"

    params = {"Collection": collectionName, "format": "json"}

    response = requests.get(url, params=params, timeout=30)
    return get_json_or_empty(response)


# Get all medical series belonging to a TCIA collection from the remote archive
def get_series_on_demand_on_uid(uid):
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"

    params = {"SeriesInstanceUID": uid, "format": "json"}

    response = requests.get(url, params=params, timeout=30)
    data = get_json_or_empty(response)[0]
    return data


# Fetch all series belonging to a study
def get_series_on_demand_on_study_uid(study_uid):
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"

    params = {"StudyInstanceUID": study_uid, "format": "json"}

    response = requests.get(url, params=params, timeout=30)
    return get_json_or_empty(response)


# Fetch all studies belonging to a collection
def get_studies_on_demand(collectionName):
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/NewStudiesInPatientCollection"

    params = {"format": "json", "Collection": collectionName, "fromDate": "01-01-1960"}

    response = requests.get(url, params=params, timeout=30)
    data = get_json_or_empty(response)

    if not data:
        return []

    # Find date_realease
    url_for_series = (
        "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"
    )

    params_for_series = {
        "StudyInstanceUID": data[0]["StudyInstanceUID"],
        "format": "json",
    }

    response_for_series = requests.get(
        url_for_series, params=params_for_series, timeout=30
    )
    series_for_study = get_json_or_empty(response_for_series)
    DateReleased = series_for_study[0].get("DateReleased") if series_for_study else None

    for study in data:
        study["DateReleased"] = DateReleased

    return data


# Fetch all patients and enrich them with age data
def get_patients_on_demand(collectionName):

    print("Sending request")

    url_for_patients = (
        "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getPatient"
    )

    patient_params = {"Collection": collectionName, "format": "json"}

    response = requests.get(url_for_patients, params=patient_params, timeout=30)
    patients = get_json_or_empty(response)

    print("Patients fetched")

    # Fetch ALL series once
    url_for_series = (
        "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"
    )

    series_params = {"Collection": collectionName, "format": "json"}

    series_response = requests.get(url_for_series, params=series_params, timeout=30)

    series_data = get_json_or_empty(series_response)

    print("Series fetched")

    # Build PatientID -> Age map
    age_map = {}

    for series in series_data:
        patient_id = series.get("PatientID")
        age = series.get("PatientAge")

        if patient_id and patient_id not in age_map:
            if age is not None:
                match = re.search(r"(\d+)", str(age))
                age = int(match.group(1)) if match else None
            else:
                age = None

            age_map[patient_id] = age

    # Attach age to patients
    for patient in patients:
        patient_id = patient.get("PatientId")
        patient["PatientAge"] = age_map.get(patient_id)
        print(patient["PatientAge"])

    print("Done")

    return patients


# Fetch a patient by ID and enrich it with age data
def get_patients_on_demand_on_id(collectionName, patient_id):

    print("Sending request")

    url_for_patients = (
        "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getPatient"
    )

    patient_params = {
        "format": "json",
        "Collection": collectionName,
        "PatientId": patient_id,
    }

    response = requests.get(url_for_patients, params=patient_params, timeout=30)
    patients = get_json_or_empty(response)

    if not patients:
        return {}

    print("Patients fetched")

    # Fetch ALL series once
    url_for_series = (
        "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"
    )

    series_params = {"Collection": collectionName, "format": "json"}

    series_response = requests.get(url_for_series, params=series_params, timeout=30)

    series_data = get_json_or_empty(series_response)

    print("Series fetched")

    # Build PatientID -> Age map
    age_map = {}

    for series in series_data:
        patient_id = series.get("PatientID")
        age = series.get("PatientAge")

        if patient_id and patient_id not in age_map:
            if age is not None:
                match = re.search(r"(\d+)", str(age))
                age = int(match.group(1)) if match else None
            else:
                age = None

            age_map[patient_id] = age

    # Attach age to patients
    for patient in patients:
        patient_id = patient.get("PatientId")
        patient["PatientAge"] = age_map.get(patient_id)
        print(patient["PatientAge"])

    print("Done")

    return patients[0]


# Retrieve all DICOM to SNOMED field mappings
def get_SNOMED_fields(session):
    return session.query(
        FieldMapping.field_name_dicom, FieldMapping.standardized_field_name
    ).all()


# Map an original value to its standardized SNOMED value
def SNOMED_value_mapping(session, original_value):
    global _VALUE_MAPPINGS_AVAILABLE

    if _VALUE_MAPPINGS_AVAILABLE is False:
        return None

    if not value_mappings_available(session):
        return None

    try:
        return (
            session
            .query(ValueMapping.standardized_value)
            .filter(ValueMapping.original_value == original_value)
            .scalar()
        )
    except ProgrammingError:
        session.rollback()
        _VALUE_MAPPINGS_AVAILABLE = False
        return None
