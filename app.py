import streamlit as st
import datetime
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
    page_title="GeoSense-Jordan"
    "Osama Al-Qawasmeh",
    page_icon="🇯🇴",
    layout="wide"
)

# --------------------------------------------------
# 2. Google Earth Engine Authentication
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
    target_city = st.sidebar.selectbox(
        "Select Governorate:",
        jordan_governorates
    )

    # Temporal settings
    st.sidebar.subheader("📅 Temporal Range")
    current_year = 2025
    selected_year = st.sidebar.slider(
        "Observation Year",
        2018,
        current_year,
        current_year
    )

    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    selected_month_name = st.sidebar.select_slider(
        "Month",
        options=month_names
    )
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

    # Time series option
    st.sidebar.markdown("---")
    enable_ts = st.sidebar.checkbox(
        "📉 Enable Time Series Analysis",
        value=False
    )
    st.sidebar.caption(
        "Generates a yearly trend chart below the map."
    )

    # ---------------- Main Interface ----------------
    roi = get_country_roi(target_city)

    # Header section
    st.markdown(
        f"""
        <div style="
            text-align: center;
            background: linear-gradient(to right, #1a5276, #117a65);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;">
            <h1 style="color: white; margin: 0;">
                GeoSense-Jordan
            </h1>
            <p style="color: #d1f2eb; font-size: 1.2em;">
                Advanced Satellite Observation |
                {target_city} - {selected_month_name} {selected_year}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------- Module Routing ----------------
    try:
        # Terrain analysis
        if analysis_type == "Terrain Analysis (DEM / Slope / Aspect)":
            dem_analysis.run(
                target_city, roi,
                selected_year, selected_month
            )

        # Flood mapping
        elif analysis_type == "Flood Mapping & Risk (SAR)":
            flood_mapping.run(
                target_city, roi,
                selected_year, selected_month
            )

        # Spectral indices
        elif analysis_type == "Spectral Indices & Environmental Metrics":
            rs_indices.run(
                target_city, roi,
                selected_year, selected_month
            )

        # Air quality
        elif analysis_type == "Air Quality Monitoring (Sentinel-5P)":
            pollutant = st.sidebar.radio(
                "Pollutant:",
                ["NO2", "CO", "O3"]
            )
            air_quality.run(
                target_city, roi,
                selected_year, selected_month,
                pollutant
            )

        # Land surface temperature
        elif analysis_type == "Land Surface Temperature (LST)":
            lst.run(
                target_city, roi,
                selected_year, selected_month
            )

        # Wildfire detection
        elif analysis_type == "Active Wildfires (FIRMS)":
            wildfire.run(
                target_city, roi,
                selected_year, selected_month
            )

        # Land cover classification
        elif analysis_type == "Land Cover Classification":
            land_cover.run(
                target_city, roi,
                selected_year, selected_month
            )

        # -------- Time Series Section --------
        if enable_ts:
            st.markdown("---")
            st.markdown("### 📊 Temporal Trend Analysis")
            time_series.run_analysis(
                analysis_type,
                roi,
                selected_year
            )

    except Exception as e:
        st.error(f"⚠️ App Routing Error: {str(e)}")
        st.info(
            "Please verify that all module files exist "
            "inside the 'modules/' directory."
        )

    # Footer
    st.markdown("---")
    st.caption(
        f"Connected to Google Earth Engine | "
        f"Region: {target_city} | "
        f"Mode: Professional Analysis"
    )

else:
    st.error(
        "❌ Google Earth Engine authentication failed. "
        "Please check your service account credentials."
    )

