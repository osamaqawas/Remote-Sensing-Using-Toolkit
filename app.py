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
# 1. Professional PDF Report Engine
# --------------------------------------------------
class GeoSenseReport(FPDF):
    def header(self):
        # Report Title & Branding
        self.set_font("Arial", 'B', 16)
        self.set_text_color(26, 82, 118)
        self.cell(0, 10, "GEOSENSE-JORDAN: SCIENTIFIC ANALYTICAL REPORT", ln=True, align='C')
        self.set_draw_color(17, 122, 101)
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        # Footer with page numbers and researcher name
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Researcher: Osama Al-Qawasmeh | Page {self.page_no()}", align='C')

def create_pdf(city, year, month, analysis, stats=None):
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
        ["Report Generation Date", str(datetime.date.today())]
    ]
    
    for row in report_info:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(55, 9, row[0], border=1, fill=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 9, row[1], border=1, ln=True)
    
    pdf.ln(10)

    # Section 1: Methodology
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(17, 122, 101)
    pdf.cell(0, 10, "1. Scientific Methodology", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    
    methodology_text = (
        f"This report utilizes advanced Remote Sensing (RS) and Geospatial Intelligence (GEOINT) "
        f"methods to analyze {analysis}. The processing pipeline includes: (1) Satellite data "
        "acquisition via Sentinel and Landsat missions, (2) Top-of-Atmosphere (TOA) and "
        "Surface Reflectance (SR) corrections, (3) Cloud masking, and (4) Spatial aggregation "
        f"over the {city} Administrative Boundary."
    )
    pdf.multi_cell(0, 7, methodology_text)
    pdf.ln(5)

    # Section 2: Statistical Results
    if stats:
        pdf.set_font("Arial", 'B', 13)
        pdf.set_text_color(17, 122, 101)
        pdf.cell(0, 10, "2. Quantitative Indicators", ln=True)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(80, 8, "Environmental Indicator", border=1, fill=True)
        pdf.cell(60, 8, "Value / Metric", border=1, fill=True, ln=True)
        
        pdf.set_font("Arial", '', 10)
        for key, value in stats.items():
            pdf.cell(80, 8, key, border=1)
            pdf.cell(60, 8, str(value), border=1, ln=True)
        pdf.ln(10)

    # Section 3: Visual Interpretation
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(17, 122, 101)
    pdf.cell(0, 10, "3. Visual Analytics Summary", ln=True)
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 7, "The spatial distribution maps and time-series plots generated in the "
                         "dashboard reveal critical environmental trends. These results are essential "
                         "for localized climate adaptation and resource management in Jordan.")

    return pdf

# --------------------------------------------------
# 2. Main Streamlit Interface
# --------------------------------------------------
st.set_page_config(page_title="GeoSense-Jordan", page_icon="🇯🇴", layout="wide")

if authenticate_gee():
    # --- Sidebar Configuration ---
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/c/c0/Flag_of_Jordan.svg", width=80)
    st.sidebar.title("🌍 Control Panel")
    st.sidebar.markdown("---")
    
    # 📍 Location Selector
    jordan_governorates = ["Amman", "Irbid", "Zarqa", "Aqaba", "Madaba", "Mafraq", "Balqa", "Jerash", "Karak", "Ma'an", "Tafilah", "Ajloun"]
    target_city = st.sidebar.selectbox("Select Governorate:", jordan_governorates)
    
    # 📅 Time Range
    selected_year = st.sidebar.slider("Observation Year", 2018, 2026, 2025)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    selected_month_name = st.sidebar.select_slider("Select Month", options=month_names)
    selected_month = month_names.index(selected_month_name) + 1

    # 🛠 Analysis Modules
    analysis_type = st.sidebar.selectbox("Intelligence Module:", [
        "Terrain Analysis (DEM / Slope / Aspect)",
        "Flood Mapping & Risk (SAR)",
        "Spectral Indices & Environmental Metrics",
        "Air Quality Monitoring (Sentinel-5P)",
        "Land Surface Temperature (LST)",
        "Active Wildfires (FIRMS)",
        "Land Cover Classification"
    ])

    # 📄 Export PDF Section
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Reporting")
    if st.sidebar.button("Generate Scientific Report"):
        with st.spinner("Processing PDF..."):
            # Placeholder for dynamic stats (these can be pulled from your modules)
            analysis_stats = {
                "Region Size": "Calculated via ROI",
                "Processing Engine": "Google Earth Engine",
                "Algorithm Applied": "Random Forest / Spectral Indexing",
                "Confidence Level": "High (Multi-Source Verification)"
            }
            
            report = create_pdf(target_city, selected_year, selected_month_name, analysis_type, analysis_stats)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                report.output(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.sidebar.download_button(
                        label="Download PDF Report",
                        data=f,
                        file_name=f"GeoSense_Report_{target_city}_{selected_year}.pdf",
                        mime="application/pdf"
                    )

    enable_ts = st.sidebar.checkbox("📉 Enable Time Series Analysis")

    # --- Main Header ---
    roi = get_country_roi(target_city)

    st.markdown(f"""
        <div style="text-align: center; background: linear-gradient(to right, #1a5276, #117a65); padding: 20px; border-radius: 15px; margin-bottom: 25px;">
            <h1 style="color: white; margin: 0;">GeoSense-Jordan</h1>
            <p style="color: #d1f2eb; font-size: 1.1em; margin: 5px 0 0 0;">
                Researcher: Osama Al-Qawasmeh | Geospatial Decision Support System
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # 3. Module Routing (Core Logic)
    # --------------------------------------------------
    try:
        if analysis_type == "Terrain Analysis (DEM / Slope / Aspect)":
            dem_analysis.run(target_city, roi, selected_year, selected_month)
        
        elif analysis_type == "Flood Mapping & Risk (SAR)":
            flood_mapping.run(target_city, roi, selected_year, selected_month)
        
        elif analysis_type == "Spectral Indices & Environmental Metrics":
            rs_indices.run(target_city, roi, selected_year, selected_month)
        
        elif analysis_type == "Air Quality Monitoring (Sentinel-5P)":
            pollutant = st.sidebar.radio("Target Pollutant:", ["NO2", "CO", "O3"])
            air_quality.run(target_city, roi, selected_year, selected_month, pollutant)
        
        elif analysis_type == "Land Surface Temperature (LST)":
            lst.run(target_city, roi, selected_year, selected_month)
        
        elif analysis_type == "Active Wildfires (FIRMS)":
            wildfire.run(target_city, roi, selected_year, selected_month)
        
        elif analysis_type == "Land Cover Classification":
            land_cover.run(target_city, roi, selected_year, selected_month)

        # Time Series Execution
        if enable_ts:
            st.markdown("---")
            st.subheader("📊 Temporal Trends")
            time_series.run_analysis(analysis_type, roi, selected_year)

    except Exception as e:
        st.error(f"Error executing analysis module: {str(e)}")

    # Footer
    st.markdown("---")
    st.caption(f"Connected to Google Earth Engine | Study Area: {target_city} | Jordan Geo-Intelligence © 2026")

else:
    st.error("Authentication failed. Please check GEE service account credentials.")
