import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month):
    st.markdown("### 🌧️ Precipitation Analysis (NASA GPM)")

    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')

    # 1. Get the collection
    rainfall_coll = ee.ImageCollection("NASA/GPM_L3/IMERG_V06") \
        .filterDate(start_date, end_date) \
        .select('precipitationCal')

    # 2. Check if the collection is empty to avoid the "0 bands" error
    count = rainfall_coll.size().getInfo()
    
    if count == 0:
        st.warning(f"⚠️ No rainfall data available for {month}/{year} yet. NASA GPM usually has a 3-month latency for final products.")
        return {"Status": "No data available", "Month": month, "Year": year}

    # 3. Process only if data exists
    total_rainfall = rainfall_coll.reduce(ee.Reducer.sum()).multiply(0.5).clip(roi)

    # Statistics
    stats = total_rainfall.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
        geometry=roi,
        scale=10000,
        maxPixels=1e9
    ).getInfo()

    # Handle potential None values in stats
    mean_rain = stats.get('precipitationCal_sum_mean') or 0
    max_rain = stats.get('precipitationCal_sum_max') or 0

    st.metric("Average Monthly Rainfall", f"{mean_rain:.2f} mm")
    
    # Map display
    m = geemap.Map()
    m.addLayer(total_rainfall, {'min': 0, 'max': 100, 'palette': ['white', 'blue']}, "Rainfall")
    folium_static(m)

    return {"Average Rainfall": f"{mean_rain:.2f} mm", "Max Rainfall": f"{max_rain:.2f} mm"}
