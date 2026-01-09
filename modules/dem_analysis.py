import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month):
    st.markdown(f"""
        <div style="background-color: #117A65; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #0E6251;">
            <h2 style="color: white; margin: 0;">🏔️ Terrain Intelligence Suite</h2>
            <p style="color: #A3E4D7; margin: 5px 0 0 0;">Topographic Characterization | {country_name}</p>
        </div>
    """, unsafe_allow_html=True)

    with st.spinner("🛰️ Extracting Geomorphometric Parameters..."):
        try:
            # 1. Load ALOS AW3D30 DEM
            dem_dataset = ee.ImageCollection("JAXA/ALOS/AW3D30/V3_2").select('DSM')
            full_dem = dem_dataset.mosaic()

            # 2. Metric Projection for accurate slope calculation
            projected_dem = full_dem.reproject(crs='EPSG:3857', scale=30)
            
            # 3. Terrain Derivatives
            slope = ee.Terrain.slope(projected_dem).clip(roi)
            aspect = ee.Terrain.aspect(projected_dem).clip(roi)
            dem = full_dem.clip(roi)
            hillshade = ee.Terrain.hillshade(dem)

            # --- QUANTITATIVE ANALYSIS ---
            # Calculate Elevation and Slope Statistics
            elev_stats = dem.reduceRegion(
                reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            ).getInfo()

            slope_stats = slope.reduceRegion(
                reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            ).getInfo()

            # Formatting results
            mean_elev = f"{elev_stats.get('DSM_mean', 0):.1f} m"
            max_elev = f"{elev_stats.get('DSM_max', 0):.1f} m"
            min_elev = f"{elev_stats.get('DSM_min', 0):.1f} m"
            mean_slope = f"{slope_stats.get('slope_mean', 0):.1f}°"
            max_slope = f"{slope_stats.get('slope_max', 0):.1f}°"
            
        except Exception as e:
            st.error(f"Geospatial Processing Error: {e}")
            return {"Status": "Error"}

    # Visualization Setup
    tab1, tab2, tab3 = st.tabs(["📊 Elevation", "📉 Slope", "🧭 Aspect"])

    vis_dem = {'min': 400, 'max': 1200, 'palette': ['#313695', '#74add1', '#ffffbf', '#f46d43', '#a50026']}
    vis_slope = {'min': 0, 'max': 30, 'palette': ['#ffffff', '#f1c40f', '#e67e22', '#c0392b']}
    vis_aspect = {'min': 0, 'max': 360, 'palette': ['#e74c3c', '#f1c40f', '#2ecc71', '#3498db', '#e74c3c']}

    def render_map(image, vis, label, unit):
        m = geemap.Map()
        m.add_basemap("HYBRID")
        m.addLayer(hillshade, {'min': 150, 'max': 255, 'opacity': 0.6}, "Hillshade Relief", True)
        m.addLayer(image, vis, label)
        m.add_colorbar(vis, label=f"{label} ({unit})", orientation="horizontal")
        m.centerObject(roi, 11)
        
        st.markdown('<div style="border: 3px solid #117A65; border-radius: 15px; overflow: hidden;">', unsafe_allow_html=True)
        folium_static(m, width=1000)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab1:
        st.markdown(f"#### Digital Elevation Model (DSM)")
        st.write(f"Region spans from **{min_elev}** to **{max_elev}** above sea level.")
        render_map(dem, vis_dem, "Elevation", "m")

    with tab2:
        st.markdown("#### Surface Slope Analysis")
        st.info(f"The average slope in this ROI is {mean_slope}. Steeper slopes increase erosion risk.")
        render_map(slope, vis_slope, "Slope", "degrees")

    with tab3:
        st.markdown("#### Terrain Aspect (Orientation)")
        render_map(aspect, vis_aspect, "Aspect", "degrees")

    # Final Footer and Return for Report
    st.markdown("---")
    st.success(f"Terrain analysis for {country_name} generated using ALOS World 3D (30m resolution).")
    
    

    return {
        "Mean Elevation": mean_elev,
        "Max Elevation": max_elev,
        "Min Elevation": min_elev,
        "Mean Slope": mean_slope,
        "Max Slope": max_slope,
        "DEM Source": "JAXA ALOS AW3D30"
    }
