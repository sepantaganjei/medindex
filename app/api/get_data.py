from fastapi import APIRouter
from typing import Optional
import app.etl.pipeline as pipe
from pydantic import BaseModel
import datetime as dt

router = APIRouter(tags=["GET DATA"])


class StudyInfo(BaseModel):
    collection: str | None = None
    patient_id: str | None = None

    model_config = {"from_attributes": True}


class SeriesResponse(BaseModel):
    instance_uid: str
    study_instance_uid: str
    modality: str | None = None
    body_part: str | None = None
    protocol_name: str | None = None
    series_date: dt.date | None = None
    series_description: str | None = None
    site: str | None = None
    manufacturer: str | None = None
    manufacturer_model_name: str | None = None
    software_versions: str | None = None
    image_count: int | None = None
    max_submission_timestamp: dt.time | None = None
    file_size: int | None = None
    third_party_analysis: bool | None = None
    study: StudyInfo

    model_config = {"from_attributes": True}


# get series
@router.get("/series", response_model=list[SeriesResponse])
def get_all_series(collectionName: Optional[str] = None):
    return pipe.get_all_series(collectionName)


class CollectionsResponse(BaseModel):
    name: str
    description: str


# get collection available for download
@router.get("/collectionsToDownload", response_model=list[CollectionsResponse])
def get_collections_available_for_download():
    return pipe.get_collections_available_for_download()


# get all collections already downloaded
@router.get("/savedCollections", response_model=list[CollectionsResponse])
def get_all_collections():
    return pipe.get_all_collections()


class PatientResponse(BaseModel):
    id: str
    sex: str | None = None
    age: int | None = None
    ethnic_group: str | None = None

    model_config = {"from_attributes": True}


# get patient on id
@router.get("/patientOnId", response_model=PatientResponse | None)
def get_patient_on_id(id: str):
    return pipe.get_patient_on_id(id)


class ExtractionResponse(BaseModel):
    id: int
    image_number: str
    series_uid: str
    feature_name: str
    standardized_feature_name: str
    vocabulary: str
    value: float

    class Config:
        from_attributes = True


# get all feature extractions
@router.get("/getExtractions", response_model=list[ExtractionResponse])
def get_all_extractions():
    return pipe.get_all_extractions()


# ==================
# get data on demand
# ==================


class SeriesOnDemandResponse(BaseModel):
    instance_uid: str
    study_instance_uid: str
    modality: str | None = None
    body_part: str | None = None
    protocol_name: str | None = None
    series_date: str | None = None
    series_description: str | None = None
    site: str | None = None
    manufacturer: str | None = None
    manufacturer_model_name: str | None = None
    software_versions: str | None = None
    image_count: int | None = None
    max_submission_timestamp: str | None = None
    file_size: int | None = None
    third_party_analysis: str | None = None
    collection: str | None = None
    patient_id: str | None = None


# get series on demand
@router.get("/seriesOnDemand", response_model=list[SeriesOnDemandResponse])
def get_series_on_demand(collectionName):
    return pipe.get_series_on_demand(collectionName)


# get series on demand on uid
@router.get("/seriesOnDemandOnUid", response_model=SeriesOnDemandResponse)
def get_series_on_demand_on_uid(uid):
    return pipe.get_series_on_demand_on_uid(uid)


# get series on demand on study_uid
@router.get("/seriesOnDemandOnStudyUid", response_model=list[SeriesOnDemandResponse])
def get_series_on_demand_on_study_uid(study_uid):
    return pipe.get_series_on_demand_on_study_uid(study_uid)


class StudyResponse(BaseModel):
    instance_uid: str
    collection: str
    date: str | None = None
    date_released: str | None = None
    description: str | None = None
    series_count: int | None = None
    patient_id: str | None = None
    longitudinal_temporal_event_type: str | None = None
    longitudinal_temporal_offset_from_event: int | None = None


# get studies on demand
@router.get("/studiesOnDemand", response_model=list[StudyResponse])
def get_studies_on_demand(collectionName):
    return pipe.get_studies_on_demand(collectionName)


# get patients on demand
@router.get("/patientsOnDemand", response_model=list[PatientResponse])
def get_patients_on_demand(collectionName):
    return pipe.get_patients_on_demand(collectionName)


# get patients on demand on uid
@router.get("/patientsOnDemandOnUid", response_model=PatientResponse)
def get_patients_on_demand_on_id(collectionName, patient_id):
    return pipe.get_patients_on_demand_on_id(collectionName, patient_id)
