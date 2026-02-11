"""
Prediction service for trained delay models.
Loads serialized model and serves predictions.
"""
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Union


class DelayPredictionService:
    """Service for loading and using trained delay prediction models."""
    
    def __init__(self, model_path: str = None):
        """
        Initialize the prediction service.
        
        Args:
            model_path: Path to saved model file (uses default if None)
        """
        self.model_data = None
        self.model = None
        self.feature_names = None
        
        # Default model path
        if model_path is None:
            model_dir = Path(__file__).parent / 'model_artifacts'
            model_path = model_dir / 'delay_model.joblib'
        
        self.model_path = Path(model_path)
        
        # Load model if it exists
        if self.model_path.exists():
            self.load_model()
        else:
            print(f"Warning: Model not found at {self.model_path}")
            print("Train a model first using train_model.py")
    
    def load_model(self):
        """Load the trained model from disk."""
        try:
            print(f"Loading model from {self.model_path}...")
            self.model_data = joblib.load(self.model_path)
            
            self.model = self.model_data['model']
            self.feature_names = self.model_data['feature_names']
            
            print(f"Model loaded successfully!")
            print(f"Model type: {self.model_data['model_type']}")
            print(f"Trained at: {self.model_data['trained_at']}")
            
            if 'training_stats' in self.model_data:
                stats = self.model_data['training_stats']
                print(f"R² score: {stats.get('r2_score', 'N/A'):.4f}")
                print(f"MAE: {stats.get('mae', 'N/A'):.2f} minutes")
        
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def predict(self, features: Union[Dict, pd.DataFrame]) -> Union[float, np.ndarray]:
        """
        Predict delay for given features.
        
        Args:
            features: Dictionary or DataFrame with feature values
            
        Returns:
            Predicted delay in minutes (float for single prediction, array for batch)
        """
        if self.model is None:
            raise ValueError("Model not loaded. Train a model first.")
        
        # Convert dict to DataFrame if needed
        if isinstance(features, dict):
            features = pd.DataFrame([features])
        
        # Ensure features are in correct order
        if not all(col in features.columns for col in self.feature_names):
            missing = [col for col in self.feature_names if col not in features.columns]
            raise ValueError(f"Missing required features: {missing}")
        
        X = features[self.feature_names]
        
        # Make prediction
        predictions = self.model.predict(X)
        
        # Return single value if single prediction, otherwise array
        if len(predictions) == 1:
            return float(predictions[0])
        return predictions
    
    def predict_batch(self, features_list: List[Dict]) -> List[float]:
        """
        Predict delays for a batch of feature dictionaries.
        
        Args:
            features_list: List of feature dictionaries
            
        Returns:
            List of predicted delays in minutes
        """
        df = pd.DataFrame(features_list)
        predictions = self.predict(df)
        return predictions.tolist()
    
    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model metadata
        """
        if self.model_data is None:
            return {'status': 'No model loaded'}
        
        return {
            'model_type': self.model_data.get('model_type'),
            'trained_at': self.model_data.get('trained_at'),
            'feature_names': self.feature_names,
            'training_stats': self.model_data.get('training_stats', {})
        }


# Global service instance for easy access
_service_instance = None


def get_prediction_service(model_path: str = None) -> DelayPredictionService:
    """
    Get or create the global prediction service instance.
    
    Args:
        model_path: Path to model file (uses default if None)
        
    Returns:
        DelayPredictionService instance
    """
    global _service_instance
    
    if _service_instance is None:
        _service_instance = DelayPredictionService(model_path)
    
    return _service_instance


def predict_delay(features: Dict) -> float:
    """
    Convenience function to predict delay for a single set of features.
    
    Args:
        features: Dictionary with feature values
        
    Returns:
        Predicted delay in minutes
    """
    service = get_prediction_service()
    return service.predict(features)


def predict_delay_batch(features_list: List[Dict]) -> List[float]:
    """
    Convenience function to predict delays for multiple feature sets.
    
    Args:
        features_list: List of feature dictionaries
        
    Returns:
        List of predicted delays in minutes
    """
    service = get_prediction_service()
    return service.predict_batch(features_list)


if __name__ == '__main__':
    print("Delay Prediction Service Test")
    print("="*50)
    
    # Check if model exists
    model_dir = Path(__file__).parent / 'model_artifacts'
    model_path = model_dir / 'delay_model.joblib'
    
    if not model_path.exists():
        print(f"\nNo model found at {model_path}")
        print("Train a model first using train_model.py")
    else:
        # Load and test the service
        service = DelayPredictionService()
        
        print("\nModel Info:")
        print(service.get_model_info())
        
        # Sample prediction
        print("\nSample prediction:")
        sample_features = {
            'hour_of_day': 8,           # 8 AM
            'day_of_week': 0,            # Monday
            'is_weekend': 0,
            'is_rush_hour': 1,           # Yes, rush hour
            'route_id_encoded': 0,       # Route 0
            'stop_sequence': 5           # 5th stop
        }
        
        try:
            predicted_delay = service.predict(sample_features)
            print(f"Features: {sample_features}")
            print(f"Predicted delay: {predicted_delay:.2f} minutes")
        except Exception as e:
            print(f"Prediction failed: {e}")
            print("This is expected if features don't match training data")
