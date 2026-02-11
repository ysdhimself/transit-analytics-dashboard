"""
Static GTFS schedule data loader for Edmonton Transit System.
Downloads and parses the static GTFS ZIP to build a master schedule DataFrame.
"""
import os
import zipfile
from pathlib import Path
from typing import Dict
import pandas as pd
import requests
from src.utils.config import GTFS_STATIC_ZIP_URL


class StaticGTFSLoader:
    """Loader for Edmonton Transit static GTFS schedule data."""
    
    def __init__(self, cache_dir: str = 'data/static_gtfs'):
        """
        Initialize the GTFS loader.
        
        Args:
            cache_dir: Local directory to cache downloaded GTFS files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.gtfs_zip_path = self.cache_dir / 'gtfs.zip'
        
    def download_gtfs_zip(self, force_refresh: bool = False) -> Path:
        """
        Download the static GTFS ZIP file if not already cached.
        
        Args:
            force_refresh: If True, re-download even if file exists
            
        Returns:
            Path to the downloaded ZIP file
        """
        if self.gtfs_zip_path.exists() and not force_refresh:
            print(f"Using cached GTFS ZIP: {self.gtfs_zip_path}")
            return self.gtfs_zip_path
        
        print(f"Downloading GTFS ZIP from {GTFS_STATIC_ZIP_URL}...")
        response = requests.get(GTFS_STATIC_ZIP_URL, timeout=60)
        response.raise_for_status()
        
        with open(self.gtfs_zip_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded {len(response.content)} bytes to {self.gtfs_zip_path}")
        return self.gtfs_zip_path
    
    def extract_gtfs_files(self) -> Dict[str, Path]:
        """
        Extract GTFS text files from the ZIP.
        
        Returns:
            Dictionary mapping file names to their extracted paths
        """
        required_files = ['routes.txt', 'trips.txt', 'stops.txt', 'stop_times.txt']
        optional_files = ['calendar.txt', 'calendar_dates.txt']
        
        extracted_files = {}
        
        with zipfile.ZipFile(self.gtfs_zip_path, 'r') as zip_ref:
            for filename in required_files + optional_files:
                try:
                    zip_ref.extract(filename, self.cache_dir)
                    extracted_files[filename] = self.cache_dir / filename
                    print(f"Extracted {filename}")
                except KeyError:
                    if filename in required_files:
                        raise FileNotFoundError(f"Required file {filename} not found in GTFS ZIP")
                    else:
                        print(f"Optional file {filename} not found, skipping")
        
        return extracted_files
    
    def load_routes(self) -> pd.DataFrame:
        """Load routes.txt as DataFrame."""
        routes_path = self.cache_dir / 'routes.txt'
        df = pd.read_csv(routes_path)
        print(f"Loaded {len(df)} routes")
        return df
    
    def load_trips(self) -> pd.DataFrame:
        """Load trips.txt as DataFrame."""
        trips_path = self.cache_dir / 'trips.txt'
        df = pd.read_csv(trips_path)
        print(f"Loaded {len(df)} trips")
        return df
    
    def load_stops(self) -> pd.DataFrame:
        """Load stops.txt as DataFrame."""
        stops_path = self.cache_dir / 'stops.txt'
        df = pd.read_csv(stops_path)
        print(f"Loaded {len(df)} stops")
        return df
    
    def load_stop_times(self) -> pd.DataFrame:
        """Load stop_times.txt as DataFrame."""
        stop_times_path = self.cache_dir / 'stop_times.txt'
        df = pd.read_csv(stop_times_path)
        print(f"Loaded {len(df)} stop times")
        return df
    
    def load_calendar_dates(self) -> pd.DataFrame:
        """
        Load calendar_dates.txt if available, otherwise fetch from Edmonton Open Data Portal.
        Edmonton does not publish calendar.txt, only calendar_dates.txt.
        
        Returns:
            DataFrame with columns: service_id, date, exception_type
        """
        calendar_dates_path = self.cache_dir / 'calendar_dates.txt'
        
        # Try local file first
        if calendar_dates_path.exists():
            df = pd.read_csv(calendar_dates_path)
            print(f"Loaded {len(df)} calendar dates from local file")
            return df
        
        # Fallback: fetch from Edmonton Open Data Portal API
        print("Fetching calendar_dates from Edmonton Open Data Portal...")
        api_url = "https://data.edmonton.ca/resource/f2sy-bth7.json"
        
        try:
            response = requests.get(api_url, params={'$limit': 10000}, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data)
            # Save to cache for future use
            df.to_csv(calendar_dates_path, index=False)
            print(f"Fetched and cached {len(df)} calendar dates")
            return df
        except Exception as e:
            print(f"Warning: Could not fetch calendar_dates: {e}")
            # Return empty DataFrame with expected schema
            return pd.DataFrame(columns=['service_id', 'date', 'exception_type'])
    
    def build_master_schedule(self) -> pd.DataFrame:
        """
        Build a master schedule DataFrame by joining routes, trips, stops, and stop_times.
        Also joins calendar_dates to derive day_of_week.
        
        Returns:
            DataFrame with comprehensive schedule information including:
            - route_id, route_short_name, route_long_name
            - trip_id, service_id
            - stop_id, stop_name, stop_lat, stop_lon
            - arrival_time, departure_time, stop_sequence
            - day_of_week (derived from date)
        """
        # Load all required tables
        routes = self.load_routes()
        trips = self.load_trips()
        stops = self.load_stops()
        stop_times = self.load_stop_times()
        calendar_dates = self.load_calendar_dates()
        
        # Join stop_times with trips
        schedule = stop_times.merge(
            trips[['trip_id', 'route_id', 'service_id', 'trip_headsign']],
            on='trip_id',
            how='left'
        )
        
        # Join with routes
        schedule = schedule.merge(
            routes[['route_id', 'route_short_name', 'route_long_name', 'route_type']],
            on='route_id',
            how='left'
        )
        
        # Join with stops
        schedule = schedule.merge(
            stops[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']],
            on='stop_id',
            how='left'
        )
        
        # If calendar_dates available, join to get date information
        if not calendar_dates.empty:
            # Convert date column to datetime
            calendar_dates['date'] = pd.to_datetime(calendar_dates['date'], format='%Y%m%d')
            calendar_dates['day_of_week'] = calendar_dates['date'].dt.dayofweek
            
            # Join with schedule on service_id
            schedule = schedule.merge(
                calendar_dates[['service_id', 'date', 'day_of_week']],
                on='service_id',
                how='left'
            )
        
        print(f"Built master schedule with {len(schedule)} records")
        print(f"Columns: {', '.join(schedule.columns)}")
        
        return schedule
    
    def load_all(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Convenience method to download, extract, and build master schedule.
        
        Args:
            force_refresh: If True, re-download GTFS data even if cached
            
        Returns:
            Master schedule DataFrame
        """
        self.download_gtfs_zip(force_refresh=force_refresh)
        self.extract_gtfs_files()
        return self.build_master_schedule()


# Convenience function for quick access
def load_static_schedule(force_refresh: bool = False) -> pd.DataFrame:
    """
    Load the complete static GTFS schedule with one function call.
    
    Args:
        force_refresh: If True, re-download GTFS data
        
    Returns:
        Master schedule DataFrame
    """
    loader = StaticGTFSLoader()
    return loader.load_all(force_refresh=force_refresh)


if __name__ == '__main__':
    # Test the loader
    print("Testing Static GTFS Loader...")
    schedule = load_static_schedule()
    print("\nSchedule preview:")
    print(schedule.head())
    print(f"\nTotal records: {len(schedule)}")
    print(f"\nUnique routes: {schedule['route_id'].nunique()}")
    print(f"\nUnique stops: {schedule['stop_id'].nunique()}")
