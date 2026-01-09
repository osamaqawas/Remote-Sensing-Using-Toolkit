import streamlit as st
import datetime
import os
import tempfile
from fpdf import FPDF
from utils.helpers import authenticate_gee
from utils.geometry_utils import get_country_roi

# Import analysis modules
import modules.wildfire as wildfire
import modules.air_quality as air_quality
import modules.lst as lst
import modules.land_cover as land_cover
import modules.rs_indices as rs_indices
import modules.flood_mapping as flood_mapping
import modules.dem_analysis as dem_analysis
import modules.time_series as time_series

# --------------------------------------------------
# 1. Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="GeoSense-Jordan | Osama Al-Qawasmeh",
    page_icon="🇯🇴",
    layout="wide"
)

# --------------------------------------------------
# 2. PDF Report Generator Class (العلمي والمنظم)
# --------------------------------------------------
class ScientificReport(FPDF):
    def header(self):
        # إضافة شعار بسيط أو عنوان في الهيدر
        self.set_font("Arial", 'B', 15)
        self.set_text_color(26, 82, 118)
        self.cell(0, 10, "GEOSENSE-JORDAN: GEOSPATIAL INTELLIGENCE REPORT", ln=True, align='C')
        self.set_draw_color(17, 122, 101)
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()} | Prepared by Researcher: Osama Al-Qawasmeh", align='C')

def create_pdf_report(city, year, month, analysis_name):
    pdf = ScientificReport()
    pdf.add_page()
    
    # معلومات التقرير
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 0, 0)
    
    data_info = [
        ["Governorate Target", city],
        ["Observation Year", str(year)],
        ["Observation Month", month],
        ["Analysis Module", analysis_name],
        ["Data Source", "Google Earth Engine (Sentinel/Landsat/SRTM)"],
        ["Report Date", str(datetime.date.today())]
    ]
    
    # رسم جدول المعلومات
    pdf.set_fill_color(240, 240, 240)
    for row in data_info:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(50, 10, row[0], border=1, fill=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 10, row[1], border=1, ln=True)
    
    pdf.ln(10)
    
    # المنهجية العلمية
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(17, 122, 101)
    pdf.cell(0, 10, "1. Scientific Methodology", ln=True)
    
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(0, 0, 0)
    method_text = (
        f"This report presents a systematic analysis of {analysis_name} for the {city} region. "
        "The methodology integrates remote sensing indices with cloud-computing capabilities. "
        "The process involves atmospheric correction, spectral enhancement, and spatial "
        "aggregation to ensure high accuracy in environmental monitoring."
    )
    pdf.multi_cell(0, 7, method_text)
    
    pdf.ln(5)
    
    # النتائج والتوصيات
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(17, 122, 101)
    pdf.cell(0, 10, "2. Analytical Summary", ln=True)
    
    pdf.set_font("Arial", 'I', 11)
    pdf.set_text_color(0, 0, 0)
    summary_text = (
        f"Based on the satellite data from {month} {year}, the {analysis_name} results show "
        "significant spatial variations. These findings are critical for decision-making "
        "in land management, environmental protection, and urban planning within the governorate."
    )
    pdf.multi_cell(0, 7, summary_text)
    
    return pdf

# --------------------------------------------------
# 3. Main Application Logic
# --------------------------------------------------
if authenticate_gee():

    # ---------------- Sidebar ----------------
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/c/c0/Flag_of_Jordan.svg",
        width=100
    )
    st.sidebar.title("🌍 Control Panel")
    st.sidebar.markdown("---")

    # Location selection
    st.sidebar.subheader("📍 Location Settings")
    jordan_governorates = [
        "Amman", "Irbid", "Zarqa", "Aqaba", "Madaba",
        "Mafraq", "Balqa", "Jerash", "Karak", "Ma'an",
        "Tafilah", "Ajloun"
    ]
    target_city = st.sidebar.selectbox("Select Governorate:", jordan_governorates)

    # Temporal settings
    st.sidebar.subheader("📅 Temporal Range")
    current_year = 2025
    selected_year = st.sidebar.slider("Observation Year", 2018, current_year, current_year)

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    selected_month_name = st.sidebar.select_slider("Month", options=month_names)
    selected_month = month_names.index(selected_month_name) + 1

    # Analysis module selection
    st.sidebar.subheader("🛠️ Intelligence Tools")
    analysis_type = st.sidebar.selectbox(
        "Analysis Module:",
        [
            "Terrain Analysis (DEM / Slope / Aspect)",
            "Flood Mapping & Risk (SAR)",
            "Spectral Indices & Environmental Metrics",
            "Air Quality Monitoring (Sentinel-5P)",
            "Land Surface Temperature (LST)",
            "Active Wildfires (FIRMS)",
            "Land Cover Classification"
        ]
    )

    # 📉 PDF Export Button in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Reporting")
    if st.sidebar.button("Generate Scientific PDF"):
        with st.spinner("Analyzing and Generating Report..."):
            report_pdf = create_pdf_report(target_city, selected_year, selected_month_name, analysis_type)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                report_pdf.output(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.sidebar.download_button(
                        label="Download Full Report",
                        data=f,
                        file_name=f"GeoSense_Report_{target_city}.pdf",
                        mime="application/pdf"
                    )

    # Time series option
    enable_ts = st.sidebar.checkbox("📉 Enable Time Series Analysis", value=False)

    # ---------------- Main Interface ----------------
    roi = get_country_roi(target_city)

    # Header section
    st.markdown(
        f"""
        <div style="text-align: center; background: linear-gradient(to right, #1a5276, #117a65); 
        padding: 20px; border-radius: 15px; margin-bottom: 20px;">
            <h1 style="color: white; margin: 0;">GeoSense-Jordan</h1>
            <p style="color: #d1f2eb; font-size: 1.2em;">
                Advanced Satellite Observation | {target_city} - {selected_month_name} {selected_year}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------- Module Routing ----------------
    try:
        if analysis_type == "Terrain Analysis (DEM / Slope / Aspect)":
            dem_analysis.run(target_city, roi, selected_year, selected_month)

        elif analysis_type == "Flood Mapping & Risk (SAR)":
            flood_mapping.run(target_city, roi, selected_year, selected_month)

        elif analysis_type == "Spectral Indices & Environmental Metrics":
            rs_indices.run(target_city, roi, selected_year, selected_month)

        elif analysis_type == "Air Quality Monitoring (Sentinel-5P)":
            pollutant = st.sidebar.radio("Pollutant:", ["NO2", "CO", "O3"])
            air_quality.run(target_city, roi, selected_year, selected_month, pollutant)

        elif analysis_type == "Land Surface Temperature (LST)":
            lst.run(target_city, roi, selected_year, selected_month)

        elif analysis_type == "Active Wildfires (FIRMS)":
            wildfire.run(target_city, roi, selected_year, selected_month)

        elif analysis_type == "Land Cover Classification":
            land_cover.run(target_city, roi, selected_year, selected_month)

        if enable_ts:
            st.markdown("---")
            st.markdown("### 📊 Temporal Trend Analysis")
            time_series.run_analysis(analysis_type, roi, selected_year)

    except Exception as e:
        st.error(f"⚠️ App Routing Error: {str(e)}")

    # Footer
    st.markdown("---")
    st.caption(f"Connected to Google Earth Engine | Region: {target_city} | Mode: Professional Analysis")

else:
    st.error("❌ Google Earth Engine authentication failed.")
