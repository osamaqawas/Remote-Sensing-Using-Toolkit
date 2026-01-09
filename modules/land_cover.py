import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static
import pandas as pd

def run(country_name, roi, year, month):
    st.markdown(f"""
        <div style="background-color: #7D3C98; padding: 20px; border-radius: 15px; text-align: center; border: 2px solid #5B2C6F;">
            <h2 style="color: white; margin: 0;">🛰️ Supervised Land Cover Classification</h2>
            <p style="color: #EBDEF0; margin: 5px 0 0 0;">
                Random Forest Machine Learning | 10m Sentinel-2 Resolution
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Date range configuration
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')

    def mask_s2_clouds(image):
        qa = image.select('QA60')
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).bitwiseAnd(cirrus_bit_mask).eq(0)
        return image.updateMask(mask).divide(10000)

    # 2. Load Sentinel-2 Collection
    s2_collection = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .map(mask_s2_clouds)
        .select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12'])
    )

    if s2_collection.size().getInfo() == 0:
        st.warning("No imagery found for this period. Expanding search...")
        s2_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(roi).map(mask_s2_clouds).select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12'])

    image = s2_collection.median().clip(roi)

    # 3. Training Logic (Random Forest)
    label_source = ee.Image("ESA/WorldCover/v200/2021").clip(roi)
    
    with st.spinner("Training Random Forest Classifier (100 Trees)..."):
        try:
            training_points = label_source.sample(region=roi, scale=100, numPixels=1500, seed=42, geometries=True)
            training_data = image.sampleRegions(collection=training_points, properties=['Map'], scale=10)
            classifier = ee.Classifier.smileRandomForest(100).train(
                features=training_data,
                classProperty='Map',
                inputProperties=['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
            )
            classified = image.classify(classifier)
        except Exception as e:
            st.error(f"ML Training Error: {e}")
            return {"Status": "Training Failed"}

    # 4. Definitions
    class_values = [10, 20, 30, 40, 50, 60, 80]
    class_names = ['Trees', 'Shrubland', 'Grassland', 'Cropland', 'Built-up', 'Bare Ground', 'Water']
    class_colors = ['#006400', '#ffbb22', '#ffff4c', '#f096ff', '#fa0000', '#b4b4b4', '#0064ff']

    # 5. Statistics Calculation
    stats_dict = {}
    st.markdown("### 📊 Classification Statistics")
    try:
        area_calc = ee.Image.pixelArea().addBands(classified)
        area_stats = area_calc.reduceRegion(
            reducer=ee.Reducer.sum().group(groupField=1, groupName='class'),
            geometry=roi, scale=100, maxPixels=1e10
        ).get('groups').getInfo()

        for item in area_stats:
            c_id = int(item['class'])
            if c_id in class_values:
                name = class_names[class_values.index(c_id)]
                area_km2 = item['sum'] / 1e6
                stats_dict[name] = f"{area_km2:.2f} km²"
        
        st.bar_chart(pd.DataFrame([{'Category': k, 'Area (km²)': float(v.split()[0])} for k,v in stats_dict.items()]).set_index('Category'))
    except:
        st.info("Computing spatial statistics...")

    # 6. Map Rendering
    m = geemap.Map()
    m.add_basemap("SATELLITE")
    vis_image = classified.remap(class_values, list(range(len(class_values))))
    m.addLayer(image, {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.3}, "Reference Imagery")
    m.addLayer(vis_image, {'min': 0, 'max': 6, 'palette': class_colors}, "RF Classification")
    m.add_legend(title="Land Cover Type", legend_dict=dict(zip(class_names, class_colors)))
    m.centerObject(roi, 10)
    
    st.markdown('<div style="border: 3px solid #7D3C98; border-radius: 15px; overflow: hidden;">', unsafe_allow_html=True)
    folium_static(m, width=1000)
    st.markdown('</div>', unsafe_allow_html=True)

    # Return for PDF
    report_results = {"Algorithm": "Random Forest (smileRandomForest)", "Resolution": "10 meters", "Training Data": "ESA WorldCover 2021"}
    report_results.update(stats_dict)
    
    return report_results
