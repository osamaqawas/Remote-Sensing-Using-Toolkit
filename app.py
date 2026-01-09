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
    
    # Section 1: Metadata
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

    # Section 2: Quantitative Results
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. Statistical Indicators", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(80, 8, "Indicator Metric", border=1, fill=True)
    pdf.cell(60, 8, "Value", border=1, fill=True, ln=True)
    
    pdf.set_font("Arial", '', 10)
    if isinstance(stats_data, dict):
        for key, value in stats_data.items():
            pdf.cell(80, 8, str(key), border=1)
            pdf.cell(60, 8, str(value), border=1, ln=True)
    else:
        pdf.cell(140, 8, "Analysis completed successfully. See dashboard for live values.", border=1, ln=True)

    # Section 3: Visual Analytics (Page 2)
    if chart_path and os.path.exists(chart_path):
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "3. Visual Trend Analysis", ln=True)
        pdf.image(chart_path, x=15, y=30, w=180)
        pdf.set_y(150)
        pdf.set_font("Arial", 'I', 9)
        pdf.multi_cell(0, 7, "This chart represents the temporal variation of the selected indices. "
                             "Spatial maps are rendered dynamically within the GeoSense platform.")

    return pdf

# --------------------------------------------------
# 2. Page Configuration & Session State
# --------------------------------------------------
st.set_page_config(page_title="GeoSense-Jordan", page_icon="🇯🇴", layout="wide")

# Persistent memory for analysis results
if 'final_stats' not in st.session_state:
    st.session_state['final_stats'] = None
if 'chart_path' not in st.session_state:
    st.session_state['chart_path'] = None

if authenticate_gee():
    # --- Sidebar Setup ---
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/c/c0/Flag_of_Jordan.svg", width=80)
    st.sidebar.title("🌍 Control Panel")
    
    jordan_governorates = ["Amman", "Irbid", "Zarqa", "Aqaba", "Madaba", "Mafraq", "Balqa", "Jerash", "Karak", "Ma'an", "Tafilah", "Ajloun"]
    target_city = st.sidebar.selectbox("Select Governorate:", jordan_governorates)
    
    selected_year = st.sidebar.slider("Year", 2018, 2026, 2025)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    selected_month_name = st.sidebar.select_slider("Month", options=month_names)
    selected_month = month_names.index(selected_month_name) + 1

    analysis_type = st.sidebar.selectbox("Analysis Module:", [
        "Terrain Analysis (DEM / Slope / Aspect)",
        "Flood Mapping & Risk (SAR)",
        "Spectral Indices & Environmental Metrics",
        "Air Quality Monitoring (Sentinel-5P)",
        "Land Surface Temperature (LST)",
        "Active Wildfires (FIRMS)",
        "Land Cover Classification"
    ])

    enable_ts = st.sidebar.checkbox("📉 Enable Time Series")
    
    # --- Main Screen Header ---
    roi = get_country_roi(target_city)
    st.markdown(f"""
        <div style="text-align: center; background: linear-gradient(to right, #1a5276, #117a65); padding: 20px; border-radius: 15px; margin-bottom: 25px;">
            <h1 style="color: white; margin: 0;">GeoSense-Jordan</h1>
            <p style="color: #d1f2eb; font-size: 1.1em;">Researcher: Osama Al-Qawasmeh | Geospatial Intelligence Dashboard</p>
        </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # 3. Execution & Routing
    # --------------------------------------------------
    try:
        # Running the selected analysis module
        if analysis_type == "Terrain Analysis (DEM / Slope / Aspect)":
            st.session_state['final_stats'] = dem_analysis.run(target_city, roi, selected_year, selected_month)
        elif analysis_type == "Flood Mapping & Risk (SAR)":
            st.session_state['final_stats'] = flood_mapping.run(target_city, roi, selected_year, selected_month)
        elif analysis_type == "Spectral Indices & Environmental Metrics":
            st.session_state['final_stats'] = rs_indices.run(target_city, roi, selected_year, selected_month)
        elif analysis_type == "Air Quality Monitoring (Sentinel-5P)":
            pollutant = st.sidebar.radio("Pollutant:", ["NO2", "CO", "O3"])
            st.session_state['final_stats'] = air_quality.run(target_city, roi, selected_year, selected_month, pollutant)
        elif analysis_type == "Land Surface Temperature (LST)":
            st.session_state['final_stats'] = lst.run(target_city, roi, selected_year, selected_month)
        elif analysis_type == "Active Wildfires (FIRMS)":
            st.session_state['final_stats'] = wildfire.run(target_city, roi, selected_year, selected_month)
        elif analysis_type == "Land Cover Classification":
            st.session_state['final_stats'] = land_cover.run(target_city, roi, selected_year, selected_month)

        # Handle Time Series
        if enable_ts:
            st.markdown("---")
            fig = time_series.run_analysis(analysis_type, roi, selected_year)
            if fig:
                st.pyplot(fig)
                # Save plot to temp file for PDF
                temp_path = os.path.join(tempfile.gettempdir(), "temp_ts_chart.png")
                fig.savefig(temp_path, dpi=300, bbox_inches='tight')
                st.session_state['chart_path'] = temp_path

    except Exception as e:
        st.error(f"Analysis Error: {e}")

    # --- PDF Export Section ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Reporting")
    
    if st.sidebar.button("Generate Scientific PDF"):
        # Check if we actually have data to report
        if st.session_state['final_stats'] is not None:
            with st.spinner("Compiling Full Scientific Report..."):
                pdf_report = generate_pdf_report(
                    target_city, 
                    selected_year, 
                    selected_month_name, 
                    analysis_type, 
                    st.session_state['final_stats'], 
                    st.session_state['chart_path']
                )
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf_report.output(tmp.name)
                    with open(tmp.name, "rb") as f:
                        st.sidebar.download_button(
                            label="📥 Download PDF Report",
                            data=f,
                            file_name=f"GeoSense_Report_{target_city}_{selected_year}.pdf",
                            mime="application/pdf"
                        )
        else:
            st.sidebar.error("Please run the analysis first to capture statistics.")

    st.markdown("---")
    st.caption("Jordan Geospatial Intelligence Platform | Professional Edition 2026")

else:
    st.error("Google Earth Engine Authentication Failed.")
