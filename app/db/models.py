# This defines the database schema in Python form (ORM models).

# What it should contain
# 1. Tables (Patient, Study, Series, Collection)
# 2. Columns and types
# 3. Relationships (foreign keys)

from app.db.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Time, Boolean, Date


# Collection model
class Collection(Base):
    __tablename__ = "collections"

    name = Column(String, primary_key=True)
    description = Column(String)
    license_name = Column(String)
    license_uri = Column(String)
    description_uri = Column(String)


# Patient model
class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True)
    sex = Column(String)
    age = Column(Integer)
    ethnic_group = Column(String)


# Study model
class Study(Base):
    __tablename__ = "studies"

    instance_uid = Column(String, primary_key=True)
    collection = Column(String, ForeignKey("collections.name"))
    date = Column(Date)
    date_released = Column(Date)
    description = Column(String)
    series_count = Column(Integer)
    patient_id = Column(String, ForeignKey("patients.id"))
    LongitudinalTemporalEventType = Column(String)
    LongitudinalTemporalOffsetFromEvent = Column(String)


# Series model
class Series(Base):
    __tablename__ = "series"

    instance_uid = Column(String, primary_key=True)
    study_instance_uid = Column(String, ForeignKey("studies.instance_uid"))
    modality = Column(String)
    body_part = Column(String)
    protocol_name = Column(String)
    series_date = Column(Date)
    series_description = Column(String)
    site = Column(String)
    manufacturer = Column(String)
    manufacturer_model_name = Column(String)
    software_versions = Column(String)
    image_count = Column(Integer)
    max_submission_timestamp = Column(Time)
    file_size = Column(Integer)
    third_party_analysis = Column(Boolean)
