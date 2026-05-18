# Role of the package:
# View building. Here we build what the user sees.
# views = orchestration + display only. 
# Here we combine the orchestrated operations and the components made available by streamlit.

import streamlit as st
import app.etl.pipeline as pipe

# Add a new dataset
def add_dataset(collection_name, dataset_type):

    pipe.add_new_dataset(session, collection_name, dataset_type)


def some_functions():
    st.button(
        "View collection dataset",
        on_click=lambda: viewCollectionDataset()
    )

    st.button(
        "View study dataset",
        on_click=lambda: viewStudyDataset()
    )

    st.button(
        "View patient dataset",
        on_click=lambda: viewPatientDataset()
    )

    st.button(
        "View series dataset",
        on_click=lambda: viewSeriesDataset()
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
