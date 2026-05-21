# This is where ALL SQL queries live.

# These are the base models that we'll use to instantiate new objects.
from app.db.models import Collection
from app.db.models import Study
from app.db.models import Patient
from app.db.models import Series

# SET OPRATIONS


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


# GET OPRATIONS


def get_studies(session):
    return session.query(Study).all()


def get_all_series(session):
    return session.query(Series).all()


def get_patients(session):
    return session.query(Patient).all()


def get_collections(session):
    return session.query(Collection).all()


def get_series_on_collection(session, collection_name):
    return (
        session
        .query(Series)
        .join(Series.study)
        .filter_by(Study.collection == collection_name)
        .all()
    )


def get_series_on_study(session, study_uid):
    return session.query(Series).filter_by(study_instance_uid=study_uid).all()
