# This is the set of 'add' REST APIs
# They are used to add data to the platform archive (relational DB or MinIO storage bucket)
from enum import Enum

from fastapi import APIRouter, File, HTTPException, UploadFile, Form
import app.etl.pipeline as pipe
from app.etl.zip_pipeline import ZipIngestionError, ingest_zip_dataset
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["ADD DATA"])


# Response to the addtion of a new dataset from TCIA archive
class NewDatasetAdditionResponse(BaseModel):
    status_operation: str
    error: str | None = None


# Response to the addtion of a new dataset from local file system
class ZipDatasetAdditionResponse(BaseModel):
    status_operation: str
    collection_name: str | None = None
    dataset_type: str | None = None
    files_discovered: int = 0
    files_uploaded: int = 0
    patients_inserted: int = 0
    studies_inserted: int = 0
    series_inserted: int = 0
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


# Definition of the dataset type
class DatasetType(str, Enum):
    DICOM = "dicom"
    NIFTI = "nifti"


# Addition of a dataset in Zip form from local file system
@router.post("/addZipDataset", response_model=ZipDatasetAdditionResponse)
def add_zip_dataset(
    dataset_type: DatasetType = Form(...),
    zip_file: UploadFile = File(...),
    metadata_file: UploadFile | None = File(None),
    collection_name: str | None = Form(None),
    description: str | None = Form(None),
    column_mapping: str | None = Form(None),
    allow_description_series_matching: bool = Form(False),
):
    try:
        return ingest_zip_dataset(
            dataset_type=dataset_type.value,
            zip_file=zip_file,
            metadata_file=metadata_file,
            collection_name=collection_name,
            description=description,
            column_mapping=column_mapping,
            remote=False,
            allow_description_series_matching=allow_description_series_matching,
        )
    except ZipIngestionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


# add dicom dataset
@router.post("/addTCIAdataset", response_model=NewDatasetAdditionResponse)
def add_new_DICOM_dataset(collection_name: str):
    return pipe.add_new_dataset(
        collection_name=collection_name, dataset_type="dicom", remote=True
    )


# An extracted feature is composed of: name and value
class FeatureInput(BaseModel):
    feature_name: str
    value: float


# Definition of the coordinates of a region of interest
class ROI_coordinates(BaseModel):
    x: float
    y: float


# Input to the add API in the case of a feature extraction
class ExtractionInput(BaseModel):
    image_number: str
    series_instance_uid: str
    features_extracted: list[FeatureInput]
    roi_coordinates: list[ROI_coordinates]


# Repsonse after the storage of a feature extraction
class ExtractionInsertionResponse(BaseModel):
    status_operation: str
    error: str | None = None


# add feature extraction
@router.post("/addExtraction", response_model=ExtractionInsertionResponse)
def add_extraction(input_model: ExtractionInput):
    return pipe.add_extraction(input_model)


# ==============
# Obsolete code
# ==============
# add nifti dataset
@router.post("/addNIFTIdataset", response_model=NewDatasetAdditionResponse)
def add_new_NIFTI_dataset(
    collection_name: str = Form(...),
    description: str = Form(...),
    zip_file: UploadFile = File(...),
):
    return pipe.add_new_dataset(
        collection_name=collection_name,
        dataset_type="nifti",
        description=description,
        zip_file=zip_file,
        remote=False,
    )
