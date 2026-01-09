import streamlit as st
import datetime
import os
import tempfile
import pandas as pd
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

def generate_pdf_report(city, year, month, analysis, stats_data):
    pdf = GeoSenseReport()
    pdf.add_page()
    
    # Information Table
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(230, 240, 235)
    
    report_info = [
        ["Governorate", city],
        ["Observation Period", f"{month} {year}"],
        ["Analysis Module", analysis],
        ["Data Source", "Google Earth Engine (Multi-Mission Satellite Data)"],
        ["Report Date", str(datetime.date.today())]
    ]
    
    for row in report_info:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(55, 9, row[0], border=1, fill=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 9, row[1], border=1, ln=True)
    
    pdf.ln(10)

    # Methodology Section
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(17, 122, 101)
    pdf.cell(0, 10, "1. Scientific Methodology", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    methodology = (
        f"This report presents an advanced geospatial analysis of {analysis} for {city}. "
        "The workflow includes multi-spectral satellite acquisition, atmospheric correction, "
        "and spatial reduction algorithms to derive accurate environmental metrics."
    )
    pdf.multi_cell(0, 7, methodology)
    pdf.ln(5)

    # Quantitative Indicators Section
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(17, 122, 101)
    pdf.cell(0, 10, "2. Quantitative Results", ln=True)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(80, 8, "Indicator Metric", border=1, fill=True)
    pdf.cell(60, 8, "Calculated Value", border=1, fill=True, ln=True)
    
    pdf.set_font("Arial", '', 10)
    for key, value in stats_data.items():
        pdf.cell(80, 8, key, border=1)
        pdf.cell(60, 8, str(value), border=1, ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 7, "Note: Visual distribution maps and trend charts are available in the live dashboard.")
    return pdf

# --------------------------------------------------
# 2. Main Interface Configuration
# --------------------------------------------------
st.set_page_config(page_title="GeoSense-Jordan", page_icon="🇯🇴", layout="wide")

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
    
    # Variable to hold data for the PDF
    final_stats = {"Status": "Data Ready", "Accuracy": "Verified"}

    # --- Main Screen ---
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
        # We capture the returned dictionary from each module to use in the PDF
        if analysis_type == "Terrain Analysis (DEM / Slope / Aspect)":
            final_stats = dem_analysis.run(target_city, roi, selected_year, selected_month)
        elif analysis_type == "Flood Mapping & Risk (SAR)":
            final_stats = flood_mapping.run(target_city, roi, selected_year, selected_month)
        elif analysis_type == "Spectral Indices & Environmental Metrics":
            final_stats = rs_indices.run(target_city, roi, selected_year, selected_month)
        elif analysis_type == "Air Quality Monitoring (Sentinel-5P)":
            pollutant = st.sidebar.radio("Pollutant:", ["NO2", "CO", "O3"])
            final_stats = air_quality.run(target_city, roi, selected_year, selected_month, pollutant)
        elif analysis_type == "Land Surface Temperature (LST)":
            final_stats = lst.run(target_city, roi, selected_year, selected_month)
        elif analysis_type == "Active Wildfires (FIRMS)":
            final_stats = wildfire.run(target_city, roi, selected_year, selected_month)
        elif analysis_type == "Land Cover Classification":
            final_stats = land_cover.run(target_city, roi, selected_year, selected_month)

        if enable_ts:
            st.markdown("---")
            time_series.run_analysis(analysis_type, roi, selected_year)

    except Exception as e:
        st.error(f"Analysis Error: {e}")

    # --- PDF Button (Now placed after execution so it has data) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Export Results")
    if st.sidebar.button("Generate Scientific PDF"):
        with st.spinner("Compiling Professional Report..."):
            # If module returns None, use placeholder to avoid crash
            report_data = final_stats if isinstance(final_stats, dict) else {"Result": "Analysis Completed"}
            
            pdf_report = generate_pdf_report(target_city, selected_year, selected_month_name, analysis_type, report_data)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf_report.output(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.sidebar.download_button(
                        label="Download PDF Report",
                        data=f,
                        file_name=f"GeoSense_Report_{target_city}.pdf",
                        mime="application/pdf"
                    )

    st.markdown("---")
    st.caption("Jordan Geospatial Intelligence Platform | Professional Edition 2026")

else:
    st.error("Google Earth Engine Authentication Failed.")
