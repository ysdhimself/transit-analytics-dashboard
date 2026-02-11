"""
Feature engineering for ML model training.
Builds feature set from delay data for delay prediction model.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional
from sklearn.preprocessing import LabelEncoder


class FeatureEngineer:
    """Feature engineer for transit delay prediction."""
    
    def __init__(self):
        """Initialize the feature engineer."""
        self.route_encoder = LabelEncoder()
        self.fitted = False
    
    def extract_temporal_features(self, df: pd.DataFrame, timestamp_col: str = 'feed_timestamp') -> pd.DataFrame:
        """
        Extract temporal features from timestamp.
        
        Args:
            df: DataFrame with timestamp column
            timestamp_col: Name of timestamp column
            
        Returns:
            DataFrame with added temporal features
        """
        df = df.copy()
        
        # Convert to datetime if not already
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        
        # Extract hour of day (0-23)
        df['hour_of_day'] = df[timestamp_col].dt.hour
        
        # Extract day of week (0=Monday, 6=Sunday)
        df['day_of_week'] = df[timestamp_col].dt.dayofweek
        
        # Is weekend (Saturday=5, Sunday=6)
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Is rush hour (7-9 AM or 4-6 PM)
        df['is_rush_hour'] = (
            ((df['hour_of_day'] >= 7) & (df['hour_of_day'] <= 9)) |
            ((df['hour_of_day'] >= 16) & (df['hour_of_day'] <= 18))
        ).astype(int)
        
        # Time of day category
        df['time_of_day'] = pd.cut(
            df['hour_of_day'],
            bins=[0, 6, 12, 18, 24],
            labels=['night', 'morning', 'afternoon', 'evening'],
            include_lowest=True
        )
        
        return df
    
    def encode_categorical_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Encode categorical features (route_id).
        
        Args:
            df: DataFrame with categorical columns
            fit: If True, fit the encoder; if False, use existing encoder
            
        Returns:
            DataFrame with encoded features
        """
        df = df.copy()
        
        if 'route_id' in df.columns:
            if fit:
                # Fit and transform
                df['route_id_encoded'] = self.route_encoder.fit_transform(df['route_id'].astype(str))
                self.fitted = True
            else:
                if not self.fitted:
                    raise ValueError("Encoder must be fitted before transform")
                # Transform only
                df['route_id_encoded'] = self.route_encoder.transform(df['route_id'].astype(str))
        
        return df
    
    def add_weather_feature(self, df: pd.DataFrame, temperature: Optional[float] = None) -> pd.DataFrame:
        """
        Add weather temperature feature (P1 - optional).
        
        Args:
            df: DataFrame
            temperature: Current temperature in Celsius (if None, will try to fetch)
            
        Returns:
            DataFrame with weather_temp column
        """
        df = df.copy()
        
        if temperature is None:
            # Try to fetch from weather API
            try:
                from src.utils.weather import get_temperature
                temperature = get_temperature()
            except:
                temperature = None
        
        df['weather_temp'] = temperature if temperature is not None else np.nan
        
        return df
    
    def create_feature_set(
        self,
        df: pd.DataFrame,
        target_col: str = 'delay_minutes',
        include_weather: bool = False,
        fit_encoders: bool = True
    ) -> pd.DataFrame:
        """
        Create complete feature set for ML model.
        
        Args:
            df: Input DataFrame with delay data
            target_col: Name of target column
            include_weather: If True, include weather features (P1)
            fit_encoders: If True, fit encoders; if False, use existing
            
        Returns:
            DataFrame with engineered features
        """
        df = df.copy()
        
        # Extract temporal features
        df = self.extract_temporal_features(df)
        
        # Encode categorical features
        df = self.encode_categorical_features(df, fit=fit_encoders)
        
        # Add weather (optional)
        if include_weather:
            df = self.add_weather_feature(df)
        
        # Select feature columns
        feature_cols = [
            'hour_of_day',
            'day_of_week',
            'is_weekend',
            'is_rush_hour',
            'route_id_encoded'
        ]
        
        # Add stop_sequence if available
        if 'stop_sequence' in df.columns:
            feature_cols.append('stop_sequence')
        
        # Add weather if included
        if include_weather and 'weather_temp' in df.columns:
            feature_cols.append('weather_temp')
            # Fill missing weather values with mean
            df['weather_temp'] = df['weather_temp'].fillna(df['weather_temp'].mean())
        
        # Keep target and identifiers
        id_cols = ['trip_id', 'route_id', 'stop_id', 'feed_timestamp']
        id_cols = [col for col in id_cols if col in df.columns]
        
        output_cols = id_cols + feature_cols
        if target_col in df.columns:
            output_cols.append(target_col)
        
        return df[output_cols]
    
    def get_feature_names(self, include_weather: bool = False) -> list:
        """
        Get list of feature names for model training.
        
        Args:
            include_weather: If True, include weather features
            
        Returns:
            List of feature names
        """
        features = [
            'hour_of_day',
            'day_of_week',
            'is_weekend',
            'is_rush_hour',
            'route_id_encoded',
            'stop_sequence'
        ]
        
        if include_weather:
            features.append('weather_temp')
        
        return features


def engineer_features(
    delays_df: pd.DataFrame,
    include_weather: bool = False
) -> pd.DataFrame:
    """
    Convenience function to engineer features from delays DataFrame.
    
    Args:
        delays_df: DataFrame with delay information
        include_weather: If True, include weather features
        
    Returns:
        DataFrame with engineered features
    """
    engineer = FeatureEngineer()
    return engineer.create_feature_set(delays_df, include_weather=include_weather)


if __name__ == '__main__':
    # Test feature engineering
    print("Testing Feature Engineer...")
    
    # Sample test data
    test_data = pd.DataFrame({
        'trip_id': ['trip1', 'trip2', 'trip3'],
        'route_id': ['route1', 'route1', 'route2'],
        'stop_id': ['stop1', 'stop2', 'stop3'],
        'stop_sequence': [1, 2, 1],
        'feed_timestamp': [
            '2024-01-15T08:30:00',  # Monday morning rush hour
            '2024-01-15T17:45:00',  # Monday evening rush hour
            '2024-01-20T14:00:00'   # Saturday afternoon
        ],
        'delay_minutes': [2.5, 5.0, 1.0]
    })
    
    engineer = FeatureEngineer()
    features = engineer.create_feature_set(test_data)
    
    print("\nEngineered features:")
    print(features)
    
    print("\nFeature names:")
    print(engineer.get_feature_names())
