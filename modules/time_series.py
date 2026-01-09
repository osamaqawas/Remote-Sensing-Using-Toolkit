import streamlit as st
import ee
import pandas as pd
import plotly.express as px

def run_analysis(analysis_type, roi, year):
    st.markdown(f"### 📈 {analysis_type} Temporal Trend ({year})")
    
    with st.spinner("📊 Extracting temporal data from satellite constellations..."):
        try:
            # 1. Dataset selection logic
            if "Air Quality" in analysis_type:
                collection = ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2") \
                    .select('NO2_column_number_density')
                label = "NO₂ Concentration"
                unit_label = "mol/m²"
                line_color = '#E74C3C' # Red for Air Quality
            
            elif "Vegetation" in analysis_type or "Indices" in analysis_type:
                collection = ee.ImageCollection("MODIS/061/MOD13Q1") \
                    .select('NDVI')
                label = "Vegetation Index (NDVI)"
                unit_label = "NDVI Score"
                line_color = '#27AE60' # Green for Vegetation
                
            elif "Temp" in analysis_type:
                collection = ee.ImageCollection("MODIS/061/MOD11A1") \
                    .select('LST_Day_1km')
                label = "Land Surface Temp"
                unit_label = "Celsius (°C)"
                line_color = '#F39C12' # Orange for Temperature

            elif "Rainfall" in analysis_type:
                collection = ee.ImageCollection("NASA/GPM_L3/IMERG_V06") \
                    .select('precipitationCal')
                label = "Total Precipitation"
                unit_label = "Rainfall (mm)"
                line_color = '#2980B9' # Blue for Rainfall
            
            else:
                st.info("Time series analysis is optimized for Air Quality, NDVI, Temperature, and Rainfall.")
                return None

            # 2. Monthly Data Aggregation
            monthly_data = []
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            
            for month in range(1, 13):
                m_start = ee.Date.fromYMD(year, month, 1)
                m_end = m_start.advance(1, 'month')
                
                # Filter collection for the specific month
                m_coll = collection.filterDate(m_start, m_end)
                
                # CHECK: Ensure data exists for this month to avoid "0 bands" error
                if m_coll.size().getInfo() > 0:
                    img = m_coll.mean()
                    
                    # Apply specific processing based on analysis type
                    if "Temp" in analysis_type:
                        img = img.multiply(0.02).subtract(273.15)
                    elif "Vegetation" in analysis_type:
                        img = img.multiply(0.0001)
                    elif "Rainfall" in analysis_type:
                        # Convert half-hourly rate (mm/hr) to monthly total 
                        # Approx 720 hours in a month * 0.5 (half-hour steps)
                        img = img.multiply(720 * 0.5)

                    stats = img.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=5000 if "Rainfall" in analysis_type else 1000,
                        maxPixels=1e9
                    ).getInfo()
                    
                    val = list(stats.values())[0] if stats else None
                else:
                    val = None # Data not yet available for this month
                
                monthly_data.append({"Month": month, "Month Name": month_names[month-1], "Value": val})

            # 3. Processing and Visualization
            df = pd.DataFrame(monthly_data)
            df = df.dropna() # Remove months with no satellite data

            if not df.empty:
                fig = px.line(
                    df,
                    x='Month Name',
                    y='Value',
                    title=f'Monthly Temporal Trend: {label} ({year})',
                    markers=True,
                    line_shape='spline',
                    color_discrete_sequence=[line_color]
                )
                
                fig.update_layout(
                    xaxis_title="Calendar Month",
                    yaxis_title=unit_label,
                    hovermode="x unified",
                    template="plotly_white",
                    font=dict(family="Arial", size=12)
                )
                
                st.plotly_chart(fig, use_container_width=True, key=f"ts_chart_{analysis_type}")
                
                with st.expander("📂 View Analytical Data Table"):
                    st.table(df[['Month Name', 'Value']])
                
                return fig 
            
            else:
                st.warning(f"⚠️ No satellite imagery found for {year} in this region. Try a previous year.")
                return None

        except Exception as e:
            st.error(f"Temporal Analysis Error: {e}")
            return None
