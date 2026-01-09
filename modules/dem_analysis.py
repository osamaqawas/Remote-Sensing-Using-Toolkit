import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month):
    st.markdown(f"""
        <div style="background-color: #117A65; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #0E6251;">
            <h2 style="color: white; margin: 0;">🏔️ Terrain Intelligence Suite</h2>
            <p style="color: #A3E4D7; margin: 5px 0 0 0;">Precision Topography | {country_name}</p>
        </div>
    """, unsafe_allow_html=True)

    with st.spinner("🛰️ Calculating Terrain Parameters (Slope & Aspect)..."):
        try:
            # 1. Load raw DEM data
            dem_dataset = ee.ImageCollection("JAXA/ALOS/AW3D30/V3_2").select('DSM')
            full_dem = dem_dataset.mosaic()

            # 2. Reproject DEM to ensure slope calculation in meters
            # EPSG:3857 (Web Mercator) is used to preserve metric units
            projected_dem = full_dem.reproject(crs='EPSG:3857', scale=30)
            
            # 3. Compute terrain derivatives on projected DEM
            slope = ee.Terrain.slope(projected_dem).clip(roi)
            aspect = ee.Terrain.aspect(projected_dem).clip(roi)
            dem = full_dem.clip(roi)
            hillshade = ee.Terrain.hillshade(dem)
            
        except Exception as e:
            st.error(f"Processing error: {e}")
            return

    # Tabs for visualization
    tab1, tab2, tab3 = st.tabs(["📊 Elevation", "📉 Slope", "🧭 Aspect"])

    # Enhanced visualization parameters
    vis_dem = {
        'min': 400,
        'max': 1200,
        'palette': ['#313695', '#74add1', '#ffffbf', '#f46d43', '#a50026']
    }
    vis_slope = {
        'min': 0,
        'max': 30,
        'palette': ['#ffffff', '#f1c40f', '#e67e22', '#c0392b']
    }  # White = flat terrain, Red = steep slopes
    vis_aspect = {
        'min': 0,
        'max': 360,
        'palette': ['#e74c3c', '#f1c40f', '#2ecc71', '#3498db', '#e74c3c']
    }

    def render_map(image, vis, label, unit):
        m = geemap.Map()
        m.add_basemap("HYBRID")

        # Add hillshade as a base layer to enhance terrain relief
        m.addLayer(hillshade, {'min': 150, 'max': 255, 'opacity': 0.6}, "Terrain Relief", True)
        m.addLayer(image, vis, label)
        m.add_colorbar(vis, label=f"{label} ({unit})", orientation="horizontal")
        m.centerObject(roi, 11)

        st.markdown(
            '<div style="border: 3px solid #117A65; border-radius: 15px; overflow: hidden;">',
            unsafe_allow_html=True
        )
        folium_static(m, width=1000)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab1:
        st.write("### Digital Elevation Model (DSM)")
        render_map(dem, vis_dem, "Elevation", "m")

    with tab2:
        st.write("### Surface Slope (Inclination)")
        st.info("💡 Red areas represent steep slopes (>25 degrees).")
        render_map(slope, vis_slope, "Slope", "degrees")

    with tab3:
        st.write("### Terrain Aspect (Orientation)")
        st.info("💡 Displays slope orientation (North, East, South, West).")
        render_map(aspect, vis_aspect, "Aspect", "degrees")

    # Data download section
    st.markdown("---")
    try:
        url = dem.getDownloadURL({
            'name': 'DEM_Jordan',
            'scale': 30,
            'region': roi.geometry().bounds().getInfo()['coordinates']
        })
        st.link_button("📥 Download DEM as GeoTIFF", url, use_container_width=True)
    except:
        pass
