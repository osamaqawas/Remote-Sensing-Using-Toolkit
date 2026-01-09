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
                label = "NO₂ Concentration (mol/m²)"
                unit_label = "mol/m²"
            
            elif "Vegetation" in analysis_type or "Indices" in analysis_type:
                collection = ee.ImageCollection("MODIS/061/MOD13Q1") \
                    .select('NDVI')
                label = "Vegetation Index (NDVI)"
                unit_label = "NDVI Score"
                
            elif "Temp" in analysis_type:
                collection = ee.ImageCollection("MODIS/061/MOD11A1") \
                    .select('LST_Day_1km')
                label = "Land Surface Temperature (°C)"
                unit_label = "Celsius"
            
            else:
                st.info("Time series analysis is optimized for Air Quality, NDVI, and Temperature.")
                return None

            # 2. Monthly Data Aggregation
            monthly_data = []
            
            for month in range(1, 13):
                m_start = ee.Date.fromYMD(year, month, 1)
                m_end = m_start.advance(1, 'month')
                
                # Filter and reduce
                img = collection.filterDate(m_start, m_end).mean()
                
                # Apply conversion for Temperature if needed
                if "Temp" in analysis_type:
                    img = img.multiply(0.02).subtract(273.15)
                
                # Apply scaling for NDVI if needed
                if "Vegetation" in analysis_type:
                    img = img.multiply(0.0001)

                stats = img.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=roi,
                    scale=1000,
                    maxPixels=1e9
                ).getInfo()
                
                val = list(stats.values())[0] if stats else None
                monthly_data.append({"Month": month, "Value": val})

            # 3. Processing and Visualization
            df = pd.DataFrame(monthly_data)
            df['Month Name'] = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            df = df.dropna()

            if not df.empty:
                fig = px.line(
                    df,
                    x='Month Name',
                    y='Value',
                    title=f'Monthly Temporal Analysis: {label} ({year})',
                    markers=True,
                    line_shape='spline',
                    color_discrete_sequence=['#117A65']
                )
                
                fig.update_layout(
                    xaxis_title="Calendar Month",
                    yaxis_title=unit_label,
                    hovermode="x unified",
                    template="plotly_white",
                    font=dict(family="Arial", size=12)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Expandable Raw Data
                with st.expander("📂 View Tabular Data"):
                    st.table(df[['Month Name', 'Value']])
                
                return fig # Crucial for PDF generation
            
            else:
                st.warning("Insufficient satellite coverage for the selected period.")
                return None

        except Exception as e:
            st.error(f"Temporal Analysis Error: {e}")
            return None
