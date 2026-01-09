import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static

def run(country_name, roi, year, month):
    st.markdown(f"""
        <div style="background-color: #154360; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #1A5276;">
            <h2 style="color: white; margin: 0;">🌧️ Precipitation Analysis (NASA GPM)</h2>
            <p style="color: #AED6F1; margin: 5px 0 0 0;">Global Precipitation Measurement | {country_name} | {month}/{year}</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. تحديد التواريخ
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')

    # 2. جلب بيانات الأمطار من NASA GPM
    # نستخدم 'precipitationCal' وهو معدل هطول الأمطار (ملم/ساعة)
    rainfall_coll = ee.ImageCollection("NASA/GPM_L3/IMERG_V06") \
        .filterDate(start_date, end_date) \
        .select('precipitationCal')

    # حساب مجموع الأمطار التراكمي للشهر (ملم)
    # ملاحظة: البيانات تأتي كل 30 دقيقة، لذا نضرب في 0.5 لتحويل المعدل إلى كمية تراكمية
    total_rainfall = rainfall_coll.reduce(ee.Reducer.sum()).multiply(0.5).clip(roi)

    # 3. الإحصائيات
    stats = total_rainfall.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=True),
        geometry=roi,
        scale=10000, # دقة GPM هي حوالي 10كم
        maxPixels=1e9
    ).getInfo()

    mean_rain = stats.get('precipitationCal_sum_mean', 0)
    max_rain = stats.get('precipitationCal_sum_max', 0)

    st.markdown("### 📊 Rainfall Statistics")
    c1, c2 = st.columns(2)
    c1.metric("Average Monthly Rainfall", f"{mean_rain:.2f} mm")
    c2.metric("Maximum Recorded Rainfall", f"{max_rain:.2f} mm")

    # 4. العرض على الخريطة
    m = geemap.Map()
    m.add_basemap("TERRAIN")
    
    # لوحة ألوان الأمطار (من الأبيض للأزرق الغامق)
    rain_vis = {
        'min': 0,
        'max': 100,
        'palette': ['#FFFFFF', '#AED6F1', '#3498DB', '#2E86C1', '#1B4F72']
    }
    
    m.addLayer(total_rainfall, rain_vis, "Total Monthly Rainfall")
    m.add_colorbar(rain_vis, label="Total Rainfall (mm)", orientation="horizontal")
    m.centerObject(roi, 7)
    
    folium_static(m, width=1000)

    # 5. البيانات للتقرير
    return {
        "Analysis Type": "Precipitation (GPM)",
        "Average Rainfall": f"{mean_rain:.2f} mm",
        "Max Rainfall": f"{max_rain:.2f} mm",
        "Sensor": "NASA GPM IMERG V06",
        "Resolution": "0.1 degrees (~11km)"
    }
