# This is where ALL SQL queries live.

from db.models import Collection
from db.models import Study
from db.models import Patient
from db.models import Series

def get_or_create_collection(session, data: dict):
    obj = session.query(Collection).filter_by(name=data['name']).first()

    if obj:
        return obj
    
    obj = Collection(**data) # Python argument unpacking
    session.add(obj)
    session.commit()
    return obj

def get_or_create_study(session, data: dict):
    obj = session.query(Study).filter_by(instance_uid=data['instance_uid']).first()

    if obj:
        return obj
    
    obj = Study(**data)
    session.add(obj)
    session.commit()
    return obj

def get_or_create_patient(session, data: dict):
    obj = session.query(Patient).filter_by(id=data['id']).first()

    if obj:
        return obj
    
    obj = Patient(**data)
    session.add(obj)
    session.commit()
    return obj

def get_or_create_series(session, data: dict):
    obj = session.query(Series).filter_by(instance_uid=data['instance_uid']).first()

    if obj:
        return obj
    
    obj = Series(**data)
    session.add(obj)
    session.commit()
    return obj
