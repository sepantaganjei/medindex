from enum import Enum

from fastapi import APIRouter, File, HTTPException, UploadFile, Form
import app.etl.pipeline as pipe
from app.etl.zip_pipeline import ZipIngestionError, ingest_zip_dataset
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["ADD DATA"])


class NewDatasetAdditionResponse(BaseModel):
    status_operation: str
    error: str | None = None


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


class DatasetType(str, Enum):
    DICOM = "dicom"
    NIFTI = "nifti"


@router.post("/addZipDataset", response_model=ZipDatasetAdditionResponse)
def add_zip_dataset(
    dataset_type: DatasetType = Form(...),
    zip_file: UploadFile = File(...),
    collection_name: str | None = Form(None),
    description: str | None = Form(None),
    column_mapping: str | None = Form(None),
):
    try:
        return ingest_zip_dataset(
            dataset_type=dataset_type.value,
            zip_file=zip_file,
            collection_name=collection_name,
            description=description,
            column_mapping=column_mapping,
        )
    except ZipIngestionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


# add dicom dataset
@router.post("/addDICOMdataset", response_model=NewDatasetAdditionResponse)
def add_new_DICOM_dataset(collection_name: str):
    return pipe.add_new_dataset(collection_name=collection_name, dataset_type="dicom")


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
    )


class ExtractionInsertionResponse(BaseModel):
    status_operation: str
    id: int | None = None
    error: str | None = None


# add feature extraction
@router.post("/addExtraction", response_model=ExtractionInsertionResponse)
def add_extraction(image_number: str, series_uid: str, feature_name: str, value: str):
    return pipe.add_extraction(image_number, series_uid, feature_name, value)
