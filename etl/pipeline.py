# This package is used as orchestrator and manages data between db and views.

import etl.dicom_transform as dcm_tsf
import etl.nifti_transform as nii_tsf
import etl.extract as extract
import db.repository as repo

# =============
# ADDING A NEW COLLECTION TO THE PLATFORM
# raw_data is a structured dataset containing:
# - collection info
# - patients
# - studies
# - series
# Each transformer extracts and processes its relevant subset.
# =============

def add_new_dataset(session, collection_name, dataset_type):
    dataset_type = dataset_type.upper()
    raw_data = extract.get_data_from_archive(collection_name, dataset_type)
    dataset = {
        "collection" : process_and_store_collection(session, raw_data, dataset_type),
        "patients" : process_and_store_patients(session, raw_data, dataset_type),
        "studies" : process_and_store_studies(session, raw_data, dataset_type),
        "series" : process_and_store_series(session, raw_data, dataset_type)
    }

    # Returns dictionary of ORM objects
    return dataset

# Set of data transformers
# They depend on the data (collection/patient/study/series) and on the dataset type
collection_data_transformers = { "DICOM": dcm_tsf.prepare_collection_data, "NIFTI": nii_tsf.prepare_collection_data}
patients_data_transformers = {"DICOM": dcm_tsf.prepare_patients_data, "NIFTI": nii_tsf.prepare_patients_data}
studies_data_transformers = {"DICOM": dcm_tsf.prepare_studies_data, "NIFTI": nii_tsf.prepare_studies_data}
series_data_transformers = {"DICOM": dcm_tsf.prepare_series_data, "NIFTI": nii_tsf.prepare_series_data}

# Insertion of new collection
def process_and_store_collection(session, raw_data, dataset_type):
    transform = collection_data_transformers[dataset_type]
    clean_collection_data = transform(raw_data)
    return repo.get_or_create_collection(session, clean_collection_data)

# Patients insertion from new collection
def process_and_store_patients(session, raw_data, dataset_type):
    transform = patients_data_transformers[dataset_type]
    clean_patients_data = transform(raw_data)

    patients = []
    for patient in clean_patients_data:
        obj = repo.get_or_create_patient(session, patient)
        patients.append(obj)

    return patients

# Studies insertion from new collection
def process_and_store_studies(session, raw_data, dataset_type):
    transform = studies_data_transformers[dataset_type]
    clean_studies_data = transform(raw_data)

    studies = []
    for study in clean_studies_data:
        obj = repo.get_or_create_study(session, study)
        studies.append(obj)

    return studies

# Series insertion from new collection
def process_and_store_series(session, raw_data, dataset_type):
    transform = series_data_transformers[dataset_type]
    clean_series_data = transform(raw_data)

    series = []
    for s in clean_series_data:
        obj = repo.get_or_create_series(session, s)
        series.append(obj)

    return series


def download_image_series(series_uid):
    zip_file = extract.getZip(series_uid)

    with open(f"{series_uid}.zip", "wb") as f:
        f.write(zip_file.content)
    
    print("Downloaded images.zip")











def view_collection_dataset():
    pass

def view_study_dataset():
    pass

def view_patient_dataset():
    pass

def view_series_dataset():
    pass