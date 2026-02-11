"""
Data loader for Streamlit dashboard.
Fetches data from S3/DynamoDB or local files for development.
"""
import pandas as pd
import streamlit as st
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import json
import boto3
from botocore.exceptions import ClientError
from pathlib import Path


class DashboardDataLoader:
    """Loader for dashboard data from various sources."""
    
    def __init__(self, use_aws: bool = True):
        """
        Initialize the data loader.
        
        Args:
            use_aws: If True, attempt to use AWS services; if False, use local files
        """
        self.use_aws = use_aws
        self.s3_client = None
        self.dynamodb = None
        self._used_mock_vehicles = False
        self._used_mock_trips = False
        
        if use_aws:
            try:
                import sys
                from pathlib import Path
                # Add project root to path for imports
                project_root = Path(__file__).parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                from src.utils.config import (
                    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
                    AWS_DEFAULT_REGION, S3_BUCKET_NAME, DYNAMODB_TABLE_NAME
                )
                
                self.bucket_name = S3_BUCKET_NAME
                self.table_name = DYNAMODB_TABLE_NAME
                
                # Initialize AWS clients
                if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
                    self.s3_client = boto3.client(
                        's3',
                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                        region_name=AWS_DEFAULT_REGION
                    )
                    dynamodb_resource = boto3.resource(
                        'dynamodb',
                        aws_access_key_id=AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                        region_name=AWS_DEFAULT_REGION
                    )
                else:
                    self.s3_client = boto3.client('s3', region_name=AWS_DEFAULT_REGION)
                    dynamodb_resource = boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)
                
                self.dynamodb_table = dynamodb_resource.Table(self.table_name)
                
            except Exception as e:
                print(f"Warning: Could not initialize AWS clients: {e}")
                self.use_aws = False
    
    @st.cache_data(ttl=30)  # Cache for 30 seconds
    def load_vehicle_positions(_self) -> pd.DataFrame:
        """
        Load recent vehicle positions.
        
        Returns:
            DataFrame with vehicle position data
        """
        if _self.use_aws and _self.dynamodb_table:
            try:
                # Query recent vehicles from DynamoDB - scan all pages to get more vehicles
                items = []
                response = _self.dynamodb_table.scan(
                    FilterExpression='record_type = :type',
                    ExpressionAttributeValues={':type': 'vehicle_position'}
                )
                items.extend(response.get('Items', []))
                
                # Continue scanning if there are more pages (up to 5000 items total)
                while 'LastEvaluatedKey' in response and len(items) < 5000:
                    response = _self.dynamodb_table.scan(
                        FilterExpression='record_type = :type',
                        ExpressionAttributeValues={':type': 'vehicle_position'},
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                    items.extend(response.get('Items', []))
                
                
                if items:
                    # Convert DynamoDB Decimal to float
                    from decimal import Decimal
                    def decimal_to_float(obj):
                        if isinstance(obj, Decimal):
                            return float(obj)
                        return obj
                    
                    items = [{k: decimal_to_float(v) for k, v in item.items()} for item in items]
                    
                    df = pd.DataFrame(items)
                    
                    # Convert timestamp if present
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
                        
                        # Keep only most recent position per vehicle (last 10 minutes to account for timezone)
                        from datetime import datetime, timedelta, timezone
                        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=10)
                        df = df[df['timestamp'] > cutoff_time]
                        
                        # Group by vehicle_id and keep most recent
                        if not df.empty and 'vehicle_id' in df.columns:
                            df = df.sort_values('timestamp').groupby('vehicle_id').last().reset_index()
                    _self._used_mock_vehicles = False
                    return df
            
            except Exception as e:
                print(f"Error loading from DynamoDB: {e}")
        
        # Fallback: load from local mock data
        _self._used_mock_vehicles = True
        return _self._load_mock_vehicle_positions()
    
    @st.cache_data(ttl=30)
    def load_trip_updates(_self) -> pd.DataFrame:
        """
        Load recent trip updates with delays.
        
        Returns:
            DataFrame with trip update data
        """
        if _self.use_aws and _self.dynamodb_table:
            try:
                # Query recent trip updates from DynamoDB - scan all pages
                items = []
                response = _self.dynamodb_table.scan(
                    FilterExpression='record_type = :type',
                    ExpressionAttributeValues={':type': 'trip_update'}
                )
                items.extend(response.get('Items', []))
                
                # Continue scanning if there are more pages (up to 5000 items total)
                while 'LastEvaluatedKey' in response and len(items) < 5000:
                    response = _self.dynamodb_table.scan(
                        FilterExpression='record_type = :type',
                        ExpressionAttributeValues={':type': 'trip_update'},
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                    items.extend(response.get('Items', []))
                
                if items:
                    # Convert DynamoDB Decimal to float
                    from decimal import Decimal
                    def decimal_to_float(obj):
                        if isinstance(obj, Decimal):
                            return float(obj)
                        return obj
                    
                    items = [{k: decimal_to_float(v) for k, v in item.items()} for item in items]
                    
                    df = pd.DataFrame(items)
                    df['feed_timestamp'] = pd.to_datetime(df['feed_timestamp'], errors='coerce', utc=True)
                    
                    # Filter to recent data (last hour)
                    from datetime import datetime, timedelta, timezone
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
                    df = df[df['feed_timestamp'] > cutoff_time]
                    
                    # Calculate delay_minutes if not present
                    if 'delay_minutes' not in df.columns and 'arrival_delay' in df.columns:
                        df['delay_minutes'] = df['arrival_delay'] / 60.0
                    elif 'delay_minutes' not in df.columns and 'departure_delay' in df.columns:
                        df['delay_minutes'] = df['departure_delay'] / 60.0
                    
                    # Group by route and trip to get average delay per trip
                    if 'route_id' in df.columns and 'trip_id' in df.columns:
                        df = df.groupby(['route_id', 'trip_id', 'vehicle_id']).agg({
                            'delay_minutes': 'mean',
                            'feed_timestamp': 'first'
                        }).reset_index()
                    
                    _self._used_mock_trips = False
                    return df
            
            except Exception as e:
                print(f"Error loading from DynamoDB: {e}")
        
        # Fallback: load from local mock data
        _self._used_mock_trips = True
        return _self._load_mock_trip_updates()
    
    def _load_mock_vehicle_positions(self) -> pd.DataFrame:
        """Generate mock vehicle position data for development."""
        import numpy as np
        
        # Edmonton coordinates
        base_lat, base_lon = 53.5461, -113.4937
        
        num_vehicles = 50
        
        data = {
            'vehicle_id': [f'vehicle_{i}' for i in range(num_vehicles)],
            'route_id': np.random.choice(['1', '2', '3', '4', '5', '7', '8', '9'], num_vehicles),
            'latitude': base_lat + np.random.uniform(-0.1, 0.1, num_vehicles),
            'longitude': base_lon + np.random.uniform(-0.1, 0.1, num_vehicles),
            'speed': np.random.uniform(0, 60, num_vehicles),
            'timestamp': [datetime.now() - timedelta(minutes=int(np.random.randint(0, 5))) for _ in range(num_vehicles)]
        }
        
        return pd.DataFrame(data)
    
    def _load_mock_trip_updates(self) -> pd.DataFrame:
        """Generate mock trip update data for development."""
        import numpy as np
        
        num_updates = 200
        
        routes = ['1', '2', '3', '4', '5', '7', '8', '9']
        hours = list(range(24))
        
        data = {
            'trip_id': [f'trip_{i}' for i in range(num_updates)],
            'route_id': np.random.choice(routes, num_updates),
            'stop_id': [f'stop_{i}' for i in np.random.randint(1, 100, num_updates)],
            'arrival_delay': np.random.normal(120, 180, num_updates),  # seconds
            'delay_minutes': np.random.normal(2, 3, num_updates),
            'feed_timestamp': [
                datetime.now() - timedelta(hours=int(np.random.choice(hours)), minutes=int(np.random.randint(0, 60)))
                for _ in range(num_updates)
            ],
            'route_short_name': np.random.choice(routes, num_updates),
            'route_long_name': [f'Route {r}' for r in np.random.choice(routes, num_updates)]
        }
        
        df = pd.DataFrame(data)
        df['hour'] = pd.to_datetime(df['feed_timestamp']).dt.hour
        
        return df


@st.cache_data(ttl=30)
def load_dashboard_data() -> Dict:
    """
    Load all data needed for the dashboard.
    
    Returns:
        Dictionary with 'vehicles', 'trip_updates', and 'data_source' ('live' or 'mock')
    """
    loader = DashboardDataLoader()
    vehicles = loader.load_vehicle_positions()
    trip_updates = loader.load_trip_updates()
    data_source = 'mock' if (loader._used_mock_vehicles or loader._used_mock_trips) else 'live'
    return {
        'vehicles': vehicles,
        'trip_updates': trip_updates,
        'data_source': data_source
    }
