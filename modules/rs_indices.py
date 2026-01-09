import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static
import pandas as pd

def run(country_name, roi, year, month):
    st.subheader(f"Remote Sensing Indices: {country_name} (Landsat 8/9)")
    
    # 1. Selection Tool
    index_choice = st.selectbox(
        "Select Spectral Index to Calculate:",
        ["NDVI (Vegetation Health)", "NDWI (Water Content)", "NDBI (Urban/Built-up)", "MNDWI (Open Water)"]
    )

    # 2. Data Preparation
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')

    # Correct Landsat 8 Collection 2 Scaling
    def apply_scale_factors(image):
        optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
        return image.addBands(optical_bands, None, True)

    def mask_landsat_clouds(image):
        qa = image.select('QA_PIXEL')
        # Bitmask for Clouds and Cloud Shadows
        mask = qa.bitwiseAnd(1 << 3).eq(0).bitwiseAnd(1 << 4).eq(0)
        return image.updateMask(mask)

    collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
        .filterBounds(roi) \
        .filterDate(start_date, end_date) \
        .map(mask_landsat_clouds) \
        .map(apply_scale_factors)

    if collection.size().getInfo() == 0:
        st.warning("No clear imagery found for this period. Expanding search to 6 months...")
        collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(roi) \
            .filterDate(start_date.advance(-6, 'month'), end_date) \
            .map(mask_landsat_clouds) \
            .map(apply_scale_factors)

    image = collection.median().clip(roi)

    # 3. Corrected Calculations & Visualization
    # Green (#008000) = High/Good, Red (#FF0000) = Low/Poor
    std_palette = ['#FF0000', '#FFFF00', '#008000'] 

    if index_choice == "NDVI (Vegetation Health)":
        # (NIR - RED) / (NIR + RED)
        result = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
        vis_params = {'min': -0.1, 'max': 0.6, 'palette': std_palette}
        
    elif index_choice == "NDWI (Water Content)":
        # (NIR - SWIR1) / (NIR + SWIR1) - Best for vegetation water stress
        result = image.normalizedDifference(['SR_B5', 'SR_B6']).rename('NDWI')
        vis_params = {'min': -0.5, 'max': 0.5, 'palette': std_palette}
        
    elif index_choice == "NDBI (Urban/Built-up)":
        # (SWIR1 - NIR) / (SWIR1 + NIR)
        result = image.normalizedDifference(['SR_B6', 'SR_B5']).rename('NDBI')
        vis_params = {'min': -0.3, 'max': 0.3, 'palette': std_palette}
        
    elif index_choice == "MNDWI (Open Water)":
        # (GREEN - SWIR1) / (GREEN + SWIR1) - Best for identifying surface water
        result = image.normalizedDifference(['SR_B3', 'SR_B6']).rename('MNDWI')
        vis_params = {'min': -0.6, 'max': 0.2, 'palette': std_palette}

    # --- MAP SECTION ---
    m = geemap.Map()
    m.add_basemap("SATELLITE")
    
    # Landsat 8 RGB Visualization
    rgb_vis = {'bands': ['SR_B4', 'SR_B3', 'SR_B2'], 'min': 0, 'max': 0.3}
    m.addLayer(image, rgb_vis, "Landsat 8 Natural Color")
    
    m.addLayer(result, vis_params, index_choice)
    m.add_colorbar(vis_params, label=f"{index_choice} (Red=Low, Green=High)", orientation="horizontal")
    
    m.centerObject(roi, 10) # Zoomed in more for Cities
    folium_static(m, width=900)

    # --- STATISTICS SECTION ---
    st.markdown("---")
    st.markdown(f"### 📊 {index_choice} Statistical Distribution")
    
    with st.spinner("Analyzing spectral frequency..."):
        try:
            # Use a slightly lower scale for better precision in cities
            hist = result.reduceRegion(
                reducer=ee.Reducer.histogram(40),
                geometry=roi,
                scale=100,
                maxPixels=1e9
            ).getInfo()
            
            b_name = list(hist.keys())[0]
            df_hist = pd.DataFrame({
                'Value': hist[b_name]['bucketMeans'],
                'Frequency': hist[b_name]['histogram']
            })
            st.area_chart(df_hist.set_index('Value'))
            st.caption("X-axis: Index Value | Y-axis: Pixel Count")
        except:
            st.info("Histogram could not be generated for this specific area/scale.")

    # 4. Export Section
    st.markdown("### 📥 Data Export")
    try:
        url = result.getDownloadURL({
            'name': f"{index_choice[:4]}_{country_name}",
            'scale': 30,
            'region': roi.geometry().bounds().getInfo()['coordinates'],
            'format': 'GEO_TIFF'
        })
        st.link_button(f"Download {index_choice[:5]} GeoTIFF (30m Resolution)", url)
    except:
        st.error("Region too large for direct download.")
