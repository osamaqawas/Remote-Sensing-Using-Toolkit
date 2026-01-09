import streamlit as st
import datetime
import os
import tempfile
import pandas as pd
from fpdf import FPDF
import plotly.io as pio

# استيراد أدوات المساعدة (تأكد من وجود مجلد utils)
from utils.helpers import authenticate_gee
from utils.geometry_utils import get_country_roi

# استيراد الموديولات (تأكد من وجود مجلد modules وملف __init__.py بداخله)
import modules.wildfire as wildfire
import modules.air_quality as air_quality
import modules.lst as lst
import modules.land_cover as land_cover
import modules.rs_indices as rs_indices
import modules.flood_mapping as flood_mapping
import modules.dem_analysis as dem_analysis
import modules.time_series as time_series

# --------------------------------------------------
# 1. محرك تقارير PDF الاحترافي
# --------------------------------------------------
class GeoSenseReport(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 16)
        self.set_text_color(26, 82, 118)
        self.cell(0, 10, "GEOSENSE-JORDAN: SCIENTIFIC ANALYTICAL REPORT", ln=True, align='C')
        self.set_draw_color(17, 122, 101)
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Researcher: Osama Al-Qawasmeh | Page {self.page_no()}", align='C')

def generate_pdf_report(city, year, month, analysis, stats_data, chart_path=None):
    pdf = GeoSenseReport()
    pdf.add_page()
    
    # المعلومات الأساسية
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. Executive Summary", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_fill_color(230, 240, 235)
    
    report_info = [
        ["Governorate", city],
        ["Observation Period", f"{month} {year}"],
        ["Analysis Module", analysis],
        ["Data Source", "Google Earth Engine / NASA / ESA"],
        ["Report Date", str(datetime.date.today())]
    ]
    
    for row in report_info:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(55, 8, row[0], border=1, fill=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, str(row[1]), border=1, ln=True)
    pdf.ln(10)

    # النتائج الإحصائية
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. Statistical Results", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(80, 8, "Indicator Metric", border=1, fill=True)
    pdf.cell(60, 8, "Value", border=1, fill=True, ln=True)
    
    pdf.set_font("Arial", '', 10)
    if isinstance(stats_data, dict) and stats_data:
        for key, value in stats_data.items():
            pdf.cell(80, 8, str(key), border=1)
            pdf.cell(60, 8, str(value), border=1, ln=True)
    else:
        pdf.cell(140, 8, "Detailed statistics available in dashboard view.", border=1, ln=True)

    # الرسوم البيانية (الصفحة الثانية)
    if chart_path and os.path.exists(chart_path):
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "3. Visual Analytics (Time Series Trend)", ln=True)
        pdf.image(chart_path, x=10, y=35, w=190)

    return pdf

# --------------------------------------------------
# 2. إعدادات التطبيق الرئيسية
# --------------------------------------------------
st.set_page_config(page_title="GeoSense-Jordan", page_icon="🇯🇴", layout="wide")

# تهيئة الذاكرة المؤقتة (Session State)
if 'data_captured' not in st.session_state:
    st.session_state.data_captured = False
if 'stats' not in st.session_state:
    st.session_state.stats = {}
if 'chart_img' not in st.session_state:
    st.session_state.chart_img = None

if authenticate_gee():
    # الشريط الجانبي (Sidebar)
    st.sidebar.title("🌍 Control Panel")
    jordan_governorates = ["Amman", "Irbid", "Zarqa", "Aqaba", "Madaba", "Mafraq", "Balqa", "Jerash", "Karak", "Ma'an", "Tafilah", "Ajloun"]
    target_city = st.sidebar.selectbox("Select Governorate:", jordan_governorates)
    selected_year = st.sidebar.slider("Year", 2018, 2026, 2025)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    selected_month_name = st.sidebar.select_slider("Month", options=month_names)
    selected_month = month_names.index(selected_month_name) + 1

    analysis_type = st.sidebar.selectbox("Module:", [
        "Terrain Analysis (DEM / Slope / Aspect)",
        "Flood Mapping & Risk (SAR)",
        "Spectral Indices & Environmental Metrics",
        "Air Quality Monitoring (Sentinel-5P)",
        "Land Surface Temperature (LST)",
        "Active Wildfires (FIRMS)",
        "Land Cover Classification"
    ])
    
    enable_ts = st.sidebar.checkbox("📉 Enable Time Series Analysis")

    # واجهة الترحيب
    roi = get_country_roi(target_city)
    st.markdown(f"""
        <div style="text-align: center; background: #1a5276; padding: 20px; border-radius: 15px; margin-bottom: 25px; border: 2px solid #17a2b8;">
            <h1 style="color: white; margin: 0;">GeoSense-Jordan</h1>
            <p style="color: #d1f2eb; font-size: 1.2em;">Researcher: Osama Al-Qawasmeh | Master's Thesis Project</p>
        </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # 3. تنفيذ التحليل
    # --------------------------------------------------
    if st.sidebar.button("🚀 Run Analysis"):
        with st.spinner(f"Processing {analysis_type} for {target_city}..."):
            try:
                # تصفير الحالة السابقة
                st.session_state.chart_img = None
                
                if analysis_type == "Terrain Analysis (DEM / Slope / Aspect)":
                    results = dem_analysis.run(target_city, roi, selected_year, selected_month)
                elif analysis_type == "Flood Mapping & Risk (SAR)":
                    results = flood_mapping.run(target_city, roi, selected_year, selected_month)
                elif analysis_type == "Spectral Indices & Environmental Metrics":
                    results = rs_indices.run(target_city, roi, selected_year, selected_month)
                elif analysis_type == "Air Quality Monitoring (Sentinel-5P)":
                    results = air_quality.run(target_city, roi, selected_year, selected_month, "NO2")
                elif analysis_type == "Land Surface Temperature (LST)":
                    results = lst.run(target_city, roi, selected_year, selected_month)
                elif analysis_type == "Active Wildfires (FIRMS)":
                    results = wildfire.run(target_city, roi, selected_year, selected_month)
                elif analysis_type == "Land Cover Classification":
                    results = land_cover.run(target_city, roi, selected_year, selected_month)
                
                st.session_state.stats = results
                st.session_state.data_captured = True
                st.success(f"Analysis for {target_city} completed successfully!")
                
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")

    # عرض النتائج والرسوم البيانية
    if st.session_state.data_captured:
        if enable_ts:
            st.markdown("---")
            # تعيين المعامل المناسب لموديول السلاسل الزمنية
            ts_mapping = {
                "Air Quality Monitoring (Sentinel-5P)": "Air Quality",
                "Land Surface Temperature (LST)": "Temp",
                "Spectral Indices & Environmental Metrics": "Vegetation"
            }
            ts_target = ts_mapping.get(analysis_type, "Vegetation")
            
            fig = time_series.run_analysis(ts_target, roi, selected_year)
            
            if fig:
                # حل مشكلة الـ Duplicate ID باستخدام مفتاح فريد
                chart_key = f"ts_chart_{target_city}_{selected_year}_{selected_month}"
                st.plotly_chart(fig, use_container_width=True, key=chart_key)
                
                # حفظ الصورة للتقرير
                temp_path = os.path.join(tempfile.gettempdir(), f"chart_{target_city}.png")
                try:
                    # استخدام pio لحفظ صورة plotly
                    fig.write_image(temp_path, engine="kaleido")
                    st.session_state.chart_img = temp_path
                except Exception as e:
                    st.warning("Install 'kaleido' to include charts in PDF reports.")

    # --------------------------------------------------
    # 4. استخراج التقارير
    # --------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Reporting Tools")
    
    if st.sidebar.button("Generate Scientific PDF"):
        if st.session_state.data_captured:
            with st.spinner("Generating PDF..."):
                pdf = generate_pdf_report(
                    target_city, 
                    selected_year, 
                    selected_month_name, 
                    analysis_type, 
                    st.session_state.stats,
                    st.session_state.chart_img
                )
                
                # تحويل الـ PDF إلى بايتات للتحميل
                pdf_bytes = pdf.output(dest='S').encode('latin-1', 'ignore')
                
                st.sidebar.download_button(
                    label="📥 Download Report",
                    data=pdf_bytes,
                    file_name=f"GeoSense_{target_city}_{selected_year}.pdf",
                    mime="application/pdf"
                )
        else:
            st.sidebar.error("Please run analysis first.")

else:
    st.error("Earth Engine Authentication Failed.")
