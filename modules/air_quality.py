import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month, pollutant_choice):
    st.markdown(f"### 💨 Air Quality Intelligence: {pollutant_choice}")

    # Mapping pollutants to GEE datasets
    pollutant_map = {
        "NO2": ("COPERNICUS/S5P/OFFL/L3_NO2", "NO2_column_number_density"),
        "CO": ("COPERNICUS/S5P/OFFL/L3_CO", "CO_column_number_density"),
        "O3": ("COPERNICUS/S5P/OFFL/L3_O3", "O3_column_number_density"),
        "SO2": ("COPERNICUS/S5P/OFFL/L3_SO2", "SO2_column_number_density")
    }

    # Extract key
    key = "NO2"
    for k in pollutant_map.keys():
        if k in pollutant_choice:
            key = k
            break

    dataset_path, band_name = pollutant_map[key]

    # Time configuration
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')

    with st.spinner(f"🛰️ Processing Sentinel-5P data for {key}..."):
        # Load Collection
        collection = ee.ImageCollection(dataset_path) \
            .filterBounds(roi) \
            .filterDate(start_date, end_date) \
            .select(band_name)

        if collection.size().getInfo() == 0:
            st.warning(f"No satellite data found for {key} in the selected period.")
            return {"Status": "No Data Found"}

        # Generate Mean Image
        image = collection.mean().clip(roi)

        # --- SCIENTIFIC STATISTICS CALCULATION ---
        # Calculate Mean and Max concentration within the ROI
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.max(), sharedInputs=True
            ),
            geometry=roi,
            scale=1113.2, # Sentinel-5P spatial resolution
            maxPixels=1e9
        ).getInfo()

        mean_val = stats.get(f"{band_name}_mean")
        max_val = stats.get(f"{band_name}_max")
        
        # Format numbers for the report
        fmt_mean = f"{mean_val:.2e}" if mean_val else "N/A"
        fmt_max = f"{max_val:.2e}" if max_val else "N/A"

    # Visualization Parameters
    vis_params = {
        "NO2": {'min': 0, 'max': 0.0002, 'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']},
        "CO": {'min': 0, 'max': 0.05, 'palette': ['blue', 'cyan', 'green', 'yellow', 'red']},
        "O3": {'min': 0.1, 'max': 0.15, 'palette': ['blue', 'green', 'yellow', 'orange', 'red']}
    }.get(key, {'min': 0, 'max': 0.0002, 'palette': ['blue', 'red']})

    # Map Rendering
    m = geemap.Map()
    m.add_basemap("HYBRID")
    m.addLayer(image, vis_params, f"{key} Concentration")
    m.add_colorbar(vis_params, label=f"{key} Density (mol/m²)", orientation="horizontal")
    m.centerObject(roi, 10)

    st.markdown('<div style="border: 3px solid #2980B9; border-radius: 15px; overflow: hidden;">', unsafe_allow_html=True)
    folium_static(m, width=1000)
    st.markdown('</div>', unsafe_allow_html=True)

    st.success(f"Analysis complete for {country_name}. Temporal average calculated from Sentinel-5P L3 Offline products.")

    # --- RETURN DATA FOR PDF REPORT ---
    return {
        "Pollutant": key,
        "Mean Concentration": f"{fmt_mean} mol/m²",
        "Max Concentration": f"{fmt_max} mol/m²",
        "Data Source": "Copernicus Sentinel-5P",
        "Resolution": "1.1 km"
    }
