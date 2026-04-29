# Role of the package:
# provide the functions that are between the data storage and the frontend.
# They prepare the data to be presented in the interface.

import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import re
from data_access import *


def viewCollectionDescription(name_of_the_collection):
    response = getCollectionDescription(name_of_the_collection)
    # convert response to json
    description = response.json()

    # convert description to a readable format
    raw_html_text = description[0]["description"]
    soup = BeautifulSoup(raw_html_text, "html.parser")
    text = soup.get_text(separator="\n")

    text = text.replace("\n", ' ').replace("\t", ' ')
    text = re.sub(r"\s+", " ", text).strip()
    clean_text = re.sub(r"\.\s*", ".\n", text)

    description[0]['description'] = clean_text

    # print the descripiton of the collection
    st.write(f"Collection name: {description[0]['collectionName']}")
    st.write(f"Description ID: {description[0]['id']}")
    st.write(f"Description URI: {description[0]['descriptionURI']}")
    st.text(f"Description: {description[0]['description']}")


def viewPatientsData(name_of_the_collection):
    # Original patient data
    response = getPatientsData(name_of_the_collection)
    patient_df = pd.DataFrame(response.json())
    patient_df = patient_df.rename(columns={"PatientId": "PatientID"})

    # Data from study series
    response = getSeriesMetadataForEntireCollection(name_of_the_collection)
    series_metadata_df = pd.DataFrame(response.json())
    series_metadata_df = series_metadata_df.drop_duplicates(subset="PatientID").reset_index(drop=True)

    # Merge data from both sources
    full_patient_df = pd.merge(patient_df, series_metadata_df, on='PatientID', how="inner")
    # Reorder by patient id
    full_patient_df = full_patient_df.sort_values(by="PatientID").reset_index(drop=True)

    # Keep only relevant data
    columns_not_to_drop = ['PatientID',
                           'PatientSex_x',
                           'EthnicGroup',
                           'SpeciesDescription',
                           'PatientAge']
    full_patient_df = full_patient_df[columns_not_to_drop]
    full_patient_df = full_patient_df.rename(columns={'PatientSex_x': 'Sex'})
    full_patient_df = full_patient_df.fillna('Missing')

    st.dataframe(full_patient_df)


def viewSeriesMetadata(name_of_the_collection):
    response = getSeriesMetadataForEntireCollection(name_of_the_collection)

    try:
        data = response.json()
        series_metadata_df = pd.DataFrame(data)
        st.dataframe(series_metadata_df)

    except ValueError:
        st.error("Response is not valid JSON")
        st.text(response.text)