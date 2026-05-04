# Role of the package:
# provide the functions needed to access the data from TCIA

import requests
from pathlib import Path

def get_data_from_archive(collection_name, dataset_type):

    handlers = {
        "DICOM": get_data_from_DICOM_archive,
        "NIFTI": get_data_from_NIFTI_archive,
    }

    return handlers[dataset_type](collection_name)

def get_data_from_DICOM_archive(collection_name):
    URLS = {
        "collection": "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getCollectionDescriptions",
        "patients": "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getPatient",
        "studies": "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/NewStudiesInPatientCollection",
        "series": "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"
    }

    PARAMS = {
        "collection": {"collectionName": collection_name},
        "patients": {"Collection": collection_name, "format": "json"},
        "studies": {"Collection": collection_name, "fromDate": "01-01-1960", "format": "json"},
        "series": {"Collection": collection_name, "format": "json"},
    }

    data = {
        key: safe_get(URLS[key], PARAMS[key]).json() for key in URLS
    }
    return data

def safe_get(url, params):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response

def get_data_from_NIFTI_archive(collection_name):
    return Path(f"{collection_name}.xlsx")

# Get the zip associated with a DICOM series
def getZip(series_uid):
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getImage"
    params = {
        "SeriesInstanceUID" : series_uid
    }
    response = requests.get(url, params = params, timeout=30)
    response.raise_for_status()
    return response

