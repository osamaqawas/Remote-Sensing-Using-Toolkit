import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static
import pandas as pd

def run(country_name, roi, year, month):
    st.markdown(f"""
        <div style="background-color: #1D8348; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #145A32;">
            <h2 style="color: white; margin: 0;">🛰️ Multi-Spectral Environmental Indices</h2>
            <p style="color: #D4EFDF; margin: 5px 0 0 0;">
                Landsat 8-9 OLI/TIRS | 30m Resolution | {country_name}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # 1. Selection Tool
    index_choice = st.selectbox(
        "Select Spectral Index to Calculate:",
        ["NDVI (Vegetation Health)", "NDWI (Water Content)", "NDBI (Urban/Built-up)", "MNDWI (Open Water)"]
    )

    # 2. Data Preparation
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')

    def apply_scale_factors(image):
        optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
        return image.addBands(optical_bands, None, True)

    def mask_landsat_clouds(image):
        qa = image.select('QA_PIXEL')
        mask = qa.bitwiseAnd(1 << 3).eq(0).bitwiseAnd(1 << 4).eq(0)
        return image.updateMask(mask)

    with st.spinner("🛰️ Harmonizing Landsat Surface Reflectance Data..."):
        collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(roi) \
            .filterDate(start_date, end_date) \
            .map(mask_landsat_clouds) \
            .map(apply_scale_factors)

        if collection.size().getInfo() == 0:
            st.info("Expanding search window to capture cloud-free pixels...")
            collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
                .filterBounds(roi) \
                .filterDate(start_date.advance(-6, 'month'), end_date) \
                .map(mask_landsat_clouds) \
                .map(apply_scale_factors)

        image = collection.median().clip(roi)

    # 3. Spectral Calculations
    # Green = High, Red = Low
    std_palette = ['#FF0000', '#FFFF00', '#008000'] 

    if "NDVI" in index_choice:
        result = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('Index')
        vis_params = {'min': -0.1, 'max': 0.7, 'palette': std_palette}
    elif "NDWI" in index_choice and "MNDWI" not in index_choice:
        result = image.normalizedDifference(['SR_B5', 'SR_B6']).rename('Index')
        vis_params = {'min': -0.5, 'max': 0.5, 'palette': ['brown', 'white', 'blue']}
    elif "NDBI" in index_choice:
        result = image.normalizedDifference(['SR_B6', 'SR_B5']).rename('Index')
        vis_params = {'min': -0.3, 'max': 0.3, 'palette': ['green', 'white', 'red']}
    else: # MNDWI
        result = image.normalizedDifference(['SR_B3', 'SR_B6']).rename('Index')
        vis_params = {'min': -0.6, 'max': 0.2, 'palette': ['white', 'blue']}

    # --- SCIENTIFIC STATS ---
    stats = result.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True),
        geometry=roi,
        scale=30,
        maxPixels=1e9
    ).getInfo()

    mean_val = stats.get('Index_mean', 0)
    max_val = stats.get('Index_max', 0)

    # --- MAP DISPLAY ---
    m = geemap.Map()
    m.add_basemap("SATELLITE")
    m.addLayer(image, {'bands': ['SR_B4', 'SR_B3', 'SR_B2'], 'min': 0, 'max': 0.3}, "Natural Color")
    m.addLayer(result, vis_params, index_choice)
    m.add_colorbar(vis_params, label=f"Calculated {index_choice}", orientation="horizontal")
    m.centerObject(roi, 11)
    
    st.markdown('<div style="border: 3px solid #1D8348; border-radius: 15px; overflow: hidden;">', unsafe_allow_html=True)
    folium_static(m, width=1000)
    st.markdown('</div>', unsafe_allow_html=True)

    # Statistics UI
    st.markdown(f"### 📊 Analysis: {index_choice}")
    c1, c2 = st.columns(2)
    c1.metric("Mean Index Value", f"{mean_val:.3f}")
    c2.metric("Maximum Peak", f"{max_val:.3f}")

    

    # --- RETURN FOR REPORT ---
    return {
        "Selected Index": index_choice.split(" (")[0],
        "Mean Value": f"{mean_val:.4f}",
        "Maximum Value": f"{max_val:.4f}",
        "Satellite": "Landsat 8-9 OLI",
        "Spatial Resolution": "30 meters",
        "Atmospheric Correction": "LaSRC (Level 2)"
    }
