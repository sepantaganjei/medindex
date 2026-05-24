# This is where ALL SQL queries live.

# These are the base models that we'll use to instantiate new objects.
from app.db.models import Collection
from app.db.models import Study
from app.db.models import Patient
from app.db.models import Series
from app.db.models import Extraction
from sqlalchemy.orm import joinedload
import requests
# SET OPERATIONS


# this method receives the session object handling all the ORM transactions on our DB and the data related to the object we want to add.
# If the object is already present we simply return it.
# Input:
# - session object
# - collection data in dictionary form
# Output
# - obejct that we added or that we found
def create_collection(session, data: dict):
    obj = session.query(Collection).filter_by(name=data["name"]).first()

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
    obj = session.query(Study).filter_by(instance_uid=data["instance_uid"]).first()

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
    obj = session.query(Patient).filter_by(id=data["id"]).first()

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
    obj = session.query(Series).filter_by(instance_uid=data["instance_uid"]).first()

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
    return session.query(Patient).filter(Patient.id == id).first()


def get_all_extractions(session):
    return session.query(Extraction).all()


def get_series_on_demand(collectionName):
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"

    params = {"Collection": collectionName, "format": "json"}

    response = requests.get(url, params=params, timeout=30)
    data = response.json()
    return data
