import streamlit as st
import ee
import pandas as pd
import plotly.express as px

def run_analysis(analysis_type, roi, year):
    st.markdown(f"### 📈 {analysis_type} Historical Trend ({year})")
    
    with st.spinner("📊 Extracting temporal data from satellite constellations..."):
        try:
            # 1. Select satellite dataset and band based on analysis type
            if "Air Quality" in analysis_type:
                collection = ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2") \
                    .select('NO2_column_number_density')
                label = "NO₂ Concentration"
            
            elif "Vegetation" in analysis_type or "Indices" in analysis_type:
                collection = ee.ImageCollection("MODIS/061/MOD13Q1") \
                    .select('NDVI')
                label = "Vegetation Index (NDVI)"
                
            elif "Temp" in analysis_type:
                collection = ee.ImageCollection("MODIS/061/MOD11A1") \
                    .select('LST_Day_1km')
                label = "Surface Temperature (K)"
            
            else:
                st.info("Time series analysis is currently available for Air Quality, NDVI, and Temperature only.")
                return

            # 2. Filter data for the selected year and aggregate monthly values
            start_date = ee.Date.fromYMD(year, 1, 1)
            end_date = ee.Date.fromYMD(year, 12, 31)
            
            monthly_data = []
            
            for month in range(1, 13):
                m_start = ee.Date.fromYMD(year, month, 1)
                m_end = m_start.advance(1, 'month')
                
                # Calculate monthly mean over the selected ROI
                mean_val = collection.filterDate(m_start, m_end) \
                    .mean() \
                    .reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=roi,
                        scale=1000,
                        maxPixels=1e9
                    ).getInfo()
                
                val = list(mean_val.values())[0] if mean_val else None
                monthly_data.append({"Month": month, "Value": val})

            # 3. Convert results to DataFrame and visualize
            df = pd.DataFrame(monthly_data)
            df['Month Name'] = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]
            
            # Remove missing values
            df = df.dropna()

            if not df.empty:
                
                fig = px.line(
                    df,
                    x='Month Name',
                    y='Value',
                    title=f'Monthly Average of {label} in {year}',
                    markers=True,
                    line_shape='spline',
                    color_discrete_sequence=['#117A65']
                )
                
                fig.update_layout(
                    hovermode="x unified",
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display raw data table
                with st.expander("📂 View Raw Data Table"):
                    st.dataframe(df)
            else:
                st.warning("No sufficient data available to generate a time series for this year.")

        except Exception as e:
            st.error(f"Time series calculation error: {e}")
