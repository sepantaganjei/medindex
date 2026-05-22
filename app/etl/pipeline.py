# This package is used as orchestrator and manages data between db and views.

import app.etl.dicom_transform as dcm_tsf
import app.etl.nifti_transform as nii_tsf
import app.etl.extract as extract
import app.db.repository as repo
from app.db.database import SessionLocal
import zipfile
import os
import re
import html
# ==========
# Insertions
# ==========


def extract_zip(upload_file, target_folder: str):
    os.makedirs(target_folder, exist_ok=True)

    with zipfile.ZipFile(upload_file.file) as zip_ref:
        zip_ref.extractall(target_folder)


def add_new_dataset(collection_name, dataset_type, description=None, zip_file=None):
    dataset_type = dataset_type.upper()

    if zip_file:
        extract_zip(zip_file, collection_name)

    raw_data = extract.get_data_from_archive(collection_name, dataset_type)
    print("Data has been found!")
    session = SessionLocal()

    try:
        print("Starting collection info imputation")
        _process_and_store_collection(session, raw_data, dataset_type)
        print("Finished collection info imputation")

        print("Starting patients info imputation")
        _process_and_store_patients(session, raw_data, dataset_type)
        print("Finished patients info imputation")

        print("Starting studies info imputation")
        _process_and_store_studies(session, raw_data, dataset_type)
        print("Finished studies info imputation")

        print("Starting series info imputation")
        _process_and_store_series(session, raw_data, dataset_type)
        print("Finished series info imputation")

        return {"status_operation": "success", "error": None}
    except Exception as e:
        return {"status_operation": "fail", "error": str(e)}

    finally:
        session.close()


# Set of data transformers
# They depend on the data (collection/patient/study/series) and on the dataset type
collection_data_transformers = {
    "DICOM": dcm_tsf.prepare_collection_data,
    "NIFTI": nii_tsf.prepare_collection_data,
}
patients_data_transformers = {
    "DICOM": dcm_tsf.prepare_patients_data,
    "NIFTI": nii_tsf.prepare_patients_data,
}
studies_data_transformers = {
    "DICOM": dcm_tsf.prepare_studies_data,
    "NIFTI": nii_tsf.prepare_studies_data,
}
series_data_transformers = {
    "DICOM": dcm_tsf.prepare_series_data,
    "NIFTI": nii_tsf.prepare_series_data,
}


# Insertion of new collection
def _process_and_store_collection(session, raw_data, dataset_type):
    transform = collection_data_transformers[dataset_type]
    clean_collection_data = transform(raw_data)
    return repo.create_collection(session, clean_collection_data)


# Patients insertion from new collection
def _process_and_store_patients(session, raw_data, dataset_type):
    transform = patients_data_transformers[dataset_type]
    clean_patients_data = transform(raw_data)

    patients = []
    for patient in clean_patients_data:
        obj = repo.create_patient(session, patient)
        patients.append(obj)

    return patients


# Studies insertion from new collection
def _process_and_store_studies(session, raw_data, dataset_type):
    transform = studies_data_transformers[dataset_type]
    clean_studies_data = transform(raw_data)

    studies = []
    for study in clean_studies_data:
        obj = repo.create_study(session, study)
        studies.append(obj)

    return studies


# Series insertion from new collection
def _process_and_store_series(session, raw_data, dataset_type):
    transform = series_data_transformers[dataset_type]
    clean_series_data = transform(raw_data)

    series = []
    for s in clean_series_data:
        obj = repo.create_series(session, s)
        series.append(obj)

    return series


def _clean_description(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_collections_available_for_download():
    print("starting extractions")
    collections = extract.getAllDICOMCollections()
    print("got extractions")

    list_of_collections = []

    for item in collections:
        name = item.get("collectionName", "")
        description = item.get("description", "")
        description = _clean_description(description)
        list_of_collections.append({"name": name, "description": description})

    return list_of_collections


# ==========
# Retrievals
# ==========


def get_all_series(collection_name):
    session = SessionLocal()

    try:
        if not collection_name:
            return repo.get_all_series(session)

        return repo.get_series_on_collection(session, collection_name)

    finally:
        session.close()


def get_patient_on_id(id):
    session = SessionLocal()

    try:
        return repo.get_patient_on_id(session, id)

    finally:
        session.close()
