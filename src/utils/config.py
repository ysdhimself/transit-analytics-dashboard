"""
Centralized configuration loader for environment variables.
Supports both .env files (local development) and Streamlit secrets (cloud deployment).
"""
import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    # Load .env from project root
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv not available in Lambda

# Try Streamlit secrets as fallback
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get configuration value from environment variables or Streamlit secrets.
    
    Args:
        key: Configuration key (can use dot notation for nested Streamlit secrets)
        default: Default value if key not found
    
    Returns:
        Configuration value or default
    """
    # Try environment variable first
    value = os.getenv(key)
    if value:
        return value
    
    # Try Streamlit secrets (supports nested keys like 'aws.AWS_ACCESS_KEY_ID')
    if STREAMLIT_AVAILABLE and hasattr(st, 'secrets'):
        try:
            if '.' in key:
                section, subkey = key.split('.', 1)
                return st.secrets[section][subkey]
            else:
                return st.secrets.get(key)
        except (KeyError, FileNotFoundError):
            pass
    
    return default


# AWS Configuration
AWS_ACCESS_KEY_ID = get_config('AWS_ACCESS_KEY_ID') or get_config('aws.AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = get_config('AWS_SECRET_ACCESS_KEY') or get_config('aws.AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = get_config('AWS_DEFAULT_REGION') or get_config('AWS_REGION') or get_config('aws.AWS_DEFAULT_REGION') or get_config('aws.AWS_REGION') or 'us-east-2'
S3_BUCKET_NAME = get_config('S3_BUCKET_NAME', 'ets-transit-data') or get_config('aws.S3_BUCKET_NAME', 'ets-transit-data')
DYNAMODB_TABLE_NAME = get_config('DYNAMODB_TABLE_NAME', 'ets_transit_processed') or get_config('aws.DYNAMODB_TABLE_NAME', 'ets_transit_processed')

# GTFS Data Sources (public, no auth required)
GTFS_RT_VEHICLE_POSITIONS_URL = get_config(
    'GTFS_RT_VEHICLE_POSITIONS_URL',
    'https://gtfs.edmonton.ca/TMGTFSRealTimeWebService/Vehicle/VehiclePositions.pb'
)
GTFS_RT_TRIP_UPDATES_URL = get_config(
    'GTFS_RT_TRIP_UPDATES_URL',
    'https://gtfs.edmonton.ca/TMGTFSRealTimeWebService/TripUpdate/TripUpdates.pb'
)
GTFS_STATIC_ZIP_URL = get_config(
    'GTFS_STATIC_ZIP_URL',
    'https://gtfs.edmonton.ca/TMGTFSRealTimeWebService/GTFS/gtfs.zip'
)

# OpenWeatherMap (P1 - Optional)
OPENWEATHER_API_KEY = get_config('OPENWEATHER_API_KEY') or get_config('apis.OPENWEATHER_API_KEY')
OPENWEATHER_LAT = float(get_config('OPENWEATHER_LAT', '53.5461'))
OPENWEATHER_LON = float(get_config('OPENWEATHER_LON', '-113.4937'))
