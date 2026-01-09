🌍 Remote Sensing Applications Toolkit (Google Colab & GEE)

This repository provides a modular remote sensing toolkit built for Google Colab using Google Earth Engine (GEE).
It covers key environmental and geospatial applications widely used in research and operational monitoring.

The project is designed for:

🎓 Students

🔬 Researchers

🛰️ Remote sensing & GIS practitioners

📂 Project Structure
remote-sensing-toolkit/
│
├── modules/
│   ├── air_quality.py
│   ├── flood_mapping.py
│   ├── land_cover.py
│   ├── lst.py
│   ├── rs_indices.py
│   ├── wildfire.py
│   └── __init__.py
│
├── notebooks/
│   └── main_app.ipynb
│
├── requirements.txt
└── README.md

🧩 Available Modules
🌫️ Air Quality (air_quality.py)

Aerosol Optical Depth (AOD)

Air quality proxies using satellite data

Temporal analysis and visualization

🌊 Flood Mapping (flood_mapping.py)

Flood detection using Sentinel-1 SAR

Pre- and post-event comparison

Water extent extraction

🌱 Land Use / Land Cover (land_cover.py)

LULC classification

Supervised & unsupervised approaches

Change detection

🔥 Wildfire Detection (wildfire.py)

Active fire detection

Burned area mapping

Fire severity indices (e.g., NBR, dNBR)

🌡️ Land Surface Temperature (lst.py)

LST retrieval from Landsat & Sentinel data

Urban heat island analysis

Time-series LST monitoring

📊 Remote Sensing Indices (rs_indices.py)

Includes:

NDVI

EVI

NDBI

NDWI

NBR

Custom spectral indices

🚀 How to Use (Google Colab)

1️⃣ Open Google Colab
2️⃣ Clone the repository:

!git clone https://github.com/your-username/remote-sensing-toolkit.git


3️⃣ Authenticate Google Earth Engine:

import ee
ee.Authenticate()
ee.Initialize()


4️⃣ Import any module:

from modules.wildfire import *
from modules.rs_indices import *

🛠️ Requirements

Python 3.9+

Google Earth Engine

geemap

rasterio

numpy

matplotlib

Install dependencies:

pip install -r requirements.txt

🎯 Future Enhancements

DEM-based analysis (slope, aspect, hillshade)

Drought monitoring indices (SPI, VHI)

Time-series trend analysis

Machine learning integration

Streamlit web application

🤝 Contributions

Contributions, ideas, and improvements are welcome!
Feel free to open issues or submit pull requests.

📜 License

This project is licensed under the MIT License.

✉️ Contact

Developed by Osama Alqawasmeh
📍 GIS & Remote Sensing | Earth Observation
🔗 LinkedIn / GitHub