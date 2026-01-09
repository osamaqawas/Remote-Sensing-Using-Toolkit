import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month):
    st.header(f"🔥 Active Wildfires Analysis - {country_name}")
    st.write(f"Monitoring thermal anomalies for **{month}/{year}**")

    # 1. Set Date Range
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')
    
    # 2. Fetch FIRMS Data (MODIS/VIIRS)
    # FIRMS provides Near Real-Time (NRT) active fire data
    fire_collection = ee.ImageCollection("FIRMS") \
        .filterDate(start_date, end_date) \
        .filterBounds(roi) \
        .select('T21') # Brightness temperature band in Kelvin

    # 3. Statistical Summary Section
    st.subheader("📊 Statistical Summary")
    
    # Get the number of fire detections
    fire_count = fire_collection.size().getInfo()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Detected Hotspots", f"{fire_count} points")
    
    if fire_count > 0:
        # Create a single composite image showing the maximum temperature for the month
        max_temp_img = fire_collection.max().clip(roi)
        
        # Calculate Max Temperature in the region
        stats = max_temp_img.reduceRegion(
            reducer=ee.Reducer.max(),
            geometry=roi,
            scale=1000,
            maxPixels=1e9
        ).getInfo()
        
        max_val = stats.get('T21')
        with col2:
            if max_val:
                st.metric("Max Brightness Temp", f"{max_val:.1f} K")
            else:
                st.metric("Max Brightness Temp", "N/A")

        # 4. Map Display Section
        m = geemap.Map()
        m.add_basemap("HYBRID")
        
        fire_vis = {
            'min': 300,
            'max': 500,
            'palette': ['yellow', 'orange', 'red']
        }
        
        m.addLayer(max_temp_img, fire_vis, "Active Fires")
        
        # Add Colorbar for reference
        m.add_colorbar(
            fire_vis, 
            label="Brightness Temp (Kelvin)", 
            orientation="horizontal",
            layer_name="Wildfires"
        )
        
        m.centerObject(roi, 6)
        folium_static(m, width=900)

        # 5. Optimized Data Export (GeoTIFF)
        st.subheader("📥 Export Data")
        try:
            # Use a larger scale (5000m) and bounds to avoid "Download size limit exceeded"
            download_url = max_temp_img.getDownloadURL({
                'name': f"Wildfire_{country_name}_{year}_{month}",
                'scale': 5000,  # 5km resolution for stable downloads
                'region': roi.geometry().bounds().getInfo()['coordinates'],
                'format': 'GEO_TIFF'
            })
            st.link_button("🚀 Download Fire Map as GeoTIFF", download_url)
            st.caption("Note: Resolution set to 5km to ensure successful download for large areas.")
        except Exception as e:
            st.info("The selected country is too large for direct download. Try a smaller time range or region.")

    else:
        st.warning(f"No active wildfires were detected in {country_name} during {month}/{year}.")
        # Show an empty map focused on the country
        m = geemap.Map()
        m.add_basemap("HYBRID")
        m.centerObject(roi, 6)
        folium_static(m, width=900)
