import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month):
    st.markdown(f"### 🌧️ Precipitation Analysis (ECMWF ERA5-Land)")

   
    date_string = f"{year}-{month:02d}-01"
    
    try:

        rainfall_img = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR") \
            .filterDate(date_string) \
            .select('total_precipitation_sum') \
            .first() \
            .clip(roi)

        
        total_rainfall_mm = rainfall_img.multiply(1000)

        
        stats = total_rainfall_mm.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.max(),
                sharedInputs=True
            ),
            geometry=roi,
            scale=11132,
            maxPixels=1e9
        ).getInfo()

        mean_val = stats.get('total_precipitation_sum_mean') or 0
        max_val = stats.get('total_precipitation_sum_max') or 0

        
        col1, col2 = st.columns(2)
        col1.metric("Average Rainfall", f"{mean_val:.2f} mm")
        col2.metric("Peak Rainfall", f"{max_val:.2f} mm")

    
        m = geemap.Map()
        m.add_basemap("TERRAIN")
        
        rain_vis = {
            'min': 0,
            'max': 100, 
            'palette': ['#f7fbff', '#6baed6', '#084594'] # تدرج أزرق احترافي
        }
        
        m.addLayer(total_rainfall_mm, rain_vis, "Precipitation (mm)")
        m.centerObject(roi, 8)
        folium_static(m, width=1000)

        return {
            "Module": "Rainfall (ERA5)",
            "Mean (mm)": f"{mean_val:.2f}",
            "Max (mm)": f"{max_val:.2f}"
        }

    except Exception as e:
        st.error(f"⚠️ Data not yet available for {month}/{year}. ERA5 usually has a short delay.")
        return {"Status": "Error"}
