"""
S3 uploader for GTFS-RT data.
Uploads validated JSON to S3 with date-based partitioning.
"""
import json
import boto3
import os
from datetime import datetime
from typing import List, Dict
from botocore.exceptions import ClientError

# Get config from environment variables (Lambda)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-2')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'ets-transit-data')


class S3Uploader:
    """Uploader for GTFS-RT data to AWS S3."""
    
    def __init__(self, bucket_name: str = None):
        """
        Initialize the S3 uploader.
        
        Args:
            bucket_name: S3 bucket name (defaults to config value)
        """
        self.bucket_name = bucket_name or S3_BUCKET_NAME
        
        # Initialize S3 client - use IAM role (default) in Lambda environment
        self.s3_client = boto3.client('s3', region_name=AWS_DEFAULT_REGION)
    
    def generate_s3_key(self, data_type: str, timestamp: datetime = None) -> str:
        """
        Generate S3 key with date-based partitioning.
        
        Args:
            data_type: Type of data ('vehicles' or 'trip_updates')
            timestamp: Timestamp for partitioning (defaults to now)
            
        Returns:
            S3 key string like 'transit/vehicles/20240101/20240101_100000.json'
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        date_str = timestamp.strftime('%Y%m%d')
        time_str = timestamp.strftime('%Y%m%d_%H%M%S')
        
        return f"transit/{data_type}/{date_str}/{time_str}.json"
    
    def upload_json(self, data: List[Dict], data_type: str, timestamp: datetime = None) -> str:
        """
        Upload data as JSON to S3.
        
        Args:
            data: List of records to upload
            data_type: Type of data ('vehicles' or 'trip_updates')
            timestamp: Timestamp for partitioning
            
        Returns:
            S3 key of uploaded file
        """
        if not data:
            print(f"No {data_type} data to upload")
            return None
        
        s3_key = self.generate_s3_key(data_type, timestamp)
        
        # Convert to JSON
        json_data = json.dumps(data, indent=2)
        
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json'
            )
            
            print(f"Uploaded {len(data)} {data_type} records to s3://{self.bucket_name}/{s3_key}")
            return s3_key
        
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return None
    
    def upload_vehicles(self, vehicles: List[Dict], timestamp: datetime = None) -> str:
        """
        Upload vehicle position data to S3.
        
        Args:
            vehicles: List of vehicle position records
            timestamp: Timestamp for partitioning
            
        Returns:
            S3 key of uploaded file
        """
        return self.upload_json(vehicles, 'vehicles', timestamp)
    
    def upload_trip_updates(self, trip_updates: List[Dict], timestamp: datetime = None) -> str:
        """
        Upload trip update data to S3.
        
        Args:
            trip_updates: List of trip update records
            timestamp: Timestamp for partitioning
            
        Returns:
            S3 key of uploaded file
        """
        return self.upload_json(trip_updates, 'trip_updates', timestamp)
    
    def upload_all(self, vehicles: List[Dict], trip_updates: List[Dict], timestamp: datetime = None) -> Dict[str, str]:
        """
        Upload both vehicles and trip updates.
        
        Args:
            vehicles: List of vehicle position records
            trip_updates: List of trip update records
            timestamp: Timestamp for partitioning
            
        Returns:
            Dictionary with 'vehicles' and 'trip_updates' S3 keys
        """
        return {
            'vehicles': self.upload_vehicles(vehicles, timestamp),
            'trip_updates': self.upload_trip_updates(trip_updates, timestamp)
        }
    
    def list_files(self, data_type: str, date: str = None) -> List[str]:
        """
        List files in S3 for a given data type and date.
        
        Args:
            data_type: Type of data ('vehicles' or 'trip_updates')
            date: Date string in YYYYMMDD format (defaults to today)
            
        Returns:
            List of S3 keys
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        prefix = f"transit/{data_type}/{date}/"
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            else:
                return []
        
        except ClientError as e:
            print(f"Error listing S3 objects: {e}")
            return []


# Convenience functions
def upload_to_s3(vehicles: List[Dict], trip_updates: List[Dict]) -> Dict[str, str]:
    """Upload data to S3."""
    uploader = S3Uploader()
    return uploader.upload_all(vehicles, trip_updates)


if __name__ == '__main__':
    # Test uploader (dry run - requires AWS credentials)
    print("Testing S3 Uploader...")
    
    # Sample test data
    test_vehicles = [
        {'vehicle_id': '1', 'latitude': 53.5461, 'longitude': -113.4937, 'timestamp': '2024-01-01T10:00:00'}
    ]
    
    uploader = S3Uploader()
    print(f"Would upload to: {uploader.generate_s3_key('vehicles')}")
