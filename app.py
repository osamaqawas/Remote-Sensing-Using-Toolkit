import streamlit as st
import datetime
import os
import tempfile
import pandas as pd
from fpdf import FPDF
import plotly.io as pio

# Import Utility Helpers
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
import modules.rainfall as rainfall  # New Module Added

# --------------------------------------------------
# 1. Professional PDF Reporting Engine
# --------------------------------------------------
# --------------------------------------------------
# 1. Advanced Executive Reporting Engine (GeoSense Pro)
# --------------------------------------------------
class GeoSenseReport(FPDF):
    def header(self):
        # إضافة شعار نصي احترافي
        self.set_font("Arial", 'B', 15)
        self.set_text_color(26, 82, 118)
        self.cell(100, 10, "GEOSENSE-JORDAN | ANALYTICAL INTELLIGENCE", ln=0)
        
        self.set_font("Arial", 'I', 9)
        self.set_text_color(100)
        self.cell(0, 10, f"Report ID: GSJ-{datetime.date.today().strftime('%Y%m%d')}", ln=1, align='R')
        
        # خط فاصل مزدوج للأناقة
        self.set_draw_color(26, 82, 118)
        self.set_line_width(0.8)
        self.line(10, 22, 200, 22)
        self.set_line_width(0.2)
        self.line(10, 23, 200, 23)
        self.ln(12)

    def footer(self):
        self.set_y(-20)
        self.set_line_width(0.2)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font("Arial", 'I', 8)
        self.set_text_color(120)
        footer_text = f"Scientific Analysis Report - Developed by Osama Al-Qawasmeh | Generation Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.cell(0, 10, footer_text, align='L')
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align='R')

def generate_pdf_report(city, year, month, analysis, stats_data, chart_path=None):
    pdf = GeoSenseReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # --- العناوين الرئيسية ---
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 15, f"{analysis.upper()} REPORT", ln=True, align='L')
    
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(52, 73, 94)
    pdf.cell(0, 7, f"Geospatial Study for {city} Governorate, Jordan", ln=True)
    pdf.ln(5)

    # --- القسم الأول: معايير الدراسة (Study Metadata) ---
    pdf.set_fill_color(26, 82, 118)
    pdf.set_text_color(255)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "  1. ADMINISTRATIVE & TEMPORAL CONTEXT", ln=True, fill=True)
    pdf.ln(2)

    # جدول بيانات مدمج
    pdf.set_text_color(0)
    pdf.set_font("Arial", 'B', 10)
    
    meta_data = [
        ["Study Area:", f"{city}, Jordan", "Analysis Period:", f"{month} {year}"],
        ["Platform:", "Google Earth Engine", "Coordinate System:", "WGS 84 / EPSG:4326"],
        ["Data Source:", str(stats_data.get('Data Source', 'Satellite Constellation')), "Status:", "Verified"]
    ]

    for row in meta_data:
        pdf.set_font("Arial", 'B', 9)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(35, 8, row[0], border=1, fill=True)
        pdf.set_font("Arial", '', 9)
        pdf.cell(60, 8, row[1], border=1)
        pdf.set_font("Arial", 'B', 9)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(35, 8, row[2], border=1, fill=True)
        pdf.set_font("Arial", '', 9)
        pdf.cell(0, 8, row[3], border=1, ln=True)
    
    pdf.ln(10)

    # --- القسم الثاني: المؤشرات الرئيسية (Key Performance Indicators) ---
    pdf.set_fill_color(26, 82, 118)
    pdf.set_text_color(255)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "  2. QUANTITATIVE ANALYTICS & KPIs", ln=True, fill=True)
    pdf.ln(5)

    # تصميم بطاقات البيانات (Data Cards)
    pdf.set_text_color(0)
    count = 0
    if isinstance(stats_data, dict):
        for key, value in stats_data.items():
            if key not in ['Module', 'Data Source', 'Status']:
                # رسم المربع
                x_start = pdf.get_x()
                y_start = pdf.get_y()
                
                pdf.set_draw_color(200)
                pdf.set_fill_color(252, 252, 252)
                pdf.rect(x_start, y_start, 92, 20, 'DF')
                
                # العنوان الصغير داخل المربع
                pdf.set_font("Arial", 'B', 8)
                pdf.set_text_color(100)
                pdf.set_xy(x_start + 2, y_start + 2)
                pdf.cell(90, 5, key.upper(), ln=0)
                
                # القيمة الكبيرة
                pdf.set_font("Arial", 'B', 14)
                pdf.set_text_color(26, 82, 118)
                pdf.set_xy(x_start + 2, y_start + 10)
                pdf.cell(90, 8, str(value), ln=0)
                
                count += 1
                if count % 2 == 0:
                    pdf.ln(25)
                    pdf.set_x(10)
                else:
                    pdf.set_xy(x_start + 95, y_start)
    
    pdf.ln(20)

    # --- القسم الثالث: التفسير العلمي (Scientific Summary) ---
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(26, 82, 118)
    pdf.cell(0, 10, "3. SCIENTIFIC INTERPRETATION", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0)
    summary_text = (
        f"The advanced geospatial processing for {city} identifies key environmental indicators for {month} {year}. "
        f"The results obtained for {analysis} demonstrate the spatial variability within the study area boundaries. "
        "These metrics are critical for decision-making and regional planning in Jordan's context."
    )
    pdf.multi_cell(0, 6, summary_text, border='L')
    
    # --- الصفحة الثانية: الرسوم البيانية ---
    if chart_path and os.path.exists(chart_path):
        pdf.add_page()
        pdf.set_fill_color(26, 82, 118)
        pdf.set_text_color(255)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "  3. VISUAL TEMPORAL ANALYTICS (TRENDS)", ln=True, fill=True)
        pdf.ln(10)
        
        # وضع الصورة مع إطار خفيف
        pdf.set_draw_color(230)
        pdf.image(chart_path, x=15, y=40, w=180)
        pdf.rect(14, 39, 182, 95, 'D')
        
        pdf.set_y(140)
        pdf.set_font("Arial", 'I', 9)
        pdf.set_text_color(100)
        pdf.cell(0, 10, f"Figure 1.0: Monthly dynamic trend analysis for {analysis} ({year})", align='C', ln=True)

    return pdf
# --------------------------------------------------
# 2. Main App Setup & UI Configuration
# --------------------------------------------------
st.set_page_config(page_title="GeoSense-Jordan", page_icon="🇯🇴", layout="wide")

# Persistent state management
if 'data_captured' not in st.session_state:
    st.session_state.data_captured = False
if 'stats' not in st.session_state:
    st.session_state.stats = {}
if 'chart_img' not in st.session_state:
    st.session_state.chart_img = None

if authenticate_gee():
    # --- Sidebar Controls ---
    st.sidebar.title("🌍 Remote Sensing Control Panel")
    st.sidebar.info("Academic Geospatial Suite for Jordan")
    
    jordan_governorates = ["Amman", "Irbid", "Zarqa", "Aqaba", "Madaba", "Mafraq", "Balqa", "Jerash", "Karak", "Ma'an", "Tafilah", "Ajloun"]
    target_city = st.sidebar.selectbox("Select Study Area (Governorate):", jordan_governorates)
    
    selected_year = st.sidebar.slider("Select Year:", 2018, 2026, 2025)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    selected_month_name = st.sidebar.select_slider("Select Month:", options=month_names)
    selected_month = month_names.index(selected_month_name) + 1

    analysis_type = st.sidebar.selectbox("Select Analytical Module:", [
        "Precipitation & Rainfall (NASA GPM)",
        "Terrain Analysis (DEM / Slope / Aspect)",
        "Flood Mapping & Risk (SAR)",
        "Spectral Indices & Environmental Metrics",
        "Air Quality Monitoring (Sentinel-5P)",
        "Land Surface Temperature (LST)",
        "Active Wildfires (FIRMS)",
        "Land Cover Classification"
    ])
    
    enable_ts = st.sidebar.checkbox("📉 Enable Time Series Trend Analysis")

    # --- Main Header ---
    roi = get_country_roi(target_city)
    st.markdown(f"""
        <div style="text-align: center; background: #1a5276; padding: 25px; border-radius: 15px; margin-bottom: 25px; border: 2px solid #17a2b8;">
            <h1 style="color: white; margin: 0;">GeoSense-Jordan</h1>
            <p style="color: #d1f2eb; font-size: 1.2em; margin-top: 5px;">
                <b>Researcher: Osama Al-Qawasmeh</b> | Master of Science in Geospatial Technologies
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------
    # 3. ANALYSIS EXECUTION ENGINE
    # --------------------------------------------------
    if st.sidebar.button("🚀 Run Scientific Analysis"):
        with st.spinner(f"Acquiring satellite data for {target_city}..."):
            try:
                # Clear previous state
                st.session_state.chart_img = None
                
                # Routing to specific module
                if analysis_type == "Precipitation & Rainfall (NASA GPM)":
                    results = rainfall.run(target_city, roi, selected_year, selected_month)
                elif analysis_type == "Terrain Analysis (DEM / Slope / Aspect)":
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
                st.success(f"Computation for {target_city} completed successfully.")
                
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")

    # --- Result Display & Visualization ---
    if st.session_state.data_captured:
        if enable_ts:
            st.markdown("---")
            st.subheader("📊 Temporal Trend Visualizer")
            
            # Map UI modules to Time Series parameters
            ts_mapping = {
                "Precipitation & Rainfall (NASA GPM)": "Rainfall",
                "Air Quality Monitoring (Sentinel-5P)": "Air Quality",
                "Land Surface Temperature (LST)": "Temp",
                "Spectral Indices & Environmental Metrics": "Vegetation"
            }
            ts_target = ts_mapping.get(analysis_type, "Vegetation")
            
            fig = time_series.run_analysis(ts_target, roi, selected_year)
            
            if fig:
                # Use unique key to prevent DuplicateElementId error
                chart_key = f"ts_chart_{target_city}_{selected_year}_{selected_month}"
                st.plotly_chart(fig, use_container_width=True, key=chart_key)
                
                # Save snapshot for PDF inclusion
                temp_path = os.path.join(tempfile.gettempdir(), f"chart_{target_city}.png")
                try:
                    # Kaleido engine is required here
                    fig.write_image(temp_path, engine="kaleido")
                    st.session_state.chart_img = temp_path
                except Exception as e:
                    st.warning("Note: Kaleido engine not detected. Trends will not appear in the PDF report.")

    # --------------------------------------------------
    # 4. EXPORT & REPORTING TOOLS
    # --------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Reporting & Export")
    
    if st.sidebar.button("📝 Generate Academic PDF Report"):
        if st.session_state.data_captured:
            with st.spinner("Compiling scientific indicators..."):
                pdf = generate_pdf_report(
                    target_city, 
                    selected_year, 
                    selected_month_name, 
                    analysis_type, 
                    st.session_state.stats,
                    st.session_state.chart_img
                )
                
                # Generate byte stream for download
                pdf_bytes = pdf.output(dest='S').encode('latin-1', 'ignore')
                
                st.sidebar.download_button(
                    label="📥 Download Scientific Report",
                    data=pdf_bytes,
                    file_name=f"GeoSense_Jordan_{target_city}_{selected_year}.pdf",
                    mime="application/pdf"
                )
        else:
            st.sidebar.error("⚠️ No data processed. Please run an analysis module first.")

else:
    st.error("Earth Engine Authentication Error. Please check your credentials.")

