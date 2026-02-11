"""
Tests for dashboard components.
"""
import pytest
import pandas as pd
from dashboard.data_loader import DashboardDataLoader


def test_data_loader_initialization():
    """Test data loader initialization."""
    loader = DashboardDataLoader(use_aws=False)
    assert loader.use_aws == False


def test_mock_vehicle_positions():
    """Test mock vehicle position generation."""
    loader = DashboardDataLoader(use_aws=False)
    vehicles = loader._load_mock_vehicle_positions()
    
    assert isinstance(vehicles, pd.DataFrame)
    assert len(vehicles) > 0
    assert 'vehicle_id' in vehicles.columns
    assert 'latitude' in vehicles.columns
    assert 'longitude' in vehicles.columns
    assert 'route_id' in vehicles.columns


def test_mock_trip_updates():
    """Test mock trip update generation."""
    loader = DashboardDataLoader(use_aws=False)
    trip_updates = loader._load_mock_trip_updates()
    
    assert isinstance(trip_updates, pd.DataFrame)
    assert len(trip_updates) > 0
    assert 'trip_id' in trip_updates.columns
    assert 'route_id' in trip_updates.columns
    assert 'delay_minutes' in trip_updates.columns


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
