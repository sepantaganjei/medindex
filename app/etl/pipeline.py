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
from app.api.add_data import ExtractionInput
# ==========
# Insertions
# ==========


def extract_zip(upload_file, target_folder: str):
    os.makedirs(target_folder, exist_ok=True)

    with zipfile.ZipFile(upload_file.file) as zip_ref:
        zip_ref.extractall(target_folder)


def add_new_dataset(
    collection_name, dataset_type, description=None, zip_file=None, remote=None
):
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
        _process_and_store_collection(
            session, raw_data, dataset_type, description, remote
        )
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
def _process_and_store_collection(
    session, raw_data, dataset_type, description=None, remote=None
):
    transform = collection_data_transformers[dataset_type]
    clean_collection_data = transform(raw_data, description, remote)
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


# add new feature extraction
def add_extraction(extraction: ExtractionInput):
    session = SessionLocal()
    try:
        roi_data = {"roi_coordinates": extraction.model_dump()["roi_coordinates"]}
        roi_id = repo.create_roi(session, roi_data)

        for feature_extracted in extraction.features_extracted:
            extraction_data = {
                "roi_id": roi_id,
                "image_number": extraction.image_number,
                "series_instance_uid_extraction": extraction.series_instance_uid,
                "feature_name": feature_extracted.feature_name,
                "value": feature_extracted.value,
            }

            repo.create_extraction(session, extraction_data)

        return {"status_operation": "success", "error": None}
    except Exception as e:
        return {"status_operation": "fail", "error": str(e)}
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
        collection_name = item.get("collectionName", "")
        description = item.get("description", "")
        description = _clean_description(description)
        list_of_collections.append({
            "collection_name": collection_name,
            "description": description,
        })

    return list_of_collections


def get_all_series(collection_name):
    fields_to_map = [
        "modality",
        "body_part_examined",
        "protocol_name",
        "series_description",
        "site",
        "manufacturer",
        "manufacturer_model_name",
        "software_versions",
    ]

    session = SessionLocal()

    try:
        if not collection_name:
            list_of_series = repo.get_all_series(session)
        else:
            list_of_series = repo.get_series_on_collection(session, collection_name)

        for series in list_of_series:
            for field in fields_to_map:
                value = getattr(series, field)

                if value:
                    standardized_value = repo.SNOMED_value_mapping(session, value)

                    if standardized_value:
                        setattr(series, field, standardized_value)

        return list_of_series

    finally:
        session.close()


def get_patient_on_id(id):
    fields_to_map = ["patient_sex", "ethnic_group"]
    session = SessionLocal()

    try:
        patient = repo.get_patient_on_id(session, id)
        for field in fields_to_map:
            value = getattr(patient, field)
            if value:
                standardized_value = repo.SNOMED_value_mapping(session, value)

                if standardized_value:
                    setattr(patient, field, standardized_value)

        return patient
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
        rows = repo.get_all_extractions(session)
        return [
            {
                "id": extraction.id,
                "image_number": extraction.image_number,
                "series_instance_uid_extraction": extraction.series_instance_uid_extraction,
                "feature_name": extraction.feature_name,
                "value": extraction.value,
                "standardized_feature_name": std_name,
            }
            for extraction, std_name in rows
        ]

    finally:
        session.close()


# On demand


def get_series_on_demand(collectionName):
    # Retrieval
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
        "SeriesInstanceUID": "series_instance_uid",
        "StudyInstanceUID": "study_instance_uid_series",
        "Modality": "modality",
        "BodyPartExamined": "body_part_examined",
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
        "Collection": "collection_name_study",
        "PatientID": "patient_id_study",
    }

    series_to_return = repo.get_series_on_demand(collectionName)
    for i, series in enumerate(series_to_return):
        temp = {}
        for key in series.keys():
            if key in to_select:
                temp[map[key]] = series[key] if series[key] else "Missing"

        series_to_return[i] = temp

    # Mapping
    fields_to_map = [
        "modality",
        "body_part_examined",
        "protocol_name",
        "series_description",
        "site",
        "manufacturer",
        "manufacturer_model_name",
        "software_versions",
    ]

    session = SessionLocal()
    try:
        for series in series_to_return:
            for field in fields_to_map:
                original_value = series.get(field)
                if original_value:
                    standardized_value = repo.SNOMED_value_mapping(
                        session, original_value
                    )

                    if standardized_value:
                        series[field] = standardized_value

        return series_to_return
    finally:
        session.close()


def get_series_on_demand_on_uid(uid):
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
        "SeriesInstanceUID": "series_instance_uid",
        "StudyInstanceUID": "study_instance_uid_series",
        "Modality": "modality",
        "BodyPartExamined": "body_part_examined",
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
        "Collection": "collection_name_study",
        "PatientID": "patient_id_study",
    }

    series = repo.get_series_on_demand_on_uid(uid)
    temp = {}
    for key in series.keys():
        if key in to_select:
            temp[map[key]] = series[key] if series[key] else "Missing"

    series = temp

    # Mapping
    fields_to_map = [
        "modality",
        "body_part_examined",
        "protocol_name",
        "series_description",
        "site",
        "manufacturer",
        "manufacturer_model_name",
        "software_versions",
    ]

    session = SessionLocal()
    try:
        for field in fields_to_map:
            original_value = series.get(field)
            if original_value:
                standardized_value = repo.SNOMED_value_mapping(session, original_value)

                if standardized_value:
                    series[field] = standardized_value

        return series
    finally:
        session.close()


def get_series_on_demand_on_study_uid(study_uid):
    # Retrieval
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
        "SeriesInstanceUID": "series_instance_uid",
        "StudyInstanceUID": "study_instance_uid_series",
        "Modality": "modality",
        "BodyPartExamined": "body_part_examined",
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
        "Collection": "collection_name_study",
        "PatientID": "patient_id_study",
    }

    series_to_return = repo.get_series_on_demand_on_study_uid(study_uid)
    for i, series in enumerate(series_to_return):
        temp = {}
        for key in series.keys():
            if key in to_select:
                temp[map[key]] = series[key] if series[key] else "Missing"

        series_to_return[i] = temp

    # Mapping
    fields_to_map = [
        "modality",
        "body_part_examined",
        "protocol_name",
        "series_description",
        "site",
        "manufacturer",
        "manufacturer_model_name",
        "software_versions",
    ]

    session = SessionLocal()
    try:
        for series in series_to_return:
            for field in fields_to_map:
                original_value = series.get(field)
                if original_value:
                    standardized_value = repo.SNOMED_value_mapping(
                        session, original_value
                    )

                    if standardized_value:
                        series[field] = standardized_value

        return series_to_return
    finally:
        session.close()


def get_studies_on_demand(collectionName):
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
        "StudyInstanceUID": "study_instance_uid",
        "Collection": "collection_name_study",
        "StudyDate": "study_date",
        "DateReleased": "date_released",
        "StudyDescription": "study_description",
        "SeriesCount": "series_count",
        "PatientID": "patient_id_study",
        "LongitudinalTemporalEventType": "longitudinal_temporal_event_type",
        "LongitudinalTemporalOffsetFromEvent": "longitudinal_temporal_offset_from_event",
    }

    studies_to_return = repo.get_studies_on_demand(collectionName)
    for i, study in enumerate(studies_to_return):
        temp = {}
        for key in study.keys():
            if key in to_select:
                temp[map[key]] = study[key] if study[key] else None

        studies_to_return[i] = temp

    # Mapping
    fields_to_map = ["study_description", "longitudinal_temporal_event_type"]

    session = SessionLocal()
    try:
        for study in studies_to_return:
            for field in fields_to_map:
                original_value = study.get(field)
                if original_value:
                    standardized_value = repo.SNOMED_value_mapping(
                        session, original_value
                    )

                    if standardized_value:
                        study[field] = standardized_value

        return studies_to_return
    finally:
        session.close()


def get_patients_on_demand(collectionName):
    to_select = ["PatientId", "PatientSex", "PatientAge", "EthnicGroup"]

    map = {
        "PatientId": "patient_id",
        "PatientSex": "patient_sex",
        "PatientAge": "patient_age",
        "EthnicGroup": "ethnic_group",
    }

    patients_to_return = repo.get_patients_on_demand(collectionName)
    for i, patient in enumerate(patients_to_return):
        temp = {}
        for key in patient.keys():
            if key in to_select:
                temp[map[key]] = patient[key] if patient[key] else None

        patients_to_return[i] = temp

    fields_to_map = ["patient_sex", "ethnic_group"]
    session = SessionLocal()
    try:
        for patient in patients_to_return:
            for field in fields_to_map:
                value = patient.get(field)
                if value:
                    standardized_value = repo.SNOMED_value_mapping(session, value)

                    if standardized_value:
                        patient[field] = standardized_value

        return patients_to_return
    finally:
        session.close()


def get_patients_on_demand_on_id(collectionName, patient_id):
    to_select = ["PatientId", "PatientSex", "PatientAge", "EthnicGroup"]

    map = {
        "PatientId": "patient_id",
        "PatientSex": "patient_sex",
        "PatientAge": "patient_age",
        "EthnicGroup": "ethnic_group",
    }

    patient = repo.get_patients_on_demand_on_id(collectionName, patient_id)
    temp = {}
    for key in patient.keys():
        if key in to_select:
            temp[map[key]] = patient[key] if patient[key] else None

    patient = temp

    fields_to_map = ["patient_sex", "ethnic_group"]
    session = SessionLocal()
    try:
        for field in fields_to_map:
            value = patient.get(field)
            if value:
                standardized_value = repo.SNOMED_value_mapping(session, value)

                if standardized_value:
                    patient[field] = standardized_value

        return patient
    finally:
        session.close()


# SNOMED mapped fields retrieval


SERIES_DICOM_FIELD_ALIASES = {
    "SeriesInstanceUID": "series_instance_uid",
    "StudyInstanceUID_series": "study_instance_uid_series",
    "Modality": "modality",
    "BodyPartExamined": "body_part_examined",
    "ProtocolName": "protocol_name",
    "SeriesDate": "series_date",
    "SeriesDescription": "series_description",
    "Site": "site",
    "Manufacturer": "manufacturer",
    "ManufacturerModelName": "manufacturer_model_name",
    "SoftwareVersions": "software_versions",
    "ImageCount": "image_count",
    "MaxSubmissionTimestamp": "max_submission_timestamp",
    "FileSize": "file_size",
    "ThirdPartyAnalysis": "third_party_analysis",
    "CollectionName_study": "collection_name_study",
    "PatientID_study": "patient_id_study",
}

SERIES_DICOM_FIELD_LABELS = {
    "SeriesInstanceUID": "Identifier",
    "StudyInstanceUID_series": "Identifier of study",
    "Modality": "Imaging modality",
    "BodyPartExamined": "Body part",
    "ProtocolName": "Protocols",
    "SeriesDate": "Date",
    "SeriesDescription": "Description in dialect",
    "Site": "Healthcare facility",
    "Manufacturer": "Manufacturer",
    "ManufacturerModelName": "Device",
    "SoftwareVersions": "Software",
    "ImageCount": "Count of images",
    "MaxSubmissionTimestamp": "Timestamp",
    "FileSize": "File size bytes",
    "ThirdPartyAnalysis": "Third party analysis",
    "CollectionName_study": "Collection",
    "PatientID_study": "Patient",
}

STUDY_DICOM_FIELD_ALIASES = {
    "StudyInstanceUID": "study_instance_uid",
    "CollectionName_study": "collection_name_study",
    "StudyDate": "study_date",
    "DateReleased": "date_released",
    "StudyDescription": "study_description",
    "SeriesCount": "series_count",
    "PatientID_study": "patient_id_study",
    "LongitudinalTemporalEventType": "longitudinal_temporal_event_type",
    "LongitudinalTemporalOffsetFromEvent": "longitudinal_temporal_offset_from_event",
}

STUDY_DICOM_FIELD_LABELS = {
    "StudyInstanceUID": "Identifier",
    "CollectionName_study": "Collection",
    "StudyDate": "Date",
    "DateReleased": "Date of release",
    "StudyDescription": "Description in dialect",
    "SeriesCount": "Count of series",
    "PatientID_study": "Patient",
    "LongitudinalTemporalEventType": "Event",
    "LongitudinalTemporalOffsetFromEvent": "Relative time",
}

PATIENT_DICOM_FIELD_ALIASES = {
    "PatientID": "patient_id",
    "PatientId": "patient_id",
    "PatientSex": "patient_sex",
    "PatientAge": "patient_age",
    "EthnicGroup": "ethnic_group",
}

PATIENT_DICOM_FIELD_LABELS = {
    "PatientID": "Identifier",
    "PatientId": "Identifier",
    "PatientSex": "Gender",
    "PatientAge": "Age",
    "EthnicGroup": "Ethnic group",
}


def _get_dicom_field_mappings(field_aliases, fallback_labels):
    session = SessionLocal()
    field_mappings = {}
    try:
        mappings = dict(repo.get_SNOMED_fields(session))
        for dicom_field, database_field in field_aliases.items():
            field_mappings[dicom_field] = (
                mappings.get(database_field)
                or fallback_labels.get(dicom_field)
                or dicom_field
            )

        return field_mappings
    except Exception:
        return fallback_labels

    finally:
        session.close()


def get_series_SNOMED_fields():
    return _get_dicom_field_mappings(
        SERIES_DICOM_FIELD_ALIASES,
        SERIES_DICOM_FIELD_LABELS,
    )


def get_study_SNOMED_fields():
    return _get_dicom_field_mappings(
        STUDY_DICOM_FIELD_ALIASES,
        STUDY_DICOM_FIELD_LABELS,
    )


def get_patient_SNOMED_fields():
    return _get_dicom_field_mappings(
        PATIENT_DICOM_FIELD_ALIASES,
        PATIENT_DICOM_FIELD_LABELS,
    )
