"""
ML model training for transit delay prediction.
Trains RandomForestRegressor (and optionally XGBoost) to predict delay_minutes.
"""
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Optional: XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not available. Install with: pip install xgboost")


class DelayPredictor:
    """Trainer for transit delay prediction models."""
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize the trainer.
        
        Args:
            model_type: 'random_forest' or 'xgboost'
        """
        self.model_type = model_type
        self.model = None
        self.feature_names = None
        self.training_stats = {}
        
        # Model artifacts directory
        self.model_dir = Path(__file__).parent / 'model_artifacts'
        self.model_dir.mkdir(exist_ok=True)
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        feature_cols: list,
        target_col: str = 'delay_minutes',
        test_size: float = 0.2,
        random_state: int = 42
    ):
        """
        Prepare data for training.
        
        Args:
            df: DataFrame with features and target
            feature_cols: List of feature column names
            target_col: Target column name
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility
            
        Returns:
            X_train, X_test, y_train, y_test
        """
        # Remove rows with missing target
        df = df.dropna(subset=[target_col])
        
        # Remove rows with missing features
        df = df.dropna(subset=feature_cols)
        
        print(f"Dataset size after cleaning: {len(df)} records")
        
        # Separate features and target
        X = df[feature_cols]
        y = df[target_col]
        
        # Store feature names
        self.feature_names = feature_cols
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=random_state
        )
        
        print(f"Training set: {len(X_train)} records")
        print(f"Test set: {len(X_test)} records")
        
        return X_train, X_test, y_train, y_test
    
    def train_random_forest(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_estimators: int = 100,
        max_depth: int = 20,
        random_state: int = 42
    ):
        """
        Train RandomForestRegressor.
        
        Args:
            X_train: Training features
            y_train: Training target
            n_estimators: Number of trees
            max_depth: Maximum tree depth
            random_state: Random seed
        """
        print(f"\nTraining Random Forest with {n_estimators} trees...")
        
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
            verbose=1
        )
        
        self.model.fit(X_train, y_train)
        print("Training complete!")
    
    def train_xgboost(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_estimators: int = 100,
        learning_rate: float = 0.1,
        max_depth: int = 6,
        random_state: int = 42
    ):
        """
        Train XGBoost model.
        
        Args:
            X_train: Training features
            y_train: Training target
            n_estimators: Number of boosting rounds
            learning_rate: Learning rate
            max_depth: Maximum tree depth
            random_state: Random seed
        """
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost not installed")
        
        print(f"\nTraining XGBoost with {n_estimators} rounds...")
        
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train, verbose=True)
        print("Training complete!")
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """
        Evaluate model on test set.
        
        Args:
            X_test: Test features
            y_test: Test target
            
        Returns:
            Dictionary with evaluation metrics
        """
        print("\nEvaluating model...")
        
        # Make predictions
        y_pred = self.model.predict(X_test)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)
        
        # Calculate accuracy within thresholds
        within_1min = np.mean(np.abs(y_test - y_pred) <= 1) * 100
        within_2min = np.mean(np.abs(y_test - y_pred) <= 2) * 100
        within_5min = np.mean(np.abs(y_test - y_pred) <= 5) * 100
        
        metrics = {
            'mae': float(mae),
            'mse': float(mse),
            'rmse': float(rmse),
            'r2_score': float(r2),
            'within_1min': float(within_1min),
            'within_2min': float(within_2min),
            'within_5min': float(within_5min),
            'test_samples': len(y_test)
        }
        
        self.training_stats = metrics
        
        # Print results
        print("\n" + "="*50)
        print("MODEL EVALUATION RESULTS")
        print("="*50)
        print(f"R² Score:                 {r2:.4f}")
        print(f"Mean Absolute Error:      {mae:.2f} minutes")
        print(f"Root Mean Squared Error:  {rmse:.2f} minutes")
        print(f"\nAccuracy within thresholds:")
        print(f"  Within 1 minute:        {within_1min:.1f}%")
        print(f"  Within 2 minutes:       {within_2min:.1f}%")
        print(f"  Within 5 minutes:       {within_5min:.1f}%")
        print("="*50)
        
        if r2 >= 0.75:
            print("✓ Target R² score (0.75) achieved!")
        else:
            print(f"⚠ R² score below target (0.75). Consider collecting more data or tuning hyperparameters.")
        
        return metrics
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance from trained model.
        
        Returns:
            DataFrame with feature names and importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        if hasattr(self.model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            })
            importance_df = importance_df.sort_values('importance', ascending=False)
            
            print("\n" + "="*50)
            print("FEATURE IMPORTANCE")
            print("="*50)
            for _, row in importance_df.iterrows():
                print(f"{row['feature']:20s} {row['importance']:.4f}")
            print("="*50)
            
            return importance_df
        else:
            print("Model does not support feature importance")
            return pd.DataFrame()
    
    def save_model(self, filename: str = None) -> Path:
        """
        Save trained model to disk.
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved model file
        """
        if self.model is None:
            raise ValueError("No model to save")
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.model_type}_model_{timestamp}.joblib"
        
        model_path = self.model_dir / filename
        
        # Save model and metadata
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'training_stats': self.training_stats,
            'trained_at': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, model_path)
        print(f"\nModel saved to: {model_path}")
        
        # Also save as default model
        default_path = self.model_dir / 'delay_model.joblib'
        joblib.dump(model_data, default_path)
        print(f"Model also saved as: {default_path}")
        
        return model_path
    
    def train_and_evaluate(
        self,
        df: pd.DataFrame,
        feature_cols: list,
        target_col: str = 'delay_minutes'
    ) -> dict:
        """
        Complete training and evaluation pipeline.
        
        Args:
            df: DataFrame with features and target
            feature_cols: List of feature column names
            target_col: Target column name
            
        Returns:
            Dictionary with evaluation metrics
        """
        # Prepare data
        X_train, X_test, y_train, y_test = self.prepare_data(
            df, feature_cols, target_col
        )
        
        # Train model
        if self.model_type == 'random_forest':
            self.train_random_forest(X_train, y_train)
        elif self.model_type == 'xgboost':
            self.train_xgboost(X_train, y_train)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Evaluate
        metrics = self.evaluate(X_test, y_test)
        
        # Feature importance
        self.get_feature_importance()
        
        # Save model
        self.save_model()
        
        return metrics


def train_delay_model(
    data_path: str,
    feature_cols: list,
    model_type: str = 'random_forest'
) -> dict:
    """
    Convenience function to train a delay prediction model.
    
    Args:
        data_path: Path to CSV file with training data
        feature_cols: List of feature column names
        model_type: 'random_forest' or 'xgboost'
        
    Returns:
        Dictionary with evaluation metrics
    """
    # Load data
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} records")
    
    # Train model
    trainer = DelayPredictor(model_type=model_type)
    metrics = trainer.train_and_evaluate(df, feature_cols)
    
    return metrics


if __name__ == '__main__':
    print("Transit Delay Prediction Model Trainer")
    print("="*50)
    
    # This is a template - actual training requires real data
    print("\nTo train a model, you need:")
    print("1. Collected GTFS-RT data with delays")
    print("2. Engineered features (use feature_engineer.py)")
    print("3. A CSV file with the complete feature set")
    print("\nExample usage:")
    print("  python train_model.py --data features.csv --model random_forest")
    
    # Create a sample training script
    sample_code = """
# Sample training script
import pandas as pd
from src.ml.train_model import DelayPredictor

# Load your engineered features
df = pd.read_csv('path/to/your/features.csv')

# Define feature columns
feature_cols = [
    'hour_of_day',
    'day_of_week',
    'is_weekend',
    'is_rush_hour',
    'route_id_encoded',
    'stop_sequence'
]

# Train model
trainer = DelayPredictor(model_type='random_forest')
metrics = trainer.train_and_evaluate(df, feature_cols)

print(f"Model trained with R² score: {metrics['r2_score']:.4f}")
"""
    
    print("\nSample training code:")
    print(sample_code)
