# This defines the database schema in Python form (ORM models).

# What it should contain
# 1. Tables (Patient, Study, Series, Collection)
# 2. Columns and types
# 3. Relationships (foreign keys)

from app.db.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Time, Boolean, Date, Float
from sqlalchemy.orm import relationship


# =========================
# COLLECTION
# =========================
class Collection(Base):
    __tablename__ = "collections"

    name = Column(String, primary_key=True)
    description = Column(String)
    license_name = Column(String)
    license_uri = Column(String)
    description_uri = Column(String)

    studies = relationship("Study", back_populates="collection_obj")


# =========================
# PATIENT
# =========================
class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True)
    sex = Column(String)
    age = Column(Integer)
    ethnic_group = Column(String)

    studies = relationship("Study", back_populates="patient")


# =========================
# STUDY
# =========================
class Study(Base):
    __tablename__ = "studies"

    instance_uid = Column(String, primary_key=True)
    collection = Column(String, ForeignKey("collections.name"))
    patient_id = Column(String, ForeignKey("patients.id"))
    date = Column(Date)
    date_released = Column(Date)
    description = Column(String)
    series_count = Column(Integer)
    longitudinal_temporal_event_type = Column(String)
    longitudinal_temporal_offset_from_event = Column(String)

    collection_obj = relationship("Collection", back_populates="studies")
    patient = relationship("Patient", back_populates="studies")
    series = relationship("Series", back_populates="study")


# =========================
# SERIES
# =========================
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

    study = relationship("Study", back_populates="series")
    extractions = relationship("Extraction", back_populates="series")


# =========================
# EXTRACTIONs
# =========================
class Extraction(Base):
    __tablename__ = "extractions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_number = Column(String)
    series_uid = Column(String, ForeignKey("series.instance_uid"))
    value = Column(Float)

    series = relationship("Series", back_populates="extractions")


# =========================
# FIELD MAPPINGs
# =========================
class Field_mapping(Base):
    __tablename__ = "field_mappings"

    field_name_DICOM = Column(String, primary_key=True)
    standardized_field_name = Column(String)
    code = Column(Integer)
    vocabulary = Column(String)


# =========================
# VALUE MAPPINGs
# =========================
class Value_mapping(Base):
    __tablename__ = "value_mappings"

    original_value = Column(String, primary_key=True)
    standardized_value = Column(String)
    code = Column(Integer)
    vocabulary = Column(String)
