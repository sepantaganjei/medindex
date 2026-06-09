# This defines the database schema in Python form (ORM models).

# What it should contain
# 1. Tables (Patient, Study, Series, Collection)
# 2. Columns and types
# 3. Relationships (foreign keys)

from app.db.database import Base
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import Time
from sqlalchemy import Boolean
from sqlalchemy import Date
from sqlalchemy import Float
from sqlalchemy import JSON
from sqlalchemy.orm import relationship


# =========================
# COLLECTION
# =========================
class Collection(Base):
    __tablename__ = "collections"

    collection_name = Column(String, primary_key=True)
    description = Column(String)
    type = Column(String)
    license_name = Column(String)
    license_uri = Column(String)
    data_description_uri = Column(String)
    remote = Column(Boolean)

    studies = relationship("Study", back_populates="collection")


# =========================
# PATIENT
# =========================
class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String, primary_key=True)
    patient_sex = Column(String)
    patient_age = Column(Integer)
    ethnic_group = Column(String)

    studies = relationship("Study", back_populates="patient")


# =========================
# STUDY
# =========================
class Study(Base):
    __tablename__ = "studies"

    study_instance_uid = Column(String, primary_key=True)
    collection_name_study = Column(String, ForeignKey("collections.collection_name"))
    patient_id_study = Column(String, ForeignKey("patients.patient_id"))
    study_date = Column(Date)
    date_released = Column(Date)
    study_description = Column(String)
    series_count = Column(Integer)
    longitudinal_temporal_event_type = Column(String)
    longitudinal_temporal_offset_from_event = Column(String)

    collection = relationship("Collection", back_populates="studies")
    patient = relationship("Patient", back_populates="studies")
    series = relationship("Series", back_populates="study")


# =========================
# SERIES
# =========================
class Series(Base):
    __tablename__ = "series"

    series_instance_uid = Column(String, primary_key=True)
    study_instance_uid_series = Column(String, ForeignKey("studies.study_instance_uid"))
    modality = Column(String)
    body_part_examined = Column(String)
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
    rois = relationship("Roi", back_populates="series")


# =========================
# EXTRACTIONs
# =========================
class Extraction(Base):
    __tablename__ = "extractions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    roi_id = Column(Integer, ForeignKey("rois.id"))
    feature_name = Column(String)
    value = Column(Float)

    roi = relationship("Roi", back_populates="extractions")


# =========================
# REGIONS OF INTEREST
# =========================
class Roi(Base):
    __tablename__ = "rois"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_number = Column(String)
    series_instance_uid_roi = Column(String, ForeignKey("series.series_instance_uid"))
    roi_coordinates = Column(JSON)

    series = relationship("Series", back_populates="rois")
    extractions = relationship("Extraction", back_populates="roi")


# =========================
# FIELD MAPPINGs
# =========================
class FieldMapping(Base):
    __tablename__ = "field_mappings"

    field_name_dicom = Column(String, primary_key=True)
    standardized_field_name = Column(String)
    code = Column(Integer)
    vocabulary = Column(String)


# =========================
# VALUE MAPPINGs
# =========================
class ValueMapping(Base):
    __tablename__ = "value_mappings"

    original_value = Column(String, primary_key=True)
    standardized_value = Column(String)
    code = Column(Integer)
    vocabulary = Column(String)
