import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month, pollutant_choice):
    st.markdown(f"### 💨 Air Quality Analysis: {pollutant_choice}")

    # Dictionary mapping pollutant abbreviations to GEE datasets and band names
    pollutant_map = {
        "NO2": ("COPERNICUS/S5P/OFFL/L3_NO2", "NO2_column_number_density"),
        "CO": ("COPERNICUS/S5P/OFFL/L3_CO", "CO_column_number_density"),
        "O3": ("COPERNICUS/S5P/OFFL/L3_O3", "O3_column_number_density"),
        "SO2": ("COPERNICUS/S5P/OFFL/L3_SO2", "SO2_column_number_density")
    }

    # Check whether the input is an abbreviation or contains the abbreviation
    key = "NO2"  # Default value
    for k in pollutant_map.keys():
        if k in pollutant_choice:
            key = k
            break

    dataset_path, band_name = pollutant_map[key]

    # Set time range
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')

    with st.spinner(f"🛰️ Processing Sentinel-5P data for {key}..."):
        # Load Sentinel-5P data
        collection = ee.ImageCollection(dataset_path) \
            .filterBounds(roi) \
            .filterDate(start_date, end_date) \
            .select(band_name)

        if collection.size().getInfo() == 0:
            st.warning("No data found for the selected period.")
            return

        image = collection.mean().clip(roi)

    # Visualization parameters based on pollutant type
    vis_params = {
        "NO2": {
            'min': 0,
            'max': 0.0002,
            'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']
        },
        "CO": {
            'min': 0,
            'max': 0.05,
            'palette': ['blue', 'cyan', 'green', 'yellow', 'red']
        },
        "O3": {
            'min': 0.1,
            'max': 0.15,
            'palette': ['blue', 'green', 'yellow', 'orange', 'red']
        }
    }.get(key, {
        'min': 0,
        'max': 0.0002,
        'palette': ['blue', 'red']
    })

    # Create and display the map
    m = geemap.Map()
    m.add_basemap("HYBRID")
    m.addLayer(image, vis_params, f"{key} Concentration")
    m.add_colorbar(vis_params, label=f"{key} Density", orientation="horizontal")
    m.centerObject(roi, 10)

    st.markdown(
        '<div style="border: 3px solid #2980B9; border-radius: 15px; overflow: hidden;">',
        unsafe_allow_html=True
    )
    folium_static(m, width=1000)
    st.markdown('</div>', unsafe_allow_html=True)

    st.info(
        f"The analysis shows the average atmospheric concentration of {key} "
        f"over {country_name} for the selected month."
    )
