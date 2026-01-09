import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month):
    st.markdown(f"""
        <div style="background-color: #A04000; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #6E2C00;">
            <h2 style="color: white; margin: 0;">🔥 Active Wildfires & Thermal Anomalies</h2>
            <p style="color: #EDBB99; margin: 5px 0 0 0;">
                FIRMS NRT (MODIS/VIIRS) | Satellite Hotspot Monitoring | {country_name}
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Set Date Range
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')
    
    # 2. Fetch FIRMS Data
    # T21 is the Brightness Temperature of the fire pixel
    fire_collection = ee.ImageCollection("FIRMS") \
        .filterDate(start_date, end_date) \
        .filterBounds(roi) \
        .select('T21')

    # Get fire detection count
    fire_count = fire_collection.size().getInfo()
    
    # Pre-define variables for the return dictionary
    max_celsius = "N/A"
    
    # 3. Statistical Summary Section
    st.markdown("### 📊 Thermal Hotspot Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Detected Hotspots", f"{fire_count}")
    
    if fire_count > 0:
        # Create composite of maximum temperature
        max_temp_img = fire_collection.max().clip(roi)
        
        # Calculate Max Temperature in Kelvin and Convert to Celsius
        stats = max_temp_img.reduceRegion(
            reducer=ee.Reducer.max(),
            geometry=roi,
            scale=1000,
            maxPixels=1e9
        ).getInfo()
        
        max_k = stats.get('T21')
        if max_k:
            max_celsius = f"{(max_k - 273.15):.1f} °C"
        
        with col2:
            st.metric("Peak Fire Temp", max_celsius)
        with col3:
            st.metric("Sensor", "MODIS/VIIRS")

        # 4. Map Display
        m = geemap.Map()
        m.add_basemap("HYBRID")
        
        fire_vis = {
            'min': 300,
            'max': 500,
            'palette': ['#F1C40F', '#E67E22', '#C0392B'] # Yellow to Deep Red
        }
        
        m.addLayer(max_temp_img, fire_vis, "Active Fire Hotspots")
        m.add_colorbar(fire_vis, label="Brightness Temperature (Kelvin)", orientation="horizontal")
        m.centerObject(roi, 7)

        st.markdown('<div style="border: 3px solid #A04000; border-radius: 15px; overflow: hidden;">', unsafe_allow_html=True)
        folium_static(m, width=1000)
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.info(f"No significant thermal anomalies detected in {country_name} for {month}/{year}.")
        m = geemap.Map()
        m.add_basemap("HYBRID")
        m.centerObject(roi, 6)
        folium_static(m, width=1000)

    # --- RETURN DATA FOR PDF REPORT ---
    return {
        "Hotspot Count": f"{fire_count} detected points",
        "Peak Intensity": max_celsius,
        "Data Source": "NASA FIRMS (NRT)",
        "Monitoring Band": "T21 (Thermal Infrared)",
        "Status": "Active Monitoring"
    }
