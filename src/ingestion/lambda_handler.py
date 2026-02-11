"""
AWS Lambda handler for GTFS-RT data ingestion.
Orchestrates the complete ETL pipeline: fetch, parse, validate, upload to S3, and write to DynamoDB.
"""
import json
from datetime import datetime
from ingestion.gtfs_rt_parser import GTFSRealtimeParser
from ingestion.data_quality import DataQualityValidator
from ingestion.s3_uploader import S3Uploader
from ingestion.dynamodb_writer import DynamoDBWriter


def handler(event, context):
    """
    Lambda handler function for GTFS-RT data ingestion.
    
    Args:
        event: Lambda event (from EventBridge scheduler)
        context: Lambda context
        
    Returns:
        Response with status code and statistics
    """
    print(f"Starting GTFS-RT ingestion at {datetime.now().isoformat()}")
    
    try:
        # Step 1: Parse GTFS-RT feeds
        print("Step 1: Parsing GTFS-RT feeds...")
        parser = GTFSRealtimeParser()
        data = parser.parse_all()
        
        vehicles = data['vehicles']
        trip_updates = data['trip_updates']
        
        print(f"Parsed {len(vehicles)} vehicles, {len(trip_updates)} trip updates")
        
        # Step 2: Validate and clean data
        print("Step 2: Validating and cleaning data...")
        validator = DataQualityValidator()
        
        clean_vehicles = validator.validate_and_clean_vehicles(vehicles)
        clean_trip_updates = validator.validate_and_clean_trip_updates(trip_updates)
        
        stats = validator.get_stats()
        print(f"Validation stats: {stats}")
        
        # Step 3: Upload to S3
        print("Step 3: Uploading to S3...")
        uploader = S3Uploader()
        timestamp = datetime.now()
        
        s3_keys = uploader.upload_all(clean_vehicles, clean_trip_updates, timestamp)
        print(f"Uploaded to S3: {s3_keys}")
        
        # Step 4: Write to DynamoDB
        print("Step 4: Writing to DynamoDB...")
        db_writer = DynamoDBWriter()
        
        vehicles_written = db_writer.batch_write_vehicles(clean_vehicles)
        trip_updates_written = db_writer.batch_write_trip_updates(clean_trip_updates)
        
        print(f"Written to DynamoDB: {vehicles_written} vehicles, {trip_updates_written} trip updates")
        
        # Prepare response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'timestamp': timestamp.isoformat(),
                'parsed': {
                    'vehicles': len(vehicles),
                    'trip_updates': len(trip_updates)
                },
                'cleaned': {
                    'vehicles': len(clean_vehicles),
                    'trip_updates': len(clean_trip_updates)
                },
                'validation_stats': stats,
                's3_keys': s3_keys,
                'dynamodb_written': {
                    'vehicles': vehicles_written,
                    'trip_updates': trip_updates_written
                }
            })
        }
        
        print(f"Ingestion completed successfully")
        return response
    
    except Exception as e:
        print(f"Error in Lambda handler: {e}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }


# For local testing
if __name__ == '__main__':
    print("Testing Lambda handler locally...")
    
    # Simulate Lambda event and context
    test_event = {}
    test_context = type('obj', (object,), {
        'function_name': 'test',
        'request_id': 'test-123'
    })
    
    result = handler(test_event, test_context)
    print(f"\nResult: {json.dumps(json.loads(result['body']), indent=2)}")
