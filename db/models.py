# This defines the database schema in Python form (ORM models).

# What it should contain
# 1. Tables (Patient, Study, Series, Collection)
# 2. Columns and types
# 3. Relationships (foreign keys)

from db.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Time, Boolean, Date

# Collection model

class Collection(Base):
    __tablename__ = "collections"

    name = Column(String, primary_key=True)
    description = Column(String)
    collection_desc_timestamp = Column(Time)
    license_id = Column(String)
    description_uri = Column(String)

# Study model

class Study(Base):
    __tablename__ = "studies"

    instance_uid = Column(String, primary_key = True)
    collection = Column(String, ForeignKey("collections.name"))
    date = Column(Date)
    description = Column(String)
    patient_id = Column(String, ForeignKey("patients.id"))
    authorized = Column(Boolean)

# Patient model

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True)
    sex = Column(String)
    age = Column(Integer)
    ethnic_group = Column(String)
    authorized = Column(Boolean)

# Series model

class Series(Base):
    __tablename__ = "series"

    instance_uid = Column(String, primary_key = True)
    study_instance_uid = Column(String, ForeignKey("studies.instance_uid"))
    modality = Column(String)
    protocol_name  = Column(String)
    series_date = Column(Date)
    series_description = Column(String)
    series_number = Column(String)
    site = Column(String)
    manufacturer = Column(String)
    manufacturer_model_name = Column(String)
    software_versions = Column(String)
    image_count = Column(Integer)
    max_submission_timestamp = Column(Time)
    license_name = Column(String)
    license_uri = Column(String)
    data_description_uri = Column(String)
    file_size = Column(Integer)
    date_released = Column(Date)
