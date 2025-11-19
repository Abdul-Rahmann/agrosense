"""
Airflow DAG for training Crop Yield Prediction model
Runs weekly to retrain the model with the latest data
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys, os
from pathlib import Path

project_root = Path('/opt/airflow/agrosense')
sys.path.insert(0, str(project_root))

from ml_models.data_loader.snowflake_loader import DataLoader
from ml_models.src.models.crop_yield_predictor import CropYieldPredictor
from sklearn.model_selection import train_test_split
import yaml
import joblib
import logging
import pandas as pd

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'agrosense',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
    'start_date': datetime(2025, 10, 1)
}


def load_data(**context):
    """Load training data from Snowflake"""
    logger.info("=" * 60)
    logger.info("TASK 1: Loading data from Snowflake")
    logger.info("=" * 60)

    try:
        config_path = project_root / 'ml_models' / 'config' / 'config.yml'
        logger.info(f"Config path: {config_path}")

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        loader = DataLoader()
        query = config['snowflake']['yield_prediction_data_query']
        df = loader.load_from_snowflake(query)

        logger.info(f"Loaded {len(df)} rows, {df.shape[1]} columns")

        temp_path = project_root / 'ml_models' / 'temp' / 'training_data.parquet'
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_parquet(temp_path, index=False)
        logger.info(f"Data saved to {temp_path}")

        if not temp_path.exists():
            raise FileNotFoundError(f"Failed to save data to {temp_path}")

        # Push to XCom
        context['ti'].xcom_push(key='data_rows', value=len(df))
        context['ti'].xcom_push(key='data_path', value=str(temp_path))

        logger.info("Task 1 completed successfully")

    except Exception as e:
        logger.error(f"Task 1 failed: {e}")
        raise


def preprocess_data(**context):
    """Preprocess data for training."""
    logger.info("=" * 60)
    logger.info("TASK 2: Preprocessing data")
    logger.info("=" * 60)

    try:
        config_path = project_root / 'ml_models' / 'config' / 'config.yml'
        logger.info(f"Loading config from: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Get data path from XCom
        data_path = context['ti'].xcom_pull(key='data_path', task_ids='load_data')
        logger.info(f"Loading data from: {data_path}")

        if not Path(data_path).exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")

        df = pd.read_parquet(data_path)
        logger.info(f"Loaded data: {df.shape}")

        model = CropYieldPredictor(config['mlflow'])
        df_processed = model.preprocess(df, fit=True)
        logger.info(f"Preprocessed data: {df_processed.shape}")

        X = df_processed.drop('TARGET_YIELD', axis=1)
        y = df_processed['TARGET_YIELD']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        logger.info(f"Split: Train={X_train.shape}, Test={X_test.shape}")

        temp_dir = project_root / 'ml_models' / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Temp directory: {temp_dir}")

        # Save preprocessed data
        X_train.to_parquet(temp_dir / 'X_train.parquet', index=False)
        X_test.to_parquet(temp_dir / 'X_test.parquet', index=False)
        y_train.to_frame().to_parquet(temp_dir / 'y_train.parquet', index=False)
        y_test.to_frame().to_parquet(temp_dir / 'y_test.parquet', index=False)

        for filename in ['X_train.parquet', 'X_test.parquet', 'y_train.parquet', 'y_test.parquet']:
            filepath = temp_dir / filename
            if not filepath.exists():
                raise FileNotFoundError(f"Failed to create {filepath}")
            logger.info(f"Created: {filename} ({filepath.stat().st_size} bytes)")

        # Save encoders
        encoders_path = project_root / 'ml_models' / 'models' / 'crop_yield' / 'encoders.pkl'
        encoders_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model.label_encoders, encoders_path)
        logger.info(f"Saved encoders to: {encoders_path}")

        # Push to XCom
        context['ti'].xcom_push(key='train_size', value=len(X_train))
        context['ti'].xcom_push(key='test_size', value=len(X_test))
        context['ti'].xcom_push(key='feature_count', value=len(X_train.columns))

        logger.info("Task 2 completed successfully")

    except Exception as e:
        logger.error(f"Task 2 failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def train_model(**context):
    """Train the crop yield model."""
    logger.info("=" * 60)
    logger.info("TASK 3: Training model")
    logger.info("=" * 60)

    try:
        # Load config
        config_path = project_root / 'ml_models' / 'config' / 'config.yml'
        logger.info(f"Loading config from: {config_path}")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        temp_dir = project_root / 'ml_models' / 'temp'
        logger.info(f"Loading preprocessed data from: {temp_dir}")

        # List files in temp directory for debugging
        if temp_dir.exists():
            files = list(temp_dir.glob('*.parquet'))
            logger.info(f"Files in temp directory: {[f.name for f in files]}")
        else:
            raise FileNotFoundError(f"Temp directory does not exist: {temp_dir}")

        # Load preprocessed data
        X_train = pd.read_parquet(temp_dir / 'X_train.parquet')
        X_test = pd.read_parquet(temp_dir / 'X_test.parquet')
        y_train = pd.read_parquet(temp_dir / 'y_train.parquet')['TARGET_YIELD']
        y_test = pd.read_parquet(temp_dir / 'y_test.parquet')['TARGET_YIELD']

        logger.info(f"Loaded training data: X_train={X_train.shape}, y_train={y_train.shape}")
        logger.info(f"Loaded test data: X_test={X_test.shape}, y_test={y_test.shape}")

        # Initialize and train model
        model = CropYieldPredictor(config['mlflow'])
        logger.info("Training model...")
        metrics = model.train(X_train, y_train, X_test, y_test)

        logger.info(f"Training completed!")
        logger.info(f"Test R²: {metrics.get('test_r2', 'N/A')}")
        logger.info(f"Test RMSE: {metrics.get('test_rmse', 'N/A')}")

        # Log to MLflow
        run_id = model.log_to_mlflow(
            params=config.get('model_params', {}),
            metrics=metrics
        )
        logger.info(f"Logged to MLflow: Run ID = {run_id}")

        # Save model
        model_path = project_root / 'ml_models' / 'models' / 'crop_yield' / 'model.pkl'
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save_model(model_path)
        logger.info(f"Saved model to: {model_path}")

        # Push metrics to XCom
        context['ti'].xcom_push(key='test_r2', value=metrics.get('test_r2', 0.0))
        context['ti'].xcom_push(key='test_rmse', value=metrics.get('test_rmse', 0.0))
        context['ti'].xcom_push(key='test_mae', value=metrics.get('test_mae', 0.0))
        context['ti'].xcom_push(key='mean_ape', value=metrics.get('mean_ape', 0.0))
        context['ti'].xcom_push(key='median_ape', value=metrics.get('median_ape', 0.0))
        context['ti'].xcom_push(key='mlflow_run_id', value=run_id)

        logger.info("Task 3 completed successfully")

    except Exception as e:
        logger.error(f"Task 3 failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def send_training_summary(**context):
    """Log training summary."""
    logger.info("=" * 60)
    logger.info("TASK 4: Generating training summary")
    logger.info("=" * 60)

    ti = context['ti']

    # Pull metrics from XCom
    data_rows = ti.xcom_pull(key='data_rows', task_ids='load_data')
    train_size = ti.xcom_pull(key='train_size', task_ids='preprocess_data')
    test_size = ti.xcom_pull(key='test_size', task_ids='preprocess_data')
    feature_count = ti.xcom_pull(key='feature_count', task_ids='preprocess_data')
    test_r2 = ti.xcom_pull(key='test_r2', task_ids='train_model')
    test_rmse = ti.xcom_pull(key='test_rmse', task_ids='train_model')
    test_mae = ti.xcom_pull(key='test_mae', task_ids='train_model')
    mean_ape = ti.xcom_pull(key='mean_ape', task_ids='train_model')
    median_ape = ti.xcom_pull(key='median_ape', task_ids='train_model')
    run_id = ti.xcom_pull(key='mlflow_run_id', task_ids='train_model')

    summary = f"""
    ========================================
    CROP YIELD MODEL TRAINING SUMMARY
    ========================================
    Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Data:
      - Total rows: {data_rows}
      - Train size: {train_size}
      - Test size: {test_size}
      - Features: {feature_count}
    
    Model Performance:
      - Test R²: {test_r2:.4f}
      - Test RMSE: {test_rmse:,.2f}
      - Test MAE: {test_mae:,.2f}
      - Mean APE: {mean_ape:.2f}%
      - Median APE: {median_ape:.2f}%
    
    MLflow Run ID: {run_id}
    
    Model Location: ml_models/models/crop_yield/model.pkl
    ========================================
    """

    logger.info(summary)
    print(summary)


def cleanup_temp_files(**context):
    """Clean up temporary files."""
    logger.info("=" * 60)
    logger.info("TASK 5: Cleaning up temporary files")
    logger.info("=" * 60)

    import shutil

    temp_dir = project_root / 'ml_models' / 'temp'

    if temp_dir.exists():
        logger.info(f"Removing temp directory: {temp_dir}")
        shutil.rmtree(temp_dir)
        logger.info(f"Removed {temp_dir}")
    else:
        logger.info(f"Temp directory doesn't exist: {temp_dir}")


with DAG(
        'train_crop_yield_model',
        default_args=default_args,
        description='Train crop yield prediction model with latest data',
        schedule_interval='0 2 * * 0',
        catchup=False,
        tags=['ml', 'training', 'crop_yield'],
) as dag:

    load_data_task = PythonOperator(
        task_id='load_data',
        python_callable=load_data,
    )

    preprocess_data_task = PythonOperator(
        task_id='preprocess_data',
        python_callable=preprocess_data,
    )

    train_model_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
    )

    send_summary_task = PythonOperator(
        task_id='send_training_summary',
        python_callable=send_training_summary,
    )

    cleanup_task = PythonOperator(
        task_id='cleanup_temp_files',
        python_callable=cleanup_temp_files,
        trigger_rule='all_done',
    )

    load_data_task >> preprocess_data_task >> train_model_task >> send_summary_task >> cleanup_task