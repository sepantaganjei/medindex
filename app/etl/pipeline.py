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
import json
from pathlib import Path

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
    if not raw_data:
        print("Data is missing or name not corresponding")
    else:
        print("Data has been found")
    session = SessionLocal()

    try:
        print("Starting collection info imputation")
        _process_and_store_collection(session, raw_data, dataset_type, description)
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


def get_mappings():
    MAPPING_PATH = Path(__file__).resolve().with_name("mapping_values.json")

    with open(MAPPING_PATH, "r") as f:
        return json.load(f)


def standardize_value(value, mapping):
    mapped = mapping.get(value)
    return mapped["standardized_feature_name"] if mapped else value


# Insertion of new collection
def _process_and_store_collection(session, raw_data, dataset_type, description=None):
    mapping = get_mappings()

    transform = collection_data_transformers[dataset_type]
    clean_collection_data = transform(raw_data, description)

    for key in list(clean_collection_data.keys()):
        clean_collection_data[key] = standardize_value(
            clean_collection_data[key], mapping
        )

    return repo.create_collection(session, clean_collection_data)


# Patients insertion from new collection
def _process_and_store_patients(session, raw_data, dataset_type):
    mapping = get_mappings()

    transform = patients_data_transformers[dataset_type]
    clean_patients_data = transform(raw_data)

    patients = []
    for patient in clean_patients_data:
        for key in list(patient.keys()):
            patient[key] = standardize_value(patient[key], mapping)

        obj = repo.create_patient(session, patient)
        patients.append(obj)

    return patients


# Studies insertion from new collection
def _process_and_store_studies(session, raw_data, dataset_type):
    mapping = get_mappings()

    transform = studies_data_transformers[dataset_type]
    clean_studies_data = transform(raw_data)

    studies = []
    for study in clean_studies_data:
        for key in list(study.keys()):
            study[key] = standardize_value(study[key], mapping)

        obj = repo.create_study(session, study)
        studies.append(obj)

    return studies


# Series insertion from new collection
def _process_and_store_series(session, raw_data, dataset_type):
    mapping = get_mappings()

    transform = series_data_transformers[dataset_type]
    clean_series_data = transform(raw_data)

    series = []
    for s in clean_series_data:
        for key in list(s.keys()):
            s[key] = standardize_value(s[key], mapping)

        obj = repo.create_series(session, s)
        series.append(obj)

    return series


# add new feature extraction
def add_extraction(image_number, series_uid, feature_name, value):
    with open("assets/mapping_values.json", "r") as f:
        mapping = json.load(f)
    session = SessionLocal()
    try:
        feature_mapping = mapping.get(feature_name, {})

        data = {
            "image_number": image_number,
            "series_uid": series_uid,
            "feature_name": feature_name,
            "standardized_feature_name": feature_mapping.get(
                "standardized_feature_name", "Unknown"
            ),
            "vocabulary": feature_mapping.get("vocabulary", "Unknown"),
            "value": value,
        }
        obj = repo.create_extraction(session, data)

        return {"status_operation": "success", "id": obj.id, "error": None}
    except Exception as e:
        return {"status_operation": "fail", "id": None, "error": str(e)}
    finally:
        session.close()


# ==========
# Retrievals
# ==========


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


def get_all_collections():
    session = SessionLocal()

    try:
        return repo.get_all_collections(session)

    finally:
        session.close()


def get_all_extractions():
    session = SessionLocal()

    try:
        return repo.get_all_extractions(session)

    finally:
        session.close()


# On demand


def get_series_on_demand(collectionName):
    mapping = get_mappings()
    to_select = [
        "SeriesInstanceUID",
        "StudyInstanceUID",
        "Modality",
        "BodyPartExamined",
        "ProtocolName",
        "StudyDate",
        "SeriesDescription",
        "Site",
        "Manufacturer",
        "ManufacturerModelName",
        "SoftwareVersions",
        "ImageCount",
        "MaxSubmissionTimestamp",
        "FileSize",
        "ThirdPartyAnalysis",
        "Collection",
        "PatientID",
    ]

    map = {
        "SeriesInstanceUID": "instance_uid",
        "StudyInstanceUID": "study_instance_uid",
        "Modality": "modality",
        "BodyPartExamined": "body_part",
        "ProtocolName": "protocol_name",
        "StudyDate": "series_date",
        "SeriesDescription": "series_description",
        "Site": "site",
        "Manufacturer": "manufacturer",
        "ManufacturerModelName": "manufacturer_model_name",
        "SoftwareVersions": "software_versions",
        "ImageCount": "image_count",
        "MaxSubmissionTimestamp": "max_submission_timestamp",
        "FileSize": "file_size",
        "ThirdPartyAnalysis": "third_party_analysis",
        "Collection": "collection",
        "PatientID": "patient_id",
    }

    series_to_return = repo.get_series_on_demand(collectionName)
    for i, series in enumerate(series_to_return):
        temp = {}
        for key in series.keys():
            if key in to_select:
                temp[map[key]] = series[key] if series[key] else "Missing"
                temp[map[key]] = standardize_value(temp[map[key]], mapping)

        series_to_return[i] = temp

    return series_to_return


def get_series_on_demand_on_uid(uid):
    mapping = get_mappings()
    to_select = [
        "SeriesInstanceUID",
        "StudyInstanceUID",
        "Modality",
        "BodyPartExamined",
        "ProtocolName",
        "StudyDate",
        "SeriesDescription",
        "Site",
        "Manufacturer",
        "ManufacturerModelName",
        "SoftwareVersions",
        "ImageCount",
        "MaxSubmissionTimestamp",
        "FileSize",
        "ThirdPartyAnalysis",
        "Collection",
        "PatientID",
    ]

    map = {
        "SeriesInstanceUID": "instance_uid",
        "StudyInstanceUID": "study_instance_uid",
        "Modality": "modality",
        "BodyPartExamined": "body_part",
        "ProtocolName": "protocol_name",
        "StudyDate": "series_date",
        "SeriesDescription": "series_description",
        "Site": "site",
        "Manufacturer": "manufacturer",
        "ManufacturerModelName": "manufacturer_model_name",
        "SoftwareVersions": "software_versions",
        "ImageCount": "image_count",
        "MaxSubmissionTimestamp": "max_submission_timestamp",
        "FileSize": "file_size",
        "ThirdPartyAnalysis": "third_party_analysis",
        "Collection": "collection",
        "PatientID": "patient_id",
    }

    series = repo.get_series_on_demand_on_uid(uid)
    temp = {}
    for key in series.keys():
        if key in to_select:
            temp[map[key]] = series[key] if series[key] else "Missing"
            temp[map[key]] = standardize_value(temp[map[key]], mapping)

    series = temp

    return series


def get_series_on_demand_on_study_uid(study_uid):
    mapping = get_mappings()
    to_select = [
        "SeriesInstanceUID",
        "StudyInstanceUID",
        "Modality",
        "BodyPartExamined",
        "ProtocolName",
        "StudyDate",
        "SeriesDescription",
        "Site",
        "Manufacturer",
        "ManufacturerModelName",
        "SoftwareVersions",
        "ImageCount",
        "MaxSubmissionTimestamp",
        "FileSize",
        "ThirdPartyAnalysis",
        "Collection",
        "PatientID",
    ]

    map = {
        "SeriesInstanceUID": "instance_uid",
        "StudyInstanceUID": "study_instance_uid",
        "Modality": "modality",
        "BodyPartExamined": "body_part",
        "ProtocolName": "protocol_name",
        "StudyDate": "series_date",
        "SeriesDescription": "series_description",
        "Site": "site",
        "Manufacturer": "manufacturer",
        "ManufacturerModelName": "manufacturer_model_name",
        "SoftwareVersions": "software_versions",
        "ImageCount": "image_count",
        "MaxSubmissionTimestamp": "max_submission_timestamp",
        "FileSize": "file_size",
        "ThirdPartyAnalysis": "third_party_analysis",
        "Collection": "collection",
        "PatientID": "patient_id",
    }

    series_to_return = repo.get_series_on_demand_on_study_uid(study_uid)
    for i, series in enumerate(series_to_return):
        temp = {}
        for key in series.keys():
            if key in to_select:
                temp[map[key]] = series[key] if series[key] else "Missing"
                temp[map[key]] = standardize_value(temp[map[key]], mapping)

        series_to_return[i] = temp

    return series_to_return


def get_studies_on_demand(collectionName):
    mapping = get_mappings()
    to_select = [
        "StudyInstanceUID",
        "Collection",
        "StudyDate",
        "DateReleased",
        "StudyDescription",
        "SeriesCount",
        "PatientID",
        "LongitudinalTemporalEventType",
        "LongitudinalTemporalOffsetFromEvent",
    ]

    map = {
        "StudyInstanceUID": "instance_uid",
        "Collection": "collection",
        "StudyDate": "date",
        "DateReleased": "date_released",
        "StudyDescription": "description",
        "SeriesCount": "series_count",
        "PatientID": "patient_id",
        "LongitudinalTemporalEventType": "longitudinal_temporal_event_type",
        "LongitudinalTemporalOffsetFromEvent": "longitudinal_temporal_offset_from_event",
    }

    studies_to_return = repo.get_studies_on_demand(collectionName)
    for i, study in enumerate(studies_to_return):
        temp = {}
        for key in study.keys():
            if key in to_select:
                temp[map[key]] = study[key] if study[key] else None
                temp[map[key]] = standardize_value(temp[map[key]], mapping)

        studies_to_return[i] = temp

    return studies_to_return


def get_patients_on_demand(collectionName):
    mapping = get_mappings()
    to_select = ["PatientId", "PatientSex", "PatientAge", "EthnicGroup"]

    map = {
        "PatientId": "id",
        "PatientSex": "sex",
        "PatientAge": "age",
        "EthnicGroup": "ethnic_group",
    }

    patients_to_return = repo.get_patients_on_demand(collectionName)
    for i, study in enumerate(patients_to_return):
        temp = {}
        for key in study.keys():
            if key in to_select:
                temp[map[key]] = study[key] if study[key] else None
                temp[map[key]] = standardize_value(temp[map[key]], mapping)

        patients_to_return[i] = temp

    return patients_to_return


def get_patients_on_demand_on_id(collectionName, patient_id):
    mapping = get_mappings()
    to_select = ["PatientId", "PatientSex", "PatientAge", "EthnicGroup"]

    map = {
        "PatientId": "id",
        "PatientSex": "sex",
        "PatientAge": "age",
        "EthnicGroup": "ethnic_group",
    }

    patient = repo.get_patients_on_demand_on_id(collectionName, patient_id)
    temp = {}
    for key in patient.keys():
        if key in to_select:
            temp[map[key]] = patient[key] if patient[key] else None
            temp[map[key]] = standardize_value(temp[map[key]], mapping)

    patient = temp

    return patient
