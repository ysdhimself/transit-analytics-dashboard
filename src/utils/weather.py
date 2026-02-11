"""
OpenWeatherMap API client for fetching weather data (P1 - Nice to Have feature).
"""
import requests
from typing import Optional, Dict
from src.utils.config import OPENWEATHER_API_KEY, OPENWEATHER_LAT, OPENWEATHER_LON


def get_current_weather() -> Optional[Dict]:
    """
    Fetch current weather data for Edmonton from OpenWeatherMap API.
    
    Returns:
        Dictionary with weather data including temperature, or None if API key not configured
    """
    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == 'your_openweathermap_api_key':
        return None
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': OPENWEATHER_LAT,
        'lon': OPENWEATHER_LON,
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric'  # Celsius
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'weather': data['weather'][0]['main'],
            'description': data['weather'][0]['description']
        }
    except Exception as e:
        print(f"Warning: Could not fetch weather data: {e}")
        return None


def get_temperature() -> Optional[float]:
    """
    Get only the temperature value (simplified for ML feature).
    
    Returns:
        Temperature in Celsius, or None if unavailable
    """
    weather_data = get_current_weather()
    return weather_data['temperature'] if weather_data else None
