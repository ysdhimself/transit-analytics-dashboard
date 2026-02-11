"""
Tests for ML modules.
"""
import pytest
import pandas as pd
import numpy as np
from src.ml.train_model import DelayPredictor


def test_data_preparation():
    """Test data preparation for ML."""
    # Create sample data
    data = pd.DataFrame({
        'hour_of_day': np.random.randint(0, 24, 100),
        'day_of_week': np.random.randint(0, 7, 100),
        'is_rush_hour': np.random.randint(0, 2, 100),
        'route_id_encoded': np.random.randint(0, 10, 100),
        'delay_minutes': np.random.normal(3, 2, 100)
    })
    
    feature_cols = ['hour_of_day', 'day_of_week', 'is_rush_hour', 'route_id_encoded']
    
    predictor = DelayPredictor()
    X_train, X_test, y_train, y_test = predictor.prepare_data(data, feature_cols)
    
    # Check split sizes (80/20 split of 100 records)
    assert len(X_train) == 80
    assert len(X_test) == 20
    assert len(y_train) == 80
    assert len(y_test) == 20
    
    # Check feature names stored
    assert predictor.feature_names == feature_cols


def test_model_training():
    """Test model training (quick test with small data)."""
    # Create sample data
    np.random.seed(42)
    n_samples = 200
    
    data = pd.DataFrame({
        'hour_of_day': np.random.randint(0, 24, n_samples),
        'day_of_week': np.random.randint(0, 7, n_samples),
        'is_rush_hour': np.random.randint(0, 2, n_samples),
        'route_id_encoded': np.random.randint(0, 10, n_samples),
        'delay_minutes': np.random.normal(3, 2, n_samples)
    })
    
    feature_cols = ['hour_of_day', 'day_of_week', 'is_rush_hour', 'route_id_encoded']
    
    predictor = DelayPredictor()
    X_train, X_test, y_train, y_test = predictor.prepare_data(data, feature_cols)
    
    # Train a small model
    predictor.train_random_forest(X_train, y_train, n_estimators=10)
    
    # Check model was trained
    assert predictor.model is not None
    
    # Make predictions
    predictions = predictor.model.predict(X_test)
    assert len(predictions) == len(X_test)
    assert all(isinstance(p, (int, float, np.number)) for p in predictions)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
