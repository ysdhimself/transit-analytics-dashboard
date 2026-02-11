"""
Data quality validation for GTFS-RT records.
Implements null checks, schema validation, and deduplication.
"""
from typing import List, Dict, Set
from datetime import datetime


class DataQualityValidator:
    """Validator for GTFS-RT data quality."""
    
    # Required fields for vehicle positions
    VEHICLE_REQUIRED_FIELDS = ['vehicle_id', 'latitude', 'longitude', 'timestamp']
    
    # Required fields for trip updates
    TRIP_UPDATE_REQUIRED_FIELDS = ['trip_id', 'stop_id', 'feed_timestamp']
    
    def __init__(self):
        """Initialize the validator."""
        self.seen_vehicles: Set[str] = set()
        self.seen_trip_updates: Set[str] = set()
        self.stats = {
            'vehicles_processed': 0,
            'vehicles_valid': 0,
            'vehicles_invalid': 0,
            'vehicles_duplicate': 0,
            'trip_updates_processed': 0,
            'trip_updates_valid': 0,
            'trip_updates_invalid': 0,
            'trip_updates_duplicate': 0
        }
    
    def validate_vehicle_position(self, record: Dict) -> bool:
        """
        Validate a single vehicle position record.
        
        Args:
            record: Vehicle position dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        for field in self.VEHICLE_REQUIRED_FIELDS:
            if field not in record or record[field] is None:
                return False
        
        # Validate latitude/longitude ranges
        lat = record.get('latitude')
        lon = record.get('longitude')
        
        if lat is not None and (lat < -90 or lat > 90):
            return False
        
        if lon is not None and (lon < -180 or lon > 180):
            return False
        
        # Validate speed (if present, should be non-negative)
        speed = record.get('speed')
        if speed is not None and speed < 0:
            return False
        
        return True
    
    def validate_trip_update(self, record: Dict) -> bool:
        """
        Validate a single trip update record.
        
        Args:
            record: Trip update dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        for field in self.TRIP_UPDATE_REQUIRED_FIELDS:
            if field not in record or record[field] is None:
                return False
        
        return True
    
    def deduplicate_vehicle_positions(self, records: List[Dict]) -> List[Dict]:
        """
        Remove duplicate vehicle positions based on vehicle_id + timestamp.
        
        Args:
            records: List of vehicle position records
            
        Returns:
            List of unique records
        """
        unique_records = []
        
        for record in records:
            key = f"{record.get('vehicle_id')}_{record.get('timestamp')}"
            
            if key not in self.seen_vehicles:
                self.seen_vehicles.add(key)
                unique_records.append(record)
            else:
                self.stats['vehicles_duplicate'] += 1
        
        return unique_records
    
    def deduplicate_trip_updates(self, records: List[Dict]) -> List[Dict]:
        """
        Remove duplicate trip updates based on trip_id + stop_id + feed_timestamp.
        
        Args:
            records: List of trip update records
            
        Returns:
            List of unique records
        """
        unique_records = []
        
        for record in records:
            key = f"{record.get('trip_id')}_{record.get('stop_id')}_{record.get('feed_timestamp')}"
            
            if key not in self.seen_trip_updates:
                self.seen_trip_updates.add(key)
                unique_records.append(record)
            else:
                self.stats['trip_updates_duplicate'] += 1
        
        return unique_records
    
    def validate_and_clean_vehicles(self, records: List[Dict]) -> List[Dict]:
        """
        Validate and clean vehicle position records.
        
        Args:
            records: List of vehicle position records
            
        Returns:
            List of validated and deduplicated records
        """
        valid_records = []
        
        for record in records:
            self.stats['vehicles_processed'] += 1
            
            if self.validate_vehicle_position(record):
                self.stats['vehicles_valid'] += 1
                valid_records.append(record)
            else:
                self.stats['vehicles_invalid'] += 1
        
        # Deduplicate
        unique_records = self.deduplicate_vehicle_positions(valid_records)
        
        return unique_records
    
    def validate_and_clean_trip_updates(self, records: List[Dict]) -> List[Dict]:
        """
        Validate and clean trip update records.
        
        Args:
            records: List of trip update records
            
        Returns:
            List of validated and deduplicated records
        """
        valid_records = []
        
        for record in records:
            self.stats['trip_updates_processed'] += 1
            
            if self.validate_trip_update(record):
                self.stats['trip_updates_valid'] += 1
                valid_records.append(record)
            else:
                self.stats['trip_updates_invalid'] += 1
        
        # Deduplicate
        unique_records = self.deduplicate_trip_updates(valid_records)
        
        return unique_records
    
    def get_stats(self) -> Dict:
        """Get validation statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset validation statistics."""
        self.stats = {k: 0 for k in self.stats.keys()}
    
    def reset_dedup_cache(self):
        """Reset deduplication cache (call periodically to prevent memory bloat)."""
        self.seen_vehicles.clear()
        self.seen_trip_updates.clear()


# Convenience functions
def validate_vehicles(records: List[Dict]) -> List[Dict]:
    """Validate and clean vehicle position records."""
    validator = DataQualityValidator()
    return validator.validate_and_clean_vehicles(records)


def validate_trip_updates(records: List[Dict]) -> List[Dict]:
    """Validate and clean trip update records."""
    validator = DataQualityValidator()
    return validator.validate_and_clean_trip_updates(records)


if __name__ == '__main__':
    # Test validation
    print("Testing Data Quality Validator...")
    
    # Sample test data
    test_vehicles = [
        {'vehicle_id': '1', 'latitude': 53.5461, 'longitude': -113.4937, 'timestamp': '2024-01-01T10:00:00'},
        {'vehicle_id': '1', 'latitude': 53.5461, 'longitude': -113.4937, 'timestamp': '2024-01-01T10:00:00'},  # duplicate
        {'vehicle_id': '2', 'latitude': None, 'longitude': -113.4937, 'timestamp': '2024-01-01T10:00:00'},  # invalid
        {'vehicle_id': '3', 'latitude': 53.5500, 'longitude': -113.5000, 'timestamp': '2024-01-01T10:01:00'},
    ]
    
    validator = DataQualityValidator()
    cleaned = validator.validate_and_clean_vehicles(test_vehicles)
    
    print(f"Input: {len(test_vehicles)} records")
    print(f"Output: {len(cleaned)} records")
    print(f"Stats: {validator.get_stats()}")
