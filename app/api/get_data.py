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


# get collections
@router.get("/collectionsToDownload", response_model=list[CollectionsResponse])
def get_collections_available_for_download():
    return pipe.get_collections_available_for_download()


class PatientResponse(BaseModel):
    id: str
    sex: str
    age: int
    ethnic_group: str


# get patient on id
@router.get("/patient", response_model=list[CollectionsResponse])
def get_patient_on_id(id: str):
    return pipe.get_patient_on_id(id)
