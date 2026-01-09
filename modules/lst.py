import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month):
    st.markdown(f"""
        <div style="background-color: #CB4335; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #943126;">
            <h2 style="color: white; margin: 0;">🌡️ Thermal Intelligence: Land Surface Temperature</h2>
            <p style="color: #F5B7B1; margin: 5px 0 0 0;">
                MODIS Terra Satellite | 1km Spatial Resolution | {country_name}
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Date range configuration
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')

    with st.spinner("🛰️ Retrieving MODIS Daily Thermal Composites..."):
        # 2. Load MODIS LST dataset
        dataset = (
            ee.ImageCollection('MODIS/061/MOD11A1')
            .filterBounds(roi)
            .filterDate(start_date, end_date)
            .select('LST_Day_1km')
        )

        if dataset.size().getInfo() == 0:
            st.warning("No thermal data found for the selected period.")
            return {"Status": "No Data Found"}

        # 3. Radiometric Calibration (Kelvin to Celsius)
        # Formula: (DN * 0.02) - 273.15
        lst_celsius = (
            dataset
            .map(lambda img: img.multiply(0.02).subtract(273.15))
            .mean()
            .clip(roi)
        )

        # 4. Thermal Statistics Calculation
        stats = lst_celsius.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.minMax(), sharedInputs=True
            ),
            geometry=roi,
            scale=1000,
            maxPixels=1e9
        ).getInfo()

        mean_temp = stats.get('LST_Day_1km_mean')
        max_temp = stats.get('LST_Day_1km_max')
        min_temp = stats.get('LST_Day_1km_min')

    # 5. Visualization setup
    vis_params = {
        'min': 15,
        'max': 45,
        'palette': ['#313695', '#4575b4', '#abd9e9', '#ffffbf', '#fdae61', '#f46d43', '#d73027']
    }

    # 6. Dashboard Metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Average LST", f"{mean_temp:.1f} °C")
    with c2:
        st.metric("Maximum Intensity", f"{max_temp:.1f} °C")
    with c3:
        st.metric("Sensor Source", "MOD11A1.061")

    # 7. Map Rendering
    m = geemap.Map()
    m.add_basemap("HYBRID")
    m.addLayer(lst_celsius, vis_params, "Surface Temperature (°C)")
    m.add_colorbar(vis_params, label="LST (Celsius)", orientation="horizontal")
    m.centerObject(roi, 7)

    st.markdown('<div style="border: 3px solid #CB4335; border-radius: 15px; overflow: hidden;">', unsafe_allow_html=True)
    folium_static(m, width=1000)
    st.markdown('</div>', unsafe_allow_html=True)

    st.success(f"Thermal analysis for {country_name} finalized using MODIS Terra Daily Day-time LST.")

    # --- RETURN DATA FOR PDF REPORT ---
    return {
        "Mean Surface Temp": f"{mean_temp:.2f} C",
        "Max Surface Temp": f"{max_temp:.2f} C",
        "Min Surface Temp": f"{min_temp:.2f} C",
        "Satellite Platform": "MODIS Terra",
        "Spatial Resolution": "1,000 meters",
        "Correction Method": "Radiometric Scaling (Kelvin-Celsius)"
    }
