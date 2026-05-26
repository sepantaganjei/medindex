from fastapi import APIRouter, File, UploadFile, Form
import app.etl.pipeline as pipe
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["ADD DATA"])


class NewDatasetAdditionResponse(BaseModel):
    status_operation: str
    error: str | None = None


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
