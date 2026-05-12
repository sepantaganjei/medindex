# This is where ALL SQL queries live.

# These are the base models that we'll use to instantiate new objects. 
from db.models import Collection
from db.models import Study
from db.models import Patient
from db.models import Series

# this method receives the session object handling all the ORM transactions on our DB and the data related to the object we want to add.
# If the object is already present we simply return it.
# Input:
# - session object
# - collection data in dictionary form
# Output
# - obejct that we added or that we found
def get_or_create_collection(session, data: dict):
    obj = session.query(Collection).filter_by(name=data['name']).first()

    if obj:
        return obj
    
    obj = Collection(**data) # Python argument unpacking
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
def get_or_create_study(session, data: dict):
    obj = session.query(Study).filter_by(instance_uid=data['instance_uid']).first()

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
def get_or_create_patient(session, data: dict):
    obj = session.query(Patient).filter_by(id=data['id']).first()

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
def get_or_create_series(session, data: dict):
    obj = session.query(Series).filter_by(instance_uid=data['instance_uid']).first()

    if obj:
        return obj
    
    obj = Series(**data)
    session.add(obj)
    session.commit()
    return obj
