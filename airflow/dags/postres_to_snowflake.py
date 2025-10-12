from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime
from snowflake.connector.pandas_tools import write_pandas

LOAD_TASK_ID = "load_to_snowflake"


def load_weather_to_snowflake(**context):
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    sf_hook = SnowflakeHook(snowflake_conn_id='snowflake_default')

    weather_last_id = int(Variable.get('weather_last_processed_id', default_var=0))
    print(f"LAST PROCESSED ID: {weather_last_id}")

    query = f"SELECT * FROM agrosense.weather WHERE id > {weather_last_id} ORDER BY id"
    df = pg_hook.get_pandas_df(query)
    print(f"QUERY RESULTS: {df}")

    if not df.empty:
        conn = sf_hook.get_conn()
        write_pandas(
            conn=conn,
            df=df,
            table_name="WEATHER",
            database="AGROSENSE_DB",
            schema="AGROSENSE_SCH",
            auto_create_table=True,
            overwrite=False
        )

        new_max_id = int(df['id'].max())
        Variable.set('weather_last_processed_id', new_max_id)
        print(f"Loaded {len(df)} rows. Last ID: {new_max_id}")
    else:
        print("No new weather data to load")

def load_soil_to_snowflake(**context):
    pg_hook = PostgresHook(postgres_conn_id='postgres_default')
    sf_hook = SnowflakeHook(snowflake_conn_id='snowflake_default')

    soil_last_id = int(Variable.get('soil_last_processed_id', default_var=0))
    print(f"LAST PROCESSED ID: {soil_last_id}")

    query = f"SELECT * FROM agrosense.soil WHERE id > {soil_last_id} ORDER BY id"
    df = pg_hook.get_pandas_df(query)
    print(f"QUERY RESULTS: {df}")

    if not df.empty:
        conn = sf_hook.get_conn()
        write_pandas(
            conn=conn,
            df=df,
            table_name="SOIL",
            database="AGROSENSE_DB",
            schema="AGROSENSE_SCH",
            auto_create_table=True,
            overwrite=False
        )

        new_max_id = int(df['id'].max())
        Variable.set('soil_last_processed_id', new_max_id)
        print(f"Loaded {len(df)} rows. Last ID: {new_max_id}")
    else:
        print("No new soil data to load")


with DAG(
        dag_id="load_postgres_to_snowflake",
        start_date=datetime(2024, 1, 1),
        schedule_interval="@daily",
        catchup=False,
) as dag:
    load_weather_task = PythonOperator(
        task_id=LOAD_TASK_ID,
        python_callable=load_weather_to_snowflake,
    )

    load_soil_task = PythonOperator(
        task_id="load_soil_to_snowflake",
        python_callable=load_soil_to_snowflake,
    )

    load_weather_task >> load_soil_task