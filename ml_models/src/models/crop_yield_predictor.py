"""
Crop Yield Prediction Model
Predicts crop yield based on weather, soil, and agricultural inputs
"""

from .base_model import BaseModel
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import logging, numpy as np, pandas as pd

logger = logging.getLogger(__name__)

class CropYieldPredictor(BaseModel):
    """Predicts crop yield using ExtraTreesRegressor"""

    def __init__(self, config):
        super().__init__('crop_yield_predictor', config)
        self.label_encoders = {}

    def preprocess(self, data, fit=True):
        """
        Preprocess data for crop yield prediction.

        Parameters:
        -----------
        data : pd.DataFrame
            Raw input data
        fit : bool
            Whether to fit encoders (True for training, False for inference)

        Returns:
        --------
        pd.DataFrame : Preprocessed data
        """

        df = data.copy()

        leakage_features = ['YIELD_EFFICIENCY', 'PESTICIDE_INTENSITY']
        df = df.drop(leakage_features, axis=1)

        categorical_features = ['AREA', 'CROP_TYPE', 'ERA']

        if fit:
            from sklearn.preprocessing import LabelEncoder
            for feature in categorical_features:
                le = LabelEncoder()
                df[feature] = le.fit_transform(df[feature])
                self.label_encoders[feature] = le
        else:
            for feature in categorical_features:
                if feature in df.columns and feature in self.label_encoders:
                    df[feature] = self.label_encoders[feature].transform(df[feature])

        return df

    def train(self, X_train, y_train, X_test=None, y_test=None):
        """
        Train the crop yield prediction model.

        Parameters:
        -----------
        X_train, X_test : pd.DataFrame
            Training and test features
        y_train, y_test : pd.Series
            Training and test targets

        Returns:
        --------
        dict : Training metrics
        """

        logger.info("Training crop yield predictor model...")

        params = self.config.get('model_params', {
            'n_estimators': 100,
            'max_depth': 20,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'random_state': 42,
            'n_jobs': -1
        })

        self.model = ExtraTreesRegressor(**params)
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # if X_test and y_test:
        #     metrics = self.evaluate(X_test, y_test)
        #     logger.info(f"Training complete. Test R²: {metrics['test_r2']:.4f}")
        #     return metrics

        return  self.evaluate(X_test, y_test)


    def predict(self, X):
        """
        Make yield predictions.

        Parameters:
        -----------
        X : pd.DataFrame
            Input features

        Returns:
        --------
        np.array : Predicted yields
        """

        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions.")

        return self.model.predict(X)

    def evaluate(self, X_test, y_test):
        """
        Evaluate model performance.

        Parameters:
        -----------
        X_test : pd.DataFrame
            Test features
        y_test : pd.Series
            Test targets

        Returns:
        --------
        dict : Evaluation metrics
        """
        y_pred = self.predict(X_test)

        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        ape = np.abs((y_test - y_pred) / y_test) * 100
        mean_ape = np.mean(ape)
        median_ape = np.median(ape)

        return {
            'test_rmse': rmse,
            'test_mae': mae,
            'test_r2': r2,
            'mean_ape': mean_ape,
            'median_ape': median_ape
        }

    def get_feature_importance(self):
        """Get feature importance from trained model."""
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        return pd.DataFrame({
            'feature': self.model.feature_names_in_,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

