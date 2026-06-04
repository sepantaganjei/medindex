# This is where ALL SQL queries live.

# These are the base models that we'll use to instantiate new objects.
from app.db.models import Collection
from app.db.models import Study
from app.db.models import Patient
from app.db.models import Series
from app.db.models import Extraction
from app.db.models import FieldMapping
from app.db.models import ValueMapping
from sqlalchemy.orm import joinedload
import requests
import re


def get_json_or_empty(response):
    response.raise_for_status()

    if not response.text.strip():
        return []

    return response.json()


# SET OPERATIONS


# this method receives the session object handling all the ORM transactions on our DB and the data related to the object we want to add.
# If the object is already present we simply return it.
# Input:
# - session object
# - collection data in dictionary form
# Output
# - obejct that we added or that we found
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


def create_extraction(session, data: dict):
    obj = Extraction(**data)
    session.add(obj)
    session.commit()
    return obj


# GET OPRATIONS
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
        .filter(Study.collection == collection_name)
        .all()
    )


def get_patient_on_id(session, id):
    return session.query(Patient).filter(Patient.patient_id == id).first()


def get_all_extractions(session):
    rows = (
        session
        .query(Extraction, ValueMapping.standardized_value)
        .join(ValueMapping, ValueMapping.original_value == Extraction.feature_name)
        .all()
    )
    return rows


def get_series_on_demand(collectionName):
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"

    params = {"Collection": collectionName, "format": "json"}

    response = requests.get(url, params=params, timeout=30)
    return get_json_or_empty(response)


def get_series_on_demand_on_uid(uid):
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"

    params = {"SeriesInstanceUID": uid, "format": "json"}

    response = requests.get(url, params=params, timeout=30)
    data = get_json_or_empty(response)[0]
    return data


def get_series_on_demand_on_study_uid(study_uid):
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"

    params = {"StudyInstanceUID": study_uid, "format": "json"}

    response = requests.get(url, params=params, timeout=30)
    return get_json_or_empty(response)


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


def get_SNOMED_fields(session):
    return session.query(
        FieldMapping.field_name_dicom, FieldMapping.standardized_field_name
    ).all()
