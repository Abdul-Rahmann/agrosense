"""
Training script for Crop Yield Prediction model.
Loads data, trains model, logs to MLflow, and saves artifacts
"""

import sys, os, joblib
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.resolve()
sys.path.append(str(project_root))
print(project_root)

from ml_models.src.models.crop_yield_predictor import CropYieldPredictor
from ml_models.data_loader.snowflake_loader import DataLoader
from sklearn.model_selection import train_test_split
import yaml,logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main training pipeline"""
    logger.info("=" * 60)
    logger.info("CROP YIELD PREDICTION MODEL TRAINING")
    logger.info("=" * 60)

    config_path = os.getenv('CONFIG_PATH') or project_root / 'ml_models/config/config.yml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    logger.info("Loading data from Snowflake...")
    loader = DataLoader(config_path=config_path)
    df = loader.load_from_snowflake()

    model = CropYieldPredictor(config['mlflow'])

    logger.info("Preprocessing data...")
    df_processed = model.preprocess(df, fit=True)

    X = df_processed.drop('TARGET_YIELD', axis=1)
    y = df_processed['TARGET_YIELD']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"X_train shape: {X_train.shape}")

    logger.info("Training model...")
    metrics = model.train(X_train, y_train, X_test, y_test)

    logger.info("Logging to MLflow...")
    run_id = model.log_to_mlflow(
        params=config['model_params'],
        metrics=metrics
    )

    model_path = project_root / 'ml_models' / 'models' / 'crop_yield' / 'model.pkl'
    model.save_model(model_path)

    encoders_path = project_root / 'ml_models' / 'models' / 'crop_yield' / 'encoders.pkl'
    joblib.dump(model.label_encoders, encoders_path)

    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Test R²: {metrics['test_r2']:.4f}")
    logger.info(f"Test RMSE: {metrics['test_rmse']:,.2f}")
    logger.info(f"MLflow Run ID: {run_id}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()