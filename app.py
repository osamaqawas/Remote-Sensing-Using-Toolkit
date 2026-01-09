import streamlit as st
import ee
import geemap.foliumap as geemap
from datetime import datetime
import importlib

# Import Modules
from modules import (
    air_quality, dem_analysis, flood_mapping, 
    land_cover, lst, rs_indices, time_series, wildfire
)

# 1. Initialize Earth Engine
try:
    ee.Initialize()
except Exception as e:
    st.error("Earth Engine authentication failed. Please run 'earthengine authenticate' in your terminal.")

# --- Page Configuration ---
st.set_page_config(page_title="Master's RS Toolkit", layout="wide", page_icon="🛰️")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
with st.sidebar:
    st.image("https://www.gstatic.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png", width=100)
    st.title("🛰️ Geospatial Control Center")
    st.info("Academic Project for Environmental Monitoring")
    
    st.header("📍 Study Area")
    country_choice = st.selectbox("Select Country", ["Jordan", "Qatar", "Saudi Arabia", "Egypt", "UAE"])
    
    st.header("📅 Temporal Range")
    year = st.slider("Select Year", 2019, 2025, 2024)
    month = st.selectbox("Select Month", range(1, 13), format_func=lambda x: datetime(2024, x, 1).strftime('%B'))
    
    st.header("🔍 Analysis Engine")
    analysis_type = st.radio("Select Research Domain", [
        "Air Quality Intelligence",
        "Topographic Characterization",
        "Flood Risk Mapping",
        "Land Cover (Machine Learning)",
        "Thermal Intensity (LST)",
        "Spectral Indices",
        "Active Wildfires",
        "Temporal Time Series"
    ])

# --- Main Logic Connection ---
# Define ROI based on selection
countries = {
    "Jordan": ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017").filter(ee.Filter.eq('country_na', 'Jordan')),
    "Qatar": ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017").filter(ee.Filter.eq('country_na', 'Qatar')),
    "Saudi Arabia": ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017").filter(ee.Filter.eq('country_na', 'Saudi Arabia')),
    "Egypt": ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017").filter(ee.Filter.eq('country_na', 'Egypt')),
    "UAE": ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017").filter(ee.Filter.eq('country_na', 'United Arab Emirates'))
}
roi = countries[country_choice]

# Store results for report generation
analysis_results = None

# --- Run Analysis Based on Selection ---
if analysis_type == "Air Quality Intelligence":
    pollutant = st.sidebar.selectbox("Pollutant Type", ["NO2 (Nitrogen Dioxide)", "CO (Carbon Monoxide)", "O3 (Ozone)"])
    analysis_results = air_quality.run(country_choice, roi, year, month, pollutant)

elif analysis_type == "Topographic Characterization":
    analysis_results = dem_analysis.run(country_choice, roi, year, month)

elif analysis_type == "Flood Risk Mapping":
    analysis_results = flood_mapping.run(country_choice, roi, year, month)

elif analysis_type == "Land Cover (Machine Learning)":
    analysis_results = land_cover.run(country_choice, roi, year, month)

elif analysis_type == "Thermal Intensity (LST)":
    analysis_results = lst.run(country_choice, roi, year, month)

elif analysis_type == "Spectral Indices":
    analysis_results = rs_indices.run(country_choice, roi, year, month)

elif analysis_type == "Active Wildfires":
    analysis_results = wildfire.run(country_choice, roi, year, month)

elif analysis_type == "Temporal Time Series":
    target = st.sidebar.selectbox("Parameter for Trend", ["Air Quality (NO2)", "Vegetation (NDVI)", "Surface Temperature (LST)"])
    # Handle the Plotly figure returned by Time Series
    fig = time_series.run_analysis(target, roi, year)
    analysis_results = {"Type": "Temporal Trend Analysis", "Target": target, "Year": year}

# --- PDF REPORT GENERATOR SECTION ---
st.sidebar.markdown("---")
if st.sidebar.button("📄 Generate Academic Report"):
    if analysis_results:
        st.sidebar.success("Generating English PDF Report...")
        
        # Simple Logic to display report data on screen for now
        with st.expander("📝 Report Summary (Export Preview)", expanded=True):
            st.markdown(f"## Research Report: {analysis_type}")
            st.markdown(f"**Region:** {country_choice} | **Period:** {month}/{year}")
            st.markdown("---")
            
            # Create a table from the results dictionary
            if isinstance(analysis_results, dict):
                import pandas as pd
                df_report = pd.DataFrame(list(analysis_results.items()), columns=['Parameter', 'Value'])
                st.table(df_report)
            
            st.info("Disclaimer: This data is generated using satellite remote sensing products (Copernicus/NASA/JAXA).")
    else:
        st.sidebar.error("Please run an analysis first.")

# --- Footer ---
st.markdown("---")
st.caption(f"Remote Sensing Master Toolkit © {datetime.now().year} | Designed for Advanced Geospatial Analytics")
