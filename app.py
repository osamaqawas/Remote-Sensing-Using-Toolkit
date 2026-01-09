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
    
    # Metadata
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. Executive Summary", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_fill_color(230, 240, 235)
    
    report_info = [
        ["Governorate", city],
        ["Observation Period", f"{month} {year}"],
        ["Analysis Module", analysis],
        ["Data Source", "Google Earth Engine"],
        ["Report Date", str(datetime.date.today())]
    ]
    
    for row in report_info:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(55, 8, row[0], border=1, fill=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, row[1], border=1, ln=True)
    pdf.ln(10)

    # Statistics
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
        pdf.cell(140, 8, "Analysis completed. Check live dashboard for spatial values.", border=1, ln=True)

    # Visuals (Page 2)
    if chart_path and os.path.exists(chart_path):
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "3. Visual Analytics (Time Series)", ln=True)
        pdf.image(chart_path, x=15, y=30, w=180)

    return pdf

# --------------------------------------------------
# 2. Main App Setup
# --------------------------------------------------
st.set_page_config(page_title="GeoSense-Jordan", page_icon="🇯🇴", layout="wide")

# Persistent memory initialization
if 'data_captured' not in st.session_state:
    st.session_state.data_captured = False
if 'stats' not in st.session_state:
    st.session_state.stats = {}
if 'chart_img' not in st.session_state:
    st.session_state.chart_img = None

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

    # Header
    roi = get_country_roi(target_city)
    st.markdown(f"""
        <div style="text-align: center; background: #1a5276; padding: 20px; border-radius: 15px; margin-bottom: 25px;">
            <h1 style="color: white; margin: 0;">GeoSense-Jordan</h1>
            <p style="color: #d1f2eb;">Researcher: Osama Al-Qawasmeh | Master's Thesis Project</p>
        </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # 3. ANALYSIS EXECUTION
    # --------------------------------------------------
    if st.sidebar.button("🚀 Run Analysis"):
        with st.spinner("Processing Data..."):
            try:
                # Run the module logic
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
                
                # Critical: Save results to persistent state
                st.session_state.stats = results
                st.session_state.data_captured = True
                st.success("Analysis successful! Data is now locked for reporting.")
                
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")

    # Display results if they exist in memory
    if st.session_state.data_captured:
        st.info(f"Showing results for {target_city} ({selected_month_name} {selected_year})")
        
        if enable_ts:
            st.markdown("### 📊 Temporal Trends")
            fig = time_series.run_analysis(analysis_type, roi, selected_year)
            if fig:
                st.pyplot(fig)
                path = os.path.join(tempfile.gettempdir(), "ts_snapshot.png")
                fig.savefig(path, dpi=300)
                st.session_state.chart_img = path

    # --------------------------------------------------
    # 4. PDF REPORTING (SECURE)
    # --------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Reporting Tools")
    
    if st.sidebar.button("Generate Scientific PDF"):
        # We check the memory directly
        if st.session_state.data_captured:
            with st.spinner("Compiling Final Report..."):
                pdf = generate_pdf_report(
                    target_city, 
                    selected_year, 
                    selected_month_name, 
                    analysis_type, 
                    st.session_state.stats,
                    st.session_state.chart_img
                )
                
                # Output PDF to bytes buffer to avoid file permission issues
                pdf_output = pdf.output(dest='S').encode('latin-1')
                
                st.sidebar.download_button(
                    label="📥 Download Report Now",
                    data=pdf_output,
                    file_name=f"GeoSense_Report_{target_city}.pdf",
                    mime="application/pdf"
                )
        else:
            st.sidebar.error("⚠️ Data is not processed yet. Click 'Run Analysis' above.")

else:
    st.error("Google Earth Engine Connection Error.")
