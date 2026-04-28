# Role of the package:
# provide the functions needed to access the data from the DICOM repo

import requests

# Patient → Study → Series → Images

# What would a researcher want to see?

# simple statistics about the patients, and selection criteria with associated values
# ability to requests series based on selection criteria
# perform series query once the series id has been selected
# download the series with those criteria

def getCollectionDescription(name_of_the_collection):
    # specify endpoint
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getCollectionDescriptions"

    # specify parameters of request
    params = {
        "collectionName": name_of_the_collection
    }

    # store response
    response = requests.get(url, params = params)
    return response

def getPatientsData(name_of_the_collection):
    endpoint = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getPatient"
    params = {
        "Collection" : name_of_the_collection,
        "format" : "json"
    }
    response = requests.get(endpoint, params = params)
    return response

def getSeriesMetadataForEntireCollection(name_of_the_collection):
    url = "https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getSeries"

    params = {
        "Collection": name_of_the_collection,
        "format": "json"
    }

    response = requests.get(url, params=params)
    return response

def getImageZip(series_uid):
    url = f"https://nbia.cancerimagingarchive.net/nbia-api/services/v4/getImage?SeriesInstanceUID={series_uid}"

    response = requests.get(url)

    if response.status_code == 200:
        with open(f"{series_uid}.zip", "wb") as f:
            f.write(response.content)
        print("Downloaded images.zip")
    else:
        print("Error: ", response.text)

