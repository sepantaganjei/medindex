# Role of the package:
# provide the functions needed to extract the data from TCIA

import requests
import os


# Main function. It returns the raw data from the archive.
# Input:
# - name of the collection
# - type of the dataset
# Output:
# - raw data of the entire dataset
def get_data_from_archive(collection_name, dataset_type):

    handlers = {
        "DICOM": _get_data_from_DICOM_archive,
        "NIFTI": _get_data_from_NIFTI_archive,
    }

    return handlers[dataset_type](collection_name)


# Helper function getting data from a DICOM dataset
# Input:
# - name of the collection
# Output:
# - data about collection, patients, studies, series in a dictionary
def _get_data_from_DICOM_archive(collection_name):
    URLS = {
        "collection": "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getCollectionDescriptions",
        "patients": "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getPatient",
        "studies": "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/NewStudiesInPatientCollection",
        "series": "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries",
    }

    PARAMS = {
        "collection": {"collectionName": collection_name},
        "patients": {"Collection": collection_name, "format": "json"},
        "studies": {
            "Collection": collection_name,
            "fromDate": "01-01-1960",
            "format": "json",
        },
        "series": {"Collection": collection_name, "format": "json"},
    }

    data = {key: _safe_get(URLS[key], PARAMS[key]).json() for key in URLS}
    return data


# Helper function to send a HTTP request in a safe way
# Input:
# - url
# - parameters of the request (like name of the colelction)
# Output:
# - return HTTP response
def _safe_get(url, params):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response


# Helper function getting data from a NIFTI dataset
# Input:
# - name of the collection
# Output:
# - data about collection, patients, studies, series in xlsx
def _get_data_from_NIFTI_archive(collection_name):
    root_path = collection_name
    target_name = collection_name.lower()
    for root, dirs, files in os.walk(root_path):
        for f in files:
            filename_no_ext, ext = os.path.splitext(f)
            # normalize
            filename_no_ext = filename_no_ext.strip().lower()
            if filename_no_ext == target_name and ext.lower() in [".csv", ".xlsx"]:
                return os.path.join(root, f)
    return None


# Get the zip associated with a DICOM series
def getZip(series_uid):
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getImage"
    params = {"SeriesInstanceUID": series_uid}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response


def getAllDICOMCollections():
    base_url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getCollectionDescriptions"
    response = requests.get(base_url, timeout=30)
    response.raise_for_status()
    return response.json()
