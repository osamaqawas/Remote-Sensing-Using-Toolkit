import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month):
    st.markdown(f"""
        <div style="background-color: #1a5276; padding: 15px; border-radius: 10px; border-left: 5px solid #5dade2;">
            <h3 style="color: white; margin: 0;">🌧️ Precipitation Analysis (ECMWF ERA5-Land)</h3>
            <p style="color: #d1f2eb; margin: 5px 0 0 0;">Climate Reanalysis Data | {country_name} | {month}/{year}</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. تحديد التواريخ
    # ERA5 Monthly متوفر عادة حتى الشهر الماضي (Latency أقل من GPM)
    date_string = f"{year}-{month:02d}-01"
    
    try:
        # 2. جلب بيانات ERA5-Land Monthly
        # نستخدم 'total_precipitation' وهي تراكمي شهري بالمتر
        rainfall_img = ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR") \
            .filterDate(date_string) \
            .select('total_precipitation') \
            .first() \
            .clip(roi)

        # تحويل من متر (m) إلى مليمتر (mm)
        total_rainfall_mm = rainfall_img.multiply(1000)

        # 3. حساب الإحصائيات الإقليمية
        stats = total_rainfall_mm.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.max(),
                sharedInputs=True
            ),
            geometry=roi,
            scale=11132, # دقة ERA5-Land هي 0.1 arc degree
            maxPixels=1e9
        ).getInfo()

        mean_val = stats.get('total_precipitation_mean') or 0
        max_val = stats.get('total_precipitation_max') or 0

        # 4. عرض المقاييس (Metrics)
        st.write("")
        col1, col2, col3 = st.columns(3)
        col1.metric("Average Rainfall", f"{mean_val:.2f} mm")
        col2.metric("Peak Rainfall", f"{max_val:.2f} mm")
        col3.metric("Data Source", "ERA5-Land")

        # 5. عرض الخريطة التفاعلية
        st.markdown("#### 🗺️ Spatial Distribution Map")
        m = geemap.Map()
        m.add_basemap("TERRAIN")
        
        rain_vis = {
            'min': 0,
            'max': 150, # يمكن تعديله حسب طبيعة المنطقة
            'palette': ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#084594']
        }
        
        m.addLayer(total_rainfall_mm, rain_vis, "Monthly Precipitation (mm)")
        m.add_colorbar(rain_vis, label="Precipitation (mm)", orientation="horizontal")
        m.centerObject(roi, 8)
        
        folium_static(m, width=1000)

        # 6. تجهيز البيانات للتقرير PDF
        return {
            "Module": "Precipitation Analysis",
            "Mean Monthly Rainfall": f"{mean_val:.2f} mm",
            "Max Monthly Rainfall": f"{max_val:.2f} mm",
            "Data Source": "ECMWF ERA5-Land Reanalysis",
            "Spatial Resolution": "11km (0.1°)"
        }

    except Exception as e:
        st.error(f"⚠️ Error accessing ERA5 data for this date: {e}")
        st.info("Note: Monthly reanalysis data might have a 1-2 month delay from the current date.")
        return {"Status": "Error", "Message": str(e)}
