"""
Tests for data processing modules.
"""
import pytest
import pandas as pd
from src.processing.delay_calculator import DelayCalculator
from src.processing.feature_engineer import FeatureEngineer


def test_delay_calculation():
    """Test delay calculation from trip updates."""
    # Create sample static schedule
    schedule = pd.DataFrame({
        'trip_id': ['trip1'],
        'stop_id': ['stop1'],
        'arrival_time': ['10:00:00'],
        'route_id': ['route1'],
        'route_short_name': ['1'],
        'route_long_name': ['Route 1'],
        'stop_name': ['Stop 1'],
        'stop_lat': [53.5],
        'stop_lon': [-113.5]
    })
    
    calculator = DelayCalculator(schedule)
    
    # Sample trip updates
    trip_updates = [
        {
            'trip_id': 'trip1',
            'stop_id': 'stop1',
            'arrival_delay': 120,  # 2 minutes late
            'feed_timestamp': '2024-01-01T10:02:00'
        }
    ]
    
    delays_df = calculator.calculate_delay_from_trip_updates(trip_updates)
    
    assert len(delays_df) == 1
    assert 'delay_minutes' in delays_df.columns
    assert delays_df.iloc[0]['delay_minutes'] == 2.0


def test_feature_engineering():
    """Test feature engineering."""
    # Sample data
    data = pd.DataFrame({
        'trip_id': ['trip1', 'trip2'],
        'route_id': ['route1', 'route2'],
        'stop_id': ['stop1', 'stop2'],
        'feed_timestamp': ['2024-01-15T08:30:00', '2024-01-20T17:45:00'],
        'delay_minutes': [2.5, 5.0]
    })
    
    engineer = FeatureEngineer()
    features = engineer.create_feature_set(data)
    
    # Check that temporal features were added
    assert 'hour_of_day' in features.columns
    assert 'day_of_week' in features.columns
    assert 'is_rush_hour' in features.columns
    assert 'is_weekend' in features.columns
    assert 'route_id_encoded' in features.columns
    
    # Check values
    assert features.iloc[0]['hour_of_day'] == 8
    assert features.iloc[0]['is_rush_hour'] == 1  # 8:30 AM is rush hour
    assert features.iloc[1]['hour_of_day'] == 17
    assert features.iloc[1]['is_rush_hour'] == 1  # 5:45 PM is rush hour


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
