"""
DynamoDB writer for processed GTFS-RT records.
Stores data for fast dashboard queries.
"""
import boto3
import os
from datetime import datetime
from typing import List, Dict
from decimal import Decimal
from botocore.exceptions import ClientError

# Get config from environment variables (Lambda)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-2')
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'ets_transit_processed')


class DynamoDBWriter:
    """Writer for GTFS-RT data to AWS DynamoDB."""
    
    def __init__(self, table_name: str = None):
        """
        Initialize the DynamoDB writer.
        
        Args:
            table_name: DynamoDB table name (defaults to config value)
        """
        self.table_name = table_name or DYNAMODB_TABLE_NAME
        
        # Initialize DynamoDB resource - use IAM role (default) in Lambda environment
        dynamodb = boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)
        self.table = dynamodb.Table(self.table_name)
    
    def convert_floats_to_decimal(self, obj):
        """
        Recursively convert float to Decimal for DynamoDB compatibility.
        
        Args:
            obj: Object to convert
            
        Returns:
            Object with floats converted to Decimal
        """
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self.convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_floats_to_decimal(item) for item in obj]
        return obj
    
    def write_vehicle_position(self, vehicle: Dict) -> bool:
        """
        Write a single vehicle position record to DynamoDB.
        
        Args:
            vehicle: Vehicle position dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert floats to Decimal
            vehicle = self.convert_floats_to_decimal(vehicle)
            
            # Add record type and timestamp for querying
            item = {
                'pk': f"VEHICLE#{vehicle.get('route_id', 'UNKNOWN')}",
                'sk': f"{vehicle.get('timestamp', datetime.now().isoformat())}#{vehicle.get('vehicle_id', 'UNKNOWN')}",
                'record_type': 'vehicle_position',
                **vehicle
            }
            
            self.table.put_item(Item=item)
            return True
        
        except ClientError as e:
            print(f"Error writing vehicle to DynamoDB: {e}")
            return False
    
    def write_trip_update(self, trip_update: Dict) -> bool:
        """
        Write a single trip update record to DynamoDB.
        
        Args:
            trip_update: Trip update dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert floats to Decimal
            trip_update = self.convert_floats_to_decimal(trip_update)
            
            # Add record type and timestamp for querying
            item = {
                'pk': f"TRIP#{trip_update.get('route_id', 'UNKNOWN')}",
                'sk': f"{trip_update.get('feed_timestamp', datetime.now().isoformat())}#{trip_update.get('trip_id', 'UNKNOWN')}#{trip_update.get('stop_id', 'UNKNOWN')}",
                'record_type': 'trip_update',
                **trip_update
            }
            
            self.table.put_item(Item=item)
            return True
        
        except ClientError as e:
            print(f"Error writing trip update to DynamoDB: {e}")
            return False
    
    def batch_write_vehicles(self, vehicles: List[Dict]) -> int:
        """
        Batch write vehicle position records to DynamoDB.
        
        Args:
            vehicles: List of vehicle position dictionaries
            
        Returns:
            Number of successfully written records
        """
        success_count = 0
        
        # DynamoDB batch write supports up to 25 items at a time
        batch_size = 25
        
        for i in range(0, len(vehicles), batch_size):
            batch = vehicles[i:i + batch_size]
            
            with self.table.batch_writer() as writer:
                for vehicle in batch:
                    try:
                        vehicle = self.convert_floats_to_decimal(vehicle)
                        
                        item = {
                            'pk': f"VEHICLE#{vehicle.get('route_id', 'UNKNOWN')}",
                            'sk': f"{vehicle.get('timestamp', datetime.now().isoformat())}#{vehicle.get('vehicle_id', 'UNKNOWN')}",
                            'record_type': 'vehicle_position',
                            **vehicle
                        }
                        
                        writer.put_item(Item=item)
                        success_count += 1
                    
                    except Exception as e:
                        print(f"Error in batch write for vehicle: {e}")
        
        print(f"Wrote {success_count}/{len(vehicles)} vehicle positions to DynamoDB")
        return success_count
    
    def batch_write_trip_updates(self, trip_updates: List[Dict]) -> int:
        """
        Batch write trip update records to DynamoDB.
        
        Args:
            trip_updates: List of trip update dictionaries
            
        Returns:
            Number of successfully written records
        """
        success_count = 0
        
        # DynamoDB batch write supports up to 25 items at a time
        batch_size = 25
        
        for i in range(0, len(trip_updates), batch_size):
            batch = trip_updates[i:i + batch_size]
            
            with self.table.batch_writer() as writer:
                for trip_update in batch:
                    try:
                        trip_update = self.convert_floats_to_decimal(trip_update)
                        
                        item = {
                            'pk': f"TRIP#{trip_update.get('route_id', 'UNKNOWN')}",
                            'sk': f"{trip_update.get('feed_timestamp', datetime.now().isoformat())}#{trip_update.get('trip_id', 'UNKNOWN')}#{trip_update.get('stop_id', 'UNKNOWN')}",
                            'record_type': 'trip_update',
                            **trip_update
                        }
                        
                        writer.put_item(Item=item)
                        success_count += 1
                    
                    except Exception as e:
                        print(f"Error in batch write for trip update: {e}")
        
        print(f"Wrote {success_count}/{len(trip_updates)} trip updates to DynamoDB")
        return success_count
    
    def query_recent_vehicles(self, route_id: str = None, limit: int = 100) -> List[Dict]:
        """
        Query recent vehicle positions.
        
        Args:
            route_id: Filter by route ID (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of vehicle position records
        """
        try:
            if route_id:
                response = self.table.query(
                    KeyConditionExpression='pk = :pk',
                    ExpressionAttributeValues={':pk': f"VEHICLE#{route_id}"},
                    Limit=limit,
                    ScanIndexForward=False  # Most recent first
                )
            else:
                # Scan for all vehicles (less efficient, use sparingly)
                response = self.table.scan(
                    FilterExpression='record_type = :type',
                    ExpressionAttributeValues={':type': 'vehicle_position'},
                    Limit=limit
                )
            
            return response.get('Items', [])
        
        except ClientError as e:
            print(f"Error querying vehicles: {e}")
            return []


# Convenience functions
def write_to_dynamodb(vehicles: List[Dict], trip_updates: List[Dict]) -> Dict[str, int]:
    """Write data to DynamoDB."""
    writer = DynamoDBWriter()
    return {
        'vehicles': writer.batch_write_vehicles(vehicles),
        'trip_updates': writer.batch_write_trip_updates(trip_updates)
    }


if __name__ == '__main__':
    # Test writer (dry run - requires AWS credentials and DynamoDB table)
    print("Testing DynamoDB Writer...")
    
    # Sample test data
    test_vehicle = {
        'vehicle_id': '1',
        'route_id': 'TEST',
        'latitude': 53.5461,
        'longitude': -113.4937,
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"Would write vehicle to DynamoDB table: {DYNAMODB_TABLE_NAME}")
