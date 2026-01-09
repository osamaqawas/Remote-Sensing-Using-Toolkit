import streamlit as st
import ee
import json
from google.oauth2 import service_account

def authenticate_gee():
    """
    Professional authentication function that explicitly defines scopes
    to avoid the 'invalid_scope' error when initializing Google Earth Engine.
    """
    if "GEE_JSON" in st.secrets:
        try:
            # Convert the JSON string into a Python dictionary
            info = json.loads(st.secrets["GEE_JSON"], strict=False)
            
            # Define the required scope for accessing Earth Engine resources
            # This explicitly resolves the invalid_scope issue
            scopes = ['https://www.googleapis.com/auth/earthengine']
            
            # Create service account credentials with the specified scope
            credentials = service_account.Credentials.from_service_account_info(
                info, scopes=scopes
            )
            
            # Initialize Earth Engine with the authenticated credentials
            ee.Initialize(credentials=credentials)
            
            return True
        
        except Exception as e:
            st.error(f"❌ Failed to connect to Google Earth Engine: {e}")
            return False
    else:
        st.error("❌ GEE_JSON was not found in Streamlit Secrets configuration.")
        return False
