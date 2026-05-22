from fastapi import APIRouter, File, UploadFile, Form
import app.etl.pipeline as pipe
from pydantic import BaseModel

router = APIRouter(tags=["ADD DATA"])


class NewDatasetAdditionResponse(BaseModel):
    status_operation: str
    error: str | None = None


@router.post("/add_dataset", response_model=NewDatasetAdditionResponse)
def add_new_dataset(
    collection_name: str = Form(...),
    dataset_type: str = Form(...),
    description: str | None = Form(None),
    zip_file: UploadFile | None = File(None),
):
    return pipe.add_new_dataset(
        collection_name=collection_name,
        dataset_type=dataset_type,
        description=description,
        zip_file=zip_file,
    )
