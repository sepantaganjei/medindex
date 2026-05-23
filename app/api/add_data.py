from fastapi import APIRouter, File, UploadFile, Form
import app.etl.pipeline as pipe
from pydantic import BaseModel

router = APIRouter(tags=["ADD DATA"])


class NewDatasetAdditionResponse(BaseModel):
    status_operation: str
    error: str | None = None


@router.post("/add_DICOM_dataset", response_model=NewDatasetAdditionResponse)
def add_new_DICOM_dataset(collection_name: str):
    return pipe.add_new_dataset(collection_name=collection_name, dataset_type="dicom")


@router.post("/add_NIFTI_dataset", response_model=NewDatasetAdditionResponse)
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
