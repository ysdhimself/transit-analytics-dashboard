"""
Tests for data ingestion modules.
"""
import pytest
from datetime import datetime
from src.ingestion.data_quality import DataQualityValidator


def test_vehicle_position_validation():
    """Test vehicle position validation."""
    validator = DataQualityValidator()
    
    # Valid record
    valid_record = {
        'vehicle_id': '123',
        'latitude': 53.5461,
        'longitude': -113.4937,
        'timestamp': '2024-01-01T10:00:00'
    }
    assert validator.validate_vehicle_position(valid_record) == True
    
    # Invalid - missing required field
    invalid_record = {
        'vehicle_id': '123',
        'latitude': 53.5461,
        # missing longitude
        'timestamp': '2024-01-01T10:00:00'
    }
    assert validator.validate_vehicle_position(invalid_record) == False
    
    # Invalid - out of range latitude
    invalid_record = {
        'vehicle_id': '123',
        'latitude': 95.0,  # Invalid
        'longitude': -113.4937,
        'timestamp': '2024-01-01T10:00:00'
    }
    assert validator.validate_vehicle_position(invalid_record) == False


def test_trip_update_validation():
    """Test trip update validation."""
    validator = DataQualityValidator()
    
    # Valid record
    valid_record = {
        'trip_id': 'trip123',
        'stop_id': 'stop456',
        'feed_timestamp': '2024-01-01T10:00:00'
    }
    assert validator.validate_trip_update(valid_record) == True
    
    # Invalid - missing required field
    invalid_record = {
        'trip_id': 'trip123',
        # missing stop_id
        'feed_timestamp': '2024-01-01T10:00:00'
    }
    assert validator.validate_trip_update(invalid_record) == False


def test_deduplication():
    """Test record deduplication."""
    validator = DataQualityValidator()
    
    records = [
        {'vehicle_id': '1', 'latitude': 53.5, 'longitude': -113.5, 'timestamp': '2024-01-01T10:00:00'},
        {'vehicle_id': '1', 'latitude': 53.5, 'longitude': -113.5, 'timestamp': '2024-01-01T10:00:00'},  # Duplicate
        {'vehicle_id': '2', 'latitude': 53.6, 'longitude': -113.6, 'timestamp': '2024-01-01T10:01:00'},
    ]
    
    unique = validator.deduplicate_vehicle_positions(records)
    assert len(unique) == 2
    assert validator.stats['vehicles_duplicate'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
