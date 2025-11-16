"""
Base model abstract class that all ML models inherit from.
Provides common functionality for training, evaluation and MLflow tracking
"""

import mlflow, mlflow.sklearn, joblib, logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseModel(ABC):
    """Abstract base class for all ML models"""
    def __init__(self, model_name, config):
        """
        Initialize base model
        Parameters:
        -----------
        model_name : str
            Name of the model (e.g., 'crop_yield_predictor')
        config : dict
            Model configuration
        """
        self.model_name = model_name
        self.config = config
        self.model = None
        self.is_trained = False

        tracking_uri = self.config.get('tracking_uri', 'http://localhost:5000')
        mlflow.set_tracking_uri(tracking_uri)
        logger.info(f"MLflow tracking URI set to: {tracking_uri}")
        print(f"MLflow tracking URI set to: {tracking_uri}")

        self.experiment_name = self.config.get('experiment_name', model_name)

    @abstractmethod
    def preprocess(self, data):
        """Preprocess input data."""
        pass

    @abstractmethod
    def train(self, X_train, y_train):
        """Train the model."""
        pass

    @abstractmethod
    def predict(self, X):
        """Make predictions on input data."""
        pass

    @abstractmethod
    def evaluate(self, X_test, y_test):
        """Evaluate the model on input data."""
        pass

    def save_model(self, file_path):
        """Save trained model to disk."""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving.")

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, file_path)
        logger.info(f"Model saved to {file_path}")

    def load_model(self, file_path):
        """Load trained model from disk"""
        self.model = joblib.load(file_path)
        self.is_trained = True
        logger.info(f"Model loaded from {file_path}")

    def log_to_mlflow(self, params, metrics, artifacts=None):
        """
        Log model to MLflow

        Parameters:
        -----------
        params : dict
            Model parameters
        metrics : dict
            Evaluation metrics
        artifacts : dict, optional
            Additional artifacts to log
        """

        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(self.experiment_name)
            logger.info(f"Created new MLflow experiment: {self.experiment_name} with id {experiment_id}")
        else:
            experiment_id = experiment.experiment_id
            logger.info(f"Using existing MLflow experiment: {self.experiment_name} with id {experiment_id}")

        mlflow.set_experiment(self.experiment_name)

        with mlflow.start_run(run_name=self.model_name):
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
            mlflow.sklearn.log_model(self.model, artifact_path='model', registered_model_name=self.model_name)

            if artifacts:
                for name, artifact in artifacts.items():
                    mlflow.log_artifact(artifact, artifact_path=name)

            run_id = mlflow.active_run().info.run_id
            logger.info(f"Model logged to MLflow run: {run_id}")
            return run_id