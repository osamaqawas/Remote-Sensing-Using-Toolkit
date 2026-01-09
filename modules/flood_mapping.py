import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static
import pandas as pd

def run(country_name, roi, year, month):
    # --- Styled Header ---
    st.markdown(f"""
        <div style="background-color: #1F618D; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #2E86C1;">
            <h2 style="color: white; margin: 0;">🌊 Advanced Flood Intelligence</h2>
            <p style="color: #AED6F1; margin: 5px 0 0 0;">
                Territorial Risk & Satellite Observation for {country_name}
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")

    # 1. Date configuration
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')
    
    # 2. Radar processing (Sentinel-1 SAR)
    with st.spinner("🛰️ Processing Radar Satellite Data..."):
        s1_col = (
            ee.ImageCollection('COPERNICUS/S1_GRD')
            .filterBounds(roi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.eq('instrumentMode', 'IW'))
            .select('VV')
        )

        if s1_col.size().getInfo() == 0:
            st.warning(
                f"⚠️ No radar data found for {month}/{year}. "
                "Satellite coverage may be unavailable for this period."
            )
            return

        # Speckle reduction (Refined Lee filter approximation)
        after_img = s1_col.median().clip(roi)
        smoothed = after_img.focal_median(
            50, 'circle', 'meters'
        )  # Strong smoothing for mountainous regions

        # Flood water classification
        flood_mask = smoothed.lt(-17).rename('flood')
        actual_flood = flood_mask.updateMask(flood_mask)

    # 3. Topographic flood-risk modeling
    elevation = ee.Image("USGS/SRTMGL1_003").clip(roi)
    slope = ee.Terrain.slope(elevation)

    # Flood-prone areas: flat slopes and low-lying terrain (valleys)
    risk_zones = slope.lt(1.5).bitwiseAnd(elevation.lt(1200))
    prone_areas = risk_zones.updateMask(risk_zones)

    # 4. Interactive map visualization
    m = geemap.Map()
    m.add_basemap("HYBRID")

    # Add layers with balanced transparency
    m.addLayer(
        prone_areas,
        {'palette': '#FF4B4B', 'opacity': 0.4},
        "High-Risk Zones (Topography)"
    )
    m.addLayer(
        actual_flood,
        {'palette': '#00D4FF'},
        "Detected Surface Water (SAR)"
    )

    # Elegant legend
    m.add_legend(
        title="Legend",
        legend_dict={
            "Flood Risk Zone (Red)": "#FF4B4B",
            "Detected Flood (Neon Blue)": "#00D4FF"
        }
    )

    m.centerObject(roi, 11)

    st.markdown(
        '<div style="border: 3px solid #1F618D; border-radius: 15px; overflow: hidden;">',
        unsafe_allow_html=True
    )
    folium_static(m, width=1000)
    st.markdown('</div>', unsafe_allow_html=True)

    # 5. Summary metrics (Decision-support cards)
    st.markdown("---")
    st.markdown("### 📊 Decision Support Metrics")

    # Flooded area calculation
    stats = actual_flood.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=30,
        maxPixels=1e9
    ).getInfo()

    flooded_km2 = (stats.get('flood', 0) or 0) / 1e6

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
            <div style="background-color: #FDEDEC; padding: 20px; border-radius: 10px; border-left: 5px solid #E74C3C;">
                <h4 style="color: #E74C3C; margin: 0;">Submerged Area</h4>
                <h2 style="margin: 10px 0;">
                    {flooded_km2:.2f} <span style="font-size: 18px;">km²</span>
                </h2>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        risk_level = (
            "Critical" if flooded_km2 > 5
            else "Alert" if flooded_km2 > 1
            else "Stable"
        )
        st.markdown(f"""
            <div style="background-color: #FEF9E7; padding: 20px; border-radius: 10px; border-left: 5px solid #F1C40F;">
                <h4 style="color: #F1C40F; margin: 0;">Status Level</h4>
                <h2 style="margin: 10px 0;">{risk_level}</h2>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
            <div style="background-color: #EAFAF1; padding: 20px; border-radius: 10px; border-left: 5px solid #27AE60;">
                <h4 style="color: #27AE60; margin: 0;">Data Source</h4>
                <h2 style="margin: 10px 0;">Sentinel-1 SAR</h2>
            </div>
        """, unsafe_allow_html=True)

    # 6. Intelligent analysis & export section
    with st.expander("🔍 Deep Intelligence Analysis"):
        st.info(f"""
        **Satellite Insight:** Radar analysis detected **{flooded_km2:.2f} km²** of surface water.
        **Red Zones** represent topographic basins in {country_name} prone to water accumulation.
        Overlap between **Neon Blue** and **Red** confirms a high-confidence flood event
        within a known risk zone.
        """)

    # Export button
    export_bounds = roi.geometry().bounds().getInfo()['coordinates']
    try:
        url = actual_flood.getDownloadURL({
            'name': f"Flood_Analysis_{country_name}",
            'scale': 30,
            'region': export_bounds,
            'format': 'GEO_TIFF'
        })
        st.link_button("📥 Download Analytical GeoTIFF", url, use_container_width=True)
    except:
        st.error("Export exceeds size limits. Please zoom into a smaller area.")
