from fastapi import APIRouter, File, UploadFile, Form
import app.etl.pipeline as pipe
from pydantic import BaseModel

router = APIRouter(tags=["ADD DATA"])


class NewDatasetAdditionResponse(BaseModel):
    status_operation: str
    error: str | None = None


@router.post("/add_dataset", response_model=NewDatasetAdditionResponse)
def add_new_dataset(
    collectionName: str = Form(...),
    datasetType: str = Form(...),
    description: str | None = Form(None),
    zipFile: UploadFile | None = File(None),
):
    return pipe.add_new_dataset(
        collectionName=collectionName,
        datasetType=datasetType,
        description=description,
        zipFile=zipFile,
    )
