import ee

def get_country_roi(area_name):
    """
    Fetches the geometry for a specific Jordan Governorate (ADM1).
    Args:
        area_name (str): Name of the Jordanian governorate.
    Returns:
        ee.FeatureCollection: The geometry of the selected area.
    """
    try:
        # Load the Global Administrative Unit Layers (Level 1 for Governorates)
        jordan_admin = ee.FeatureCollection("FAO/GAUL/2015/level1") \
            .filter(ee.Filter.eq('ADM0_NAME', 'Jordan'))
        
        # Mapping common names to GAUL names to prevent errors
        name_mapping = {
            "Amman": "Amman",
            "Irbid": "Irbid",
            "Zarqa": "Az Zarqa",
            "Aqaba": "Al Aqabah",
            "Madaba": "Madaba",
            "Mafraq": "Al Mafraq",
            "Balqa": "Al Balqa",
            "Jerash": "Jarash",
            "Karak": "Al Karak",
            "Ma'an": "Ma'an",
            "Tafilah": "At Tafilah",
            "Ajloun": "Ajlun"
        }
        
        # Use the mapped name if it exists, otherwise use the input name
        search_name = name_mapping.get(area_name, area_name)
        
        # Filter the collection
        roi = jordan_admin.filter(ee.Filter.eq('ADM1_NAME', search_name))
        
        # Check if ROI exists, if not, try a 'contains' search as a safety net
        if roi.size().getInfo() == 0:
            roi = jordan_admin.filter(ee.Filter.stringContains('ADM1_NAME', area_name))
            
        return roi

    except Exception as e:
        # Fallback to Jordan Country level if city fails
        print(f"Error fetching ROI for {area_name}: {e}")
        return ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017") \
                 .filter(ee.Filter.eq('country_na', 'Jordan'))
