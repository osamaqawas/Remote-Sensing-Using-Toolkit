import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month):
    # --- Professional Header ---
    st.markdown(f"""
        <div style="background-color: #1F618D; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #2E86C1;">
            <h2 style="color: white; margin: 0;">🌊 Advanced Flood Intelligence</h2>
            <p style="color: #AED6F1; margin: 5px 0 0 0;">
                SAR Satellite Observation & Risk Modeling | {country_name}
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")

    # 1. Date configuration
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')
    
    # 2. Radar processing (Sentinel-1 SAR)
    with st.spinner("🛰️ Analyzing Radar Backscatter Coefficients..."):
        s1_col = (
            ee.ImageCollection('COPERNICUS/S1_GRD')
            .filterBounds(roi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.eq('instrumentMode', 'IW'))
            .select('VV')
        )

        if s1_col.size().getInfo() == 0:
            st.warning(f"⚠️ No radar data found for {month}/{year}.")
            return {"Status": "No Satellite Coverage"}

        # Speckle reduction and median composite
        after_img = s1_col.median().clip(roi)
        smoothed = after_img.focal_median(50, 'circle', 'meters') 

        # Flood water classification (Thresholding technique)
        flood_mask = smoothed.lt(-17).rename('flood')
        actual_flood = flood_mask.updateMask(flood_mask)

    # 3. Topographic modeling (SRTM)
    elevation = ee.Image("USGS/SRTMGL1_003").clip(roi)
    slope = ee.Terrain.slope(elevation)
    risk_zones = slope.lt(1.5).bitwiseAnd(elevation.lt(1200))
    prone_areas = risk_zones.updateMask(risk_zones)

    # 4. Map visualization
    m = geemap.Map()
    m.add_basemap("HYBRID")
    m.addLayer(prone_areas, {'palette': '#FF4B4B', 'opacity': 0.4}, "High-Risk Topography")
    m.addLayer(actual_flood, {'palette': '#00D4FF'}, "Satellite Detected Water")
    m.add_legend(title="Risk Legend", legend_dict={
        "Flood Prone (Topography)": "#FF4B4B",
        "Detected Flood (SAR)": "#00D4FF"
    })
    m.centerObject(roi, 11)

    st.markdown('<div style="border: 3px solid #1F618D; border-radius: 15px; overflow: hidden;">', unsafe_allow_html=True)
    folium_static(m, width=1000)
    st.markdown('</div>', unsafe_allow_html=True)

    # 5. Summary Metrics
    st.markdown("### 📊 Quantitative Metrics")

    # Area calculation
    stats = actual_flood.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=30,
        maxPixels=1e9
    ).getInfo()

    flooded_km2 = (stats.get('flood', 0) or 0) / 1e6
    risk_level = "Critical" if flooded_km2 > 5 else "Alert" if flooded_km2 > 1 else "Stable"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Submerged Area", f"{flooded_km2:.2f} km²")
    with c2:
        st.metric("Risk Status", risk_level)
    with c3:
        st.metric("Sensor", "Sentinel-1 SAR")

    st.success(f"Analysis complete. Radar signals used to detect surface water regardless of cloud cover.")

    # --- RETURN DATA FOR PDF REPORT ---
    return {
        "Submerged Area": f"{flooded_km2:.2f} sq km",
        "Hazard Level": risk_level,
        "Detection Method": "SAR Backscatter Thresholding",
        "Satellite Platform": "Sentinel-1 (VV)",
        "Topographic Risk": "Integrated SRTM Elevation"
    }
