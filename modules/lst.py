import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month):
    st.header(f"🌡️ Land Surface Temperature (LST) – {country_name}")
    st.write(f"Observation period: **{month}/{year}**")

    # 1. Date range configuration
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')

    # 2. Load MODIS LST dataset (daily, 1 km resolution)
    dataset = (
        ee.ImageCollection('MODIS/061/MOD11A1')
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .select('LST_Day_1km')
    )

    if dataset.size().getInfo() == 0:
        st.warning("No Land Surface Temperature data available for the selected period.")
        return

    # 3. Convert LST from Kelvin to Celsius
    # Scale factor = 0.02, then subtract 273.15
    celsius_img = (
        dataset
        .map(lambda img: img.multiply(0.02).subtract(273.15))
        .mean()
        .clip(roi)
    )

    # 4. Visualization parameters
    vis_params = {
        'min': 10,
        'max': 50,
        'palette': ['blue', 'cyan', 'green', 'yellow', 'orange', 'red']
    }

    # 5. Map visualization
    m = geemap.Map()
    m.add_basemap("HYBRID")
    m.addLayer(celsius_img, vis_params, "Land Surface Temperature (°C)")
    m.add_colorbar(vis_params, label="Temperature (°C)")

    m.centerObject(roi, 6)
    folium_static(m, width=900)
