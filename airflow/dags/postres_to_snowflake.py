from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime
from snowflake.connector.pandas_tools import write_pandas


def load_weather_to_snowflake(**context):
    pg = PostgresHook(postgres_conn_id='postgres_default')
    sf = SnowflakeHook(snowflake_conn_id='snowflake_default')

    last_id = int(Variable.get('weather_last_processed_id', default_var=0))
    query = f"SELECT * FROM agrosense.weather WHERE id > {last_id} ORDER BY id"
    df = pg.get_pandas_df(query)

    if not df.empty:
        conn = sf.get_conn()
        write_pandas(
            conn=conn,
            df=df,
            table_name="WEATHER",
            database="AGROSENSE_DB",
            schema="AGROSENSE_SCH",
            auto_create_table=True
        )
        new_id = int(df['id'].max())
        Variable.set('weather_last_processed_id', new_id)
    else:
        print("No new weather data to load")


def load_soil_to_snowflake(**context):
    pg = PostgresHook(postgres_conn_id='postgres_default')
    sf = SnowflakeHook(snowflake_conn_id='snowflake_default')

    last_id = int(Variable.get('soil_last_processed_id', default_var=0))
    query = f"SELECT * FROM agrosense.soil WHERE id > {last_id} ORDER BY id"
    df = pg.get_pandas_df(query)

    if not df.empty:
        conn = sf.get_conn()
        write_pandas(
            conn=conn,
            df=df,
            table_name="SOIL",
            database="AGROSENSE_DB",
            schema="AGROSENSE_SCH",
            auto_create_table=True
        )
        new_id = int(df['id'].max())
        Variable.set('soil_last_processed_id', new_id)
    else:
        print("No new soil data to load")


def load_predictions_to_snowflake(**context):
    pg = PostgresHook(postgres_conn_id='postgres_default')
    sf = SnowflakeHook(snowflake_conn_id='snowflake_default')

    last_id = int(Variable.get('yield_predictions_last_processed_id', default_var=0))
    query = f"SELECT * FROM agrosense.crop_yield_predictions WHERE id > {last_id} ORDER BY id"
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
        new_id = int(df['id'].max())
        Variable.set('yield_predictions_last_processed_id', new_id)
    else:
        print("No new prediction data to load")


default_args = {
    "owner": "agrosense",
    "retries": 1
}

with DAG(
    dag_id="load_postgres_to_snowflake",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False
) as dag:

    weather = PythonOperator(
        task_id="load_weather_to_snowflake",
        python_callable=load_weather_to_snowflake
    )

    soil = PythonOperator(
        task_id="load_soil_to_snowflake",
        python_callable=load_soil_to_snowflake
    )

    predictions = PythonOperator(
        task_id="load_predictions_to_snowflake",
        python_callable=load_predictions_to_snowflake
    )

    weather >> soil >> predictions