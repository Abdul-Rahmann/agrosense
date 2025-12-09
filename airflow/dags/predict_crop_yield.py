"""
Daily Crop Yield Prediction Pipeline
Makes predictions for current growing season scenarios
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys, yaml
from pathlib import Path
import pandas as pd
import logging
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from snowflake.connector.pandas_tools import write_pandas
from airflow.models import Variable

project_root = Path('/opt/airflow/agrosense')
sys.path.insert(0, str(project_root))

from ml_models.data_loader.snowflake_loader import DataLoader

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'agrosense',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def load_current_conditions(**context):
    """Load synthetic current conditions from dbt mart"""
    logger.info("=" * 60)
    logger.info("STEP 1: Loading current conditions for prediction")
    logger.info("=" * 60)

    config_path = project_root / 'ml_models' / 'config' / 'config.yml'
    logger.info(f"Config path: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    loader = DataLoader()
    query = config['snowflake']['current_condition_data_query1']
    df = loader.load_from_snowflake(query)

    print("------DF-HEAD-----\n", df.head())
    logger.info(f"Loaded {len(df)} scenarios for prediction")
    logger.info(f"   Areas: {df['AREA'].nunique()}")
    logger.info(f"   Crops: {df['CROP_TYPE'].nunique()}")
    logger.info(f"   Scenarios: {df['SCENARIO'].unique().tolist()}")

    # Save for next task
    temp_path = project_root / 'ml_models' / 'temp' / 'current_conditions.parquet'
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(temp_path, index=False)

    context['ti'].xcom_push(key='data_path', value=str(temp_path))
    context['ti'].xcom_push(key='record_count', value=len(df))


def make_predictions(**context):
    """Generate predictions using production model"""
    logger.info("=" * 60)
    logger.info("STEP 2: Making predictions with trained model")
    logger.info("=" * 60)

    import mlflow.sklearn
    import joblib
    import yaml

    config_path = project_root / 'ml_models' / 'config' / 'config.yml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    mlflow.set_tracking_uri(config['mlflow']['tracking_uri'])

    # Load data
    data_path = context['ti'].xcom_pull(key='data_path', task_ids='load_current_conditions')
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} records for prediction")

    metadata_cols = ['AREA', 'CROP_TYPE', 'YEAR', 'SCENARIO']
    metadata = df[metadata_cols].copy()

    # Load encoders
    encoders_path = project_root / 'ml_models' / 'models' / 'crop_yield' / 'encoders.pkl'
    encoders = joblib.load(encoders_path)
    logger.info("loaded label encoders")

    # Encode categorical features
    feature_df = df.copy()
    feature_df['AREA'] = encoders['AREA'].transform(df['AREA'])
    feature_df['CROP_TYPE'] = encoders['CROP_TYPE'].transform(
        df['CROP_TYPE'])
    feature_df['ERA'] = encoders['ERA'].transform(df['ERA'])

    feature_cols = [
        'AREA',
        'CROP_TYPE',
        'YEAR',
        'AVERAGE_RAINFALL_MM_PER_YEAR',
        'PESTICIDES_TONNES',
        'AVG_TEMP',
        'YEAR_IN_DECADE',
        'ERA'
    ]
    X = feature_df[feature_cols]

    logger.info(f"FEATURES: {X.head()}")

    logger.info(f"Prepared features: {X.shape}")

    # Load model from MLflow Model Registry
    try:
        model_uri = f"models:/crop_yield_predictor/Production"
        model = mlflow.sklearn.load_model(model_uri)
        logger.info("Loaded model from Production stage")
    except Exception as e:
        logger.warning(f"Could not load from Production: {e}")
        logger.info("Loading latest trained model instead...")
        model_path = project_root / 'ml_models' / 'models' / 'crop_yield' / 'model.pkl'
        model = joblib.load(model_path)
        logger.info("Model Loaded Successfully!")

    predictions = model.predict(X)
    logger.info(f"Generated {len(predictions)} predictions")

    # Combine with metadata
    results = metadata.copy()
    results['predicted_yield_hg_ha'] = predictions
    results['predicted_yield_kg_ha'] = predictions / 10  # Convert hg to kg
    results['predicted_yield_tonnes_ha'] = predictions / 10000  # Convert to tonnes
    results['prediction_date'] = datetime.now()
    results['model_version'] = 'v1.0'  # Track model version

    logger.info("=" * 60)
    logger.info("PREDICTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Average predicted yield: {predictions.mean():.0f} hg/ha")
    logger.info(f"Min predicted yield: {predictions.min():.0f} hg/ha")
    logger.info(f"Max predicted yield: {predictions.max():.0f} hg/ha")

    logger.info("\nSample predictions:")
    logger.info(results.head(10).to_string())

    # Save predictions
    output_path = project_root / 'ml_models' / 'predictions' / f'predictions_{datetime.now():%Y%m%d_%H%M%S}.parquet'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_parquet(output_path, index=False)

    context['ti'].xcom_push(key='output_path', value=str(output_path))
    context['ti'].xcom_push(key='avg_prediction', value=float(predictions.mean()))

    logger.info(f"Saved predictions to: {output_path}")


def save_to_database(**context):
    """Save predictions to PostgreSQL for dashboard/analysis"""
    logger.info("=" * 60)
    logger.info("STEP 3: Saving predictions to database")
    logger.info("=" * 60)

    from sqlalchemy import create_engine

    # Load predictions
    output_path = context['ti'].xcom_pull(key='output_path', task_ids='make_predictions')
    predictions = pd.read_parquet(output_path)

    # Database connection
    engine = create_engine(
        f"postgresql+psycopg2://agrosense:agrosense@postgres:5432/agrosense_db"
    )

    # Save to database
    predictions.columns = predictions.columns.str.lower()
    predictions.to_sql(
        'crop_yield_predictions',
        engine,
        schema='agrosense',
        if_exists='append',
        index=False
    )

    logger.info(f"Saved {len(predictions)} predictions to agrosense.crop_yield_predictions")
    logger.info("=" * 60)


def analyze_scenarios(**context):
    """Analyze predictions across different scenarios"""
    logger.info("=" * 60)
    logger.info("STEP 4: Scenario analysis")
    logger.info("=" * 60)

    output_path = context['ti'].xcom_pull(key='output_path', task_ids='make_predictions')
    predictions = pd.read_parquet(output_path)

    scenario_summary = predictions.groupby('SCENARIO').agg({
        'predicted_yield_kg_ha': ['mean', 'min', 'max']
    }).round(0)

    logger.info("\nScenario Comparison:")
    logger.info(scenario_summary.to_string())

    best = predictions.nlargest(5, 'predicted_yield_kg_ha')[['AREA', 'CROP_TYPE', 'SCENARIO', 'predicted_yield_kg_ha']]
    worst = predictions.nsmallest(5, 'predicted_yield_kg_ha')[
        ['AREA', 'CROP_TYPE', 'SCENARIO', 'predicted_yield_kg_ha']]

    logger.info("\nTop 5 Predicted Yields:")
    logger.info(best.to_string())

    logger.info("\nBottom 5 Predicted Yields:")
    logger.info(worst.to_string())

    logger.info("=" * 60)


def sync_predictions_to_snowflake(**context):
    """
    Sync prediction results from Postgres to Snowflake using
    the exact logic and behaviour of the working loader DAG.
    """

    pg = PostgresHook(postgres_conn_id='postgres_default')
    sf = SnowflakeHook(snowflake_conn_id='snowflake_default')

    # Match variable key exactly
    last_id = int(Variable.get('yield_predictions_last_processed_id', default_var=0))
    query = (
        f"SELECT * FROM agrosense.crop_yield_predictions "
        f"WHERE id > {last_id} ORDER BY id"
    )

    df = pg.get_pandas_df(query)

    if not df.empty:
        conn = sf.get_conn()
        write_pandas(
            conn=conn,
            df=df,
            table_name="CROP_YIELD_PREDICTIONS",
            database="AGROSENSE_DB",
            schema="AGROSENSE_SCH",
            auto_create_table=True
        )

        new_id = int(df["id"].max())
        Variable.set("yield_predictions_last_processed_id", new_id)
    else:
        print("No new prediction data to load")
with DAG(
        'predict_crop_yield',
        default_args=default_args,
        description='Generate daily crop yield predictions for current season',
        schedule_interval='0 6 * * *',  # Daily at 6 AM UTC
        catchup=False,
        tags=['ml', 'inference', 'predictions'],
) as dag:
    load_task = PythonOperator(
        task_id='load_current_conditions',
        python_callable=load_current_conditions,
    )

    predict_task = PythonOperator(
        task_id='make_predictions',
        python_callable=make_predictions,
    )

    save_task = PythonOperator(
        task_id='save_to_database',
        python_callable=save_to_database,
    )

    analyze_task = PythonOperator(
        task_id='analyze_scenarios',
        python_callable=analyze_scenarios,
    )

    sync_predictions = PythonOperator(
        task_id='sync_predictions_to_snowflake',
        python_callable=sync_predictions_to_snowflake
    )

    load_task >> predict_task >> save_task >> analyze_task >> sync_predictions