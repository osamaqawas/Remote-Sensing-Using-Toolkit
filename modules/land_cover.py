import streamlit as st
import ee
import geemap.foliumap as geemap
from streamlit_folium import folium_static
import pandas as pd

def run(country_name, roi, year, month):
    st.subheader(f"Sentinel-2 Random Forest Land Cover Classification – {country_name}")
    st.write(f"Processing 10 m spatial resolution imagery for {month}/{year}")

    # 1. Date range configuration
    start_date = ee.Date.fromYMD(year, month, 1)
    end_date = start_date.advance(1, 'month')

    # 2. Cloud masking function for Sentinel-2 SR
    def mask_s2_clouds(image):
        qa = image.select('QA60')
        # Bit 10: opaque clouds, Bit 11: cirrus clouds
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11

        # Keep pixels where both cloud bits are set to zero
        mask = qa.bitwiseAnd(cloud_bit_mask).eq(0) \
                 .bitwiseAnd(cirrus_bit_mask).eq(0)

        # Scale reflectance values to [0–1]
        return image.updateMask(mask).divide(10000)

    # 3. Load Sentinel-2 surface reflectance collection
    s2_collection = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .map(mask_s2_clouds)
        .select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12'])
    )

    # Fallback strategy if no clear imagery is found
    if s2_collection.size().getInfo() == 0:
        st.warning(
            f"No cloud-free imagery available for {country_name} "
            f"during {month}/{year}. Expanding temporal search window..."
        )
        s2_collection = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(roi)
            .filterDate(start_date.advance(-3, 'month'), end_date)
            .map(mask_s2_clouds)
            .select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12'])
        )

    # Median composite
    image = s2_collection.median().clip(roi)

    # 4. Training labels: ESA WorldCover 10 m (2021)
    label_source = ee.Image("ESA/WorldCover/v200/2021").clip(roi)

    # 5. Random Forest training
    with st.spinner("Training Random Forest classifier using 10 m spectral features..."):
        try:
            # Sample training points from reference land cover map
            training_points = label_source.sample(
                region=roi,
                scale=100,
                numPixels=1500,
                seed=42,
                geometries=True
            )

            # Extract spectral values at training locations
            training_data = image.sampleRegions(
                collection=training_points,
                properties=['Map'],
                scale=10
            )

            # Train Random Forest classifier
            classifier = ee.Classifier.smileRandomForest(100).train(
                features=training_data,
                classProperty='Map',
                inputProperties=['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
            )

            # Apply classification
            classified = image.classify(classifier)

        except Exception as e:
            st.error(f"Model training failed: {e}")
            return

    # 6. Class definitions and visualization parameters
    # ESA WorldCover classes:
    # 10: Trees | 20: Shrubland | 30: Grassland | 40: Cropland
    # 50: Built-up | 60: Bare / Sparse | 80: Water
    class_values = [10, 20, 30, 40, 50, 60, 80]
    class_names = [
        'Trees',
        'Shrubland',
        'Grassland',
        'Cropland',
        'Built-up',
        'Bare Ground',
        'Water'
    ]
    class_colors = [
        '#006400',
        '#ffbb22',
        '#ffff4c',
        '#f096ff',
        '#fa0000',
        '#b4b4b4',
        '#0064ff'
    ]

    # 7. Area statistics (bar chart)
    st.markdown("### 📊 Land Cover Composition (km²)")
    try:
        area_calc = ee.Image.pixelArea().addBands(classified)
        area_stats = area_calc.reduceRegion(
            reducer=ee.Reducer.sum().group(
                groupField=1,
                groupName='class'
            ),
            geometry=roi,
            scale=100,
            maxPixels=1e10
        ).get('groups').getInfo()

        chart_data = []
        for item in area_stats:
            class_id = int(item['class'])
            if class_id in class_values:
                name = class_names[class_values.index(class_id)]
                chart_data.append({
                    'Category': name,
                    'Area_km2': item['sum'] / 1e6
                })

        st.bar_chart(pd.DataFrame(chart_data).set_index('Category'))

    except:
        st.info("Area statistics could not be computed at the current map scale.")

    # 8. Map visualization
    m = geemap.Map()
    m.add_basemap("SATELLITE")

    # Remap class values for consistent visualization
    vis_image = classified.remap(class_values, list(range(len(class_values))))
    vis_params = {'min': 0, 'max': 6, 'palette': class_colors}

    m.addLayer(
        image,
        {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.3},
        "Sentinel-2 Natural Color"
    )
    m.addLayer(vis_image, vis_params, "Random Forest Classification")

    # Add legend
    legend_dict = dict(zip(class_names, class_colors))
    m.add_legend(title="Land Cover Legend", legend_dict=legend_dict)

    m.centerObject(roi, 10 if country_name == "Qatar" else 7)
    folium_static(m, width=900)

    # 9. Export classified map
    st.markdown("### 📥 Export Results")
    export_url = classified.getDownloadURL({
        'name': f"RF_Classification_{country_name}",
        'scale': 10,
        'region': roi.geometry().bounds().getInfo()['coordinates'],
        'format': 'GEO_TIFF'
    })
    st.link_button("Download Classified GeoTIFF (10 m)", export_url)
