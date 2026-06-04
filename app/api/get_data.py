from fastapi import APIRouter
from typing import Optional
import app.etl.pipeline as pipe
from pydantic import BaseModel
import datetime as dt

router = APIRouter(prefix="/api", tags=["GET DATA"])

# ========================
# GET functions for values
# ========================

# ========================
# GET data from db
# ========================


class StudyInfo(BaseModel):
    CollectionName: str | None = None
    PatientID: str | None = None

    model_config = {"from_attributes": True}


class SeriesResponse(BaseModel):
    SeriesInstanceUID: str
    StudyInstanceUID: str
    Modality: str | None = None
    BodyPartExamined: str | None = None
    ProtocolName: str | None = None
    SeriesDate: dt.date | None = None
    SeriesDescription: str | None = None
    Site: str | None = None
    Manufacturer: str | None = None
    ManufacturerModelName: str | None = None
    SoftwareVersions: str | None = None
    ImageCount: int | None = None
    MaxSubmissionTimestamp: dt.time | None = None
    FileSize: int | None = None
    ThirdPartyAnalysis: bool | None = None
    Study: StudyInfo

    model_config = {"from_attributes": True}


# get series
@router.get("/series", response_model=list[SeriesResponse])
def get_all_series(collectionName: Optional[str] = None):
    return pipe.get_all_series(collectionName)


class CollectionsResponse(BaseModel):
    collectionName: str
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
    PatientID: str
    PatientSex: str | None = None
    PatientAge: int | None = None
    EthnicGroup: str | None = None

    model_config = {"from_attributes": True}


# get patient on id
@router.get("/patientOnId", response_model=PatientResponse | None)
def get_patient_on_id(id: str):
    return pipe.get_patient_on_id(id)


class ExtractionResponse(BaseModel):
    Id: int
    ImageNumber: str
    SeriesInstanceUID: str
    FeatureName: str
    Value: float

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
    SeriesInstanceUID: str
    StudyInstanceUID: str
    Modality: str | None = None
    BodyPartExamined: str | None = None
    ProtocolName: str | None = None
    StudyDate: str | None = None
    SeriesDescription: str | None = None
    Site: str | None = None
    Manufacturer: str | None = None
    ManufacturerModelName: str | None = None
    SoftwareVersions: str | None = None
    ImageCount: int | None = None
    MaxSubmissionTimestamp: str | None = None
    FileSize: int | None = None
    ThirdPartyAnalysis: str | None = None
    Collection: str | None = None
    PatientID: str | None = None


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
    StudyInstanceUID: str
    Collection: str
    StudyDate: str | None = None
    DateReleased: str | None = None
    StudyDescription: str | None = None
    SeriesCount: int | None = None
    PatientID: str | None = None
    LongitudinalTemporalEventType: str | None = None
    LongitudinalTemporalOffsetFromEvent: int | None = None


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


# =====================================
# GET functions for standardized fields
# =====================================


# get SNOMED fields for a series
@router.get("/getSeriesSNOMEDFields", response_model=list[str])
def get_series_SNOMED_fields():
    return pipe.get_series_SNOMED_fields()


# get SNOMED fields for a study
@router.get("/getStudySNOMEDFields", response_model=list[str])
def get_study_SNOMED_fields():
    return pipe.get_study_SNOMED_fields()


# get SNOMED fields for a patient
@router.get("/getPatientSNOMEDFields", response_model=list[str])
def get_patient_SNOMED_fields():
    return pipe.get_patient_SNOMED_fields()
