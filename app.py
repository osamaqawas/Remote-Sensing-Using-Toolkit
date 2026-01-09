import streamlit as st
import datetime
import os
import tempfile
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from utils.helpers import authenticate_gee
from utils.geometry_utils import get_country_roi

# Import Analysis Modules
import modules.wildfire as wildfire
import modules.air_quality as air_quality
import modules.lst as lst
import modules.land_cover as land_cover
import modules.rs_indices as rs_indices
import modules.flood_mapping as flood_mapping
import modules.dem_analysis as dem_analysis
import modules.time_series as time_series

# --------------------------------------------------
# 1. Professional PDF Reporting Engine
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
    
    # Metadata Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. Executive Summary", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_fill_color(230, 240, 235)
    
    report_info = [
        ["Governorate", city],
        ["Observation Period", f"{month} {year}"],
        ["Analysis Module", analysis],
        ["Data Engine", "Google Earth Engine"],
        ["Report Date", str(datetime.date.today())]
    ]
    
    for row in report_info:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(55, 8, row[0], border=1, fill=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, row[1], border=1, ln=True)
    pdf.ln(10)

    # Statistics Section
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
        pdf.cell(140, 8, "Analysis completed successfully. Refer to dashboard for details.", border=1, ln=True)

    # Image Section (Page 2)
    if chart_path and os.path.exists(chart_path):
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "3. Visual Trend Analytics", ln=True)
        pdf.image(chart_path, x=15, y=30, w=180)

    return pdf

# --------------------------------------------------
# 2. Page Configuration & State Management
# --------------------------------------------------
st.set_page_config(page_title="GeoSense-Jordan", page_icon="🇯🇴", layout="wide")

# Initialize Session State to keep data between reruns
if 'current_stats' not in st.session_state:
    st.session_state['current_stats'] = None
if 'current_chart' not in st.session_state:
    st.session_state['current_chart'] = None

if authenticate_gee():
    # Sidebar
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

    # Main UI Header
    roi = get_country_roi(target_city)
    st.markdown(f"""
        <div style="text-align: center; background: #1a5276; padding: 20px; border-radius: 15px; margin-bottom: 25px;">
            <h1 style="color: white; margin: 0;">GeoSense-Jordan</h1>
            <p style="color: #d1f2eb;">Researcher: Osama Al-Qawasmeh | Master's Thesis Portfolio</p>
        </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # 3. ANALYSIS EXECUTION
    # --------------------------------------------------
    # We use a button to trigger analysis so it doesn't reset unnecessarily
    if st.sidebar.button("🚀 Run Analysis"):
        with st.spinner("Processing Geospatial Data..."):
            try:
                if analysis_type == "Terrain Analysis (DEM / Slope / Aspect)":
                    res = dem_analysis.run(target_city, roi, selected_year, selected_month)
                elif analysis_type == "Flood Mapping & Risk (SAR)":
                    res = flood_mapping.run(target_city, roi, selected_year, selected_month)
                elif analysis_type == "Spectral Indices & Environmental Metrics":
                    res = rs_indices.run(target_city, roi, selected_year, selected_month)
                elif analysis_type == "Air Quality Monitoring (Sentinel-5P)":
                    res = air_quality.run(target_city, roi, selected_year, selected_month, "NO2")
                elif analysis_type == "Land Surface Temperature (LST)":
                    res = lst.run(target_city, roi, selected_year, selected_month)
                elif analysis_type == "Active Wildfires (FIRMS)":
                    res = wildfire.run(target_city, roi, selected_year, selected_month)
                elif analysis_type == "Land Cover Classification":
                    res = land_cover.run(target_city, roi, selected_year, selected_month)
                
                # Save results to session state
                st.session_state['current_stats'] = res
                st.success("Analysis Completed! You can now generate the PDF.")

            except Exception as e:
                st.error(f"Analysis Error: {e}")

    # Display Time Series if enabled
    if enable_ts:
        st.markdown("### 📊 Time Series Trends")
        fig = time_series.run_analysis(analysis_type, roi, selected_year)
        if fig:
            st.pyplot(fig)
            path = os.path.join(tempfile.gettempdir(), "ts_plot.png")
            fig.savefig(path, dpi=300)
            st.session_state['current_chart'] = path

    # --------------------------------------------------
    # 4. PDF GENERATION
    # --------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Reporting")
    
    if st.sidebar.button("Generate Scientific PDF"):
        # We check the session state instead of a local variable
        if st.session_state['current_stats'] is not None:
            with st.spinner("Generating PDF..."):
                pdf = generate_pdf_report(
                    target_city, 
                    selected_year, 
                    selected_month_name, 
                    analysis_type, 
                    st.session_state['current_stats'],
                    st.session_state['current_chart']
                )
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    with open(tmp.name, "rb") as f:
                        st.sidebar.download_button("📥 Download Report", f, f"Report_{target_city}.pdf")
        else:
            st.sidebar.error("Please click 'Run Analysis' button first!")

else:
    st.error("GEE Authentication Failed.")
