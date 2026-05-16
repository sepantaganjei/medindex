import datetime as dt

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.models import Collection, Patient, Series, Study

router = APIRouter(prefix="/api", tags=["mock"])


class CollectionResponse(BaseModel):
    name: str
    description: str | None = None
    license_name: str | None = None
    license_uri: str | None = None
    description_uri: str | None = None


class SeriesListResponse(BaseModel):
    instance_uid: str
    study_instance_uid: str
    modality: str | None = None
    series_description: str | None = None
    series_date: dt.date | None = None
    image_count: int | None = None
    collection: str | None = None
    patient_id: str | None = None


class SeriesDetailResponse(BaseModel):
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
    collection: str | None = None
    patient_id: str | None = None


class StudyMetadataResponse(BaseModel):
    instance_uid: str
    collection: str | None = None
    date: dt.date | None = None
    date_released: dt.date | None = None
    description: str | None = None
    series_count: int | None = None
    patient_id: str | None = None
    longitudinal_temporal_event_type: str | None = None
    longitudinal_temporal_offset_from_event: str | None = None


class PatientMetadataResponse(BaseModel):
    id: str
    sex: str | None = None
    age: int | None = None
    ethnic_group: str | None = None


class SeriesMetadataResponse(BaseModel):
    series_uid: str
    collection: CollectionResponse | None = None
    study: StudyMetadataResponse | None = None
    patient: PatientMetadataResponse | None = None


MOCK_COLLECTIONS = {
    "TCGA-GBM": Collection(
        name="TCGA-GBM",
        description="Glioblastoma multiforme collection",
        license_name="CC BY 4.0",
        license_uri="https://creativecommons.org/licenses/by/4.0/",
        description_uri="https://www.cancerimagingarchive.net/collection/tcga-gbm/",
    ),
    "CPTAC-GBM": Collection(
        name="CPTAC-GBM",
        description="Proteogenomic glioblastoma collection",
        license_name="CC BY 4.0",
        license_uri="https://creativecommons.org/licenses/by/4.0/",
        description_uri="https://www.cancerimagingarchive.net/",
    ),
}

MOCK_PATIENTS = {
    "TCGA-06-0125": Patient(id="TCGA-06-0125", sex="M", age=58, ethnic_group="Not Reported"),
    "C3N-02232": Patient(id="C3N-02232", sex="F", age=63, ethnic_group="Not Reported"),
}

MOCK_STUDIES = {
    "1.2.840.113619.2.55.3.604688121.1234.1111": Study(
        instance_uid="1.2.840.113619.2.55.3.604688121.1234.1111",
        collection="TCGA-GBM",
        date=dt.date(2012, 3, 14),
        date_released=dt.date(2018, 7, 10),
        description="Pre-operative brain MRI",
        series_count=2,
        patient_id="TCGA-06-0125",
        LongitudinalTemporalEventType="Baseline",
        LongitudinalTemporalOffsetFromEvent="0",
    ),
    "1.2.840.113619.2.55.3.604688121.5678.2222": Study(
        instance_uid="1.2.840.113619.2.55.3.604688121.5678.2222",
        collection="CPTAC-GBM",
        date=dt.date(2019, 11, 2),
        date_released=dt.date(2021, 2, 19),
        description="Follow-up MRI",
        series_count=1,
        patient_id="C3N-02232",
        LongitudinalTemporalEventType="Follow-up",
        LongitudinalTemporalOffsetFromEvent="180",
    ),
}

MOCK_SERIES = {
    "1.2.840.113619.2.55.3.604688121.1234.1111.1": Series(
        instance_uid="1.2.840.113619.2.55.3.604688121.1234.1111.1",
        study_instance_uid="1.2.840.113619.2.55.3.604688121.1234.1111",
        modality="MR",
        body_part="BRAIN",
        protocol_name="T1_AX_PRE",
        series_date=dt.date(2012, 3, 14),
        series_description="T1 weighted axial pre-contrast",
        site="POLIMI-HOSPITAL",
        manufacturer="GE",
        manufacturer_model_name="SIGNA HDx",
        software_versions="15.0",
        image_count=176,
        max_submission_timestamp=dt.time(13, 45, 0),
        file_size=73400320,
        third_party_analysis=False,
    ),
    "1.2.840.113619.2.55.3.604688121.1234.1111.2": Series(
        instance_uid="1.2.840.113619.2.55.3.604688121.1234.1111.2",
        study_instance_uid="1.2.840.113619.2.55.3.604688121.1234.1111",
        modality="MR",
        body_part="BRAIN",
        protocol_name="T2_FLAIR",
        series_date=dt.date(2012, 3, 14),
        series_description="T2 FLAIR axial",
        site="POLIMI-HOSPITAL",
        manufacturer="GE",
        manufacturer_model_name="SIGNA HDx",
        software_versions="15.0",
        image_count=164,
        max_submission_timestamp=dt.time(14, 5, 0),
        file_size=67108864,
        third_party_analysis=True,
    ),
    "1.2.840.113619.2.55.3.604688121.5678.2222.1": Series(
        instance_uid="1.2.840.113619.2.55.3.604688121.5678.2222.1",
        study_instance_uid="1.2.840.113619.2.55.3.604688121.5678.2222",
        modality="MR",
        body_part="BRAIN",
        protocol_name="DWI",
        series_date=dt.date(2019, 11, 2),
        series_description="Diffusion weighted imaging",
        site="POLIMI-HOSPITAL",
        manufacturer="Siemens",
        manufacturer_model_name="MAGNETOM Skyra",
        software_versions="syngo MR E11",
        image_count=68,
        max_submission_timestamp=dt.time(9, 32, 0),
        file_size=26214400,
        third_party_analysis=False,
    ),
}


def _build_series_list_row(series: Series) -> SeriesListResponse:
    study = MOCK_STUDIES.get(series.study_instance_uid)
    return SeriesListResponse(
        instance_uid=series.instance_uid,
        study_instance_uid=series.study_instance_uid,
        modality=series.modality,
        series_description=series.series_description,
        series_date=series.series_date,
        image_count=series.image_count,
        collection=study.collection if study else None,
        patient_id=study.patient_id if study else None,
    )


def _build_series_detail(series: Series) -> SeriesDetailResponse:
    study = MOCK_STUDIES.get(series.study_instance_uid)
    return SeriesDetailResponse(
        instance_uid=series.instance_uid,
        study_instance_uid=series.study_instance_uid,
        modality=series.modality,
        body_part=series.body_part,
        protocol_name=series.protocol_name,
        series_date=series.series_date,
        series_description=series.series_description,
        site=series.site,
        manufacturer=series.manufacturer,
        manufacturer_model_name=series.manufacturer_model_name,
        software_versions=series.software_versions,
        image_count=series.image_count,
        max_submission_timestamp=series.max_submission_timestamp,
        file_size=series.file_size,
        third_party_analysis=series.third_party_analysis,
        collection=study.collection if study else None,
        patient_id=study.patient_id if study else None,
    )


@router.get("/collections", response_model=list[CollectionResponse])
def get_collections() -> list[CollectionResponse]:
    return [CollectionResponse.model_validate(collection, from_attributes=True) for collection in MOCK_COLLECTIONS.values()]


@router.get("/series", response_model=list[SeriesListResponse])
def get_series() -> list[SeriesListResponse]:
    return [_build_series_list_row(series) for series in MOCK_SERIES.values()]


@router.get("/series/{series_uid}", response_model=SeriesDetailResponse)
def get_series_detail(series_uid: str) -> SeriesDetailResponse:
    series = MOCK_SERIES.get(series_uid)
    if not series:
        raise HTTPException(status_code=404, detail=f"Series '{series_uid}' not found")
    return _build_series_detail(series)


@router.get("/series/{series_uid}/metadata", response_model=SeriesMetadataResponse)
def get_series_metadata(series_uid: str) -> SeriesMetadataResponse:
    series = MOCK_SERIES.get(series_uid)
    if not series:
        raise HTTPException(status_code=404, detail=f"Series '{series_uid}' not found")

    study = MOCK_STUDIES.get(series.study_instance_uid)
    patient = MOCK_PATIENTS.get(study.patient_id) if study else None
    collection = MOCK_COLLECTIONS.get(study.collection) if study else None

    return SeriesMetadataResponse(
        series_uid=series_uid,
        collection=CollectionResponse.model_validate(collection, from_attributes=True) if collection else None,
        study=StudyMetadataResponse(
            instance_uid=study.instance_uid,
            collection=study.collection,
            date=study.date,
            date_released=study.date_released,
            description=study.description,
            series_count=study.series_count,
            patient_id=study.patient_id,
            longitudinal_temporal_event_type=study.LongitudinalTemporalEventType,
            longitudinal_temporal_offset_from_event=study.LongitudinalTemporalOffsetFromEvent,
        )
        if study
        else None,
        patient=PatientMetadataResponse.model_validate(patient, from_attributes=True) if patient else None,
    )
