# Main program

from app.views import *
import streamlit as st

st.button(
    "View dataset description",
    on_click=lambda: viewCollectionDescription("CPTAC-LUAD")
)

st.button(
    "View patients data",
    on_click=lambda: viewPatientsData("CPTAC-LUAD")
)

st.button(
    "View series metadata", 
    on_click=lambda: viewSeriesMetadata("CPTAC-LUAD")
)

with st.form("download_series_form"):
    st.write("Insert the series id you are interested in downloading:")
    series_uid = st.text_input("Series ID") 
    submitted = st.form_submit_button("Download")

    if submitted:
        if not series_uid.strip():
            st.warning("Please enter a valid series ID.")
        else:
            try:
                with st.spinner("Downloading images..."):
                    getImageZip(series_uid)
                st.success("Download completed!")
            except Exception as e:
                st.error(f"An error as occurred: {e}")