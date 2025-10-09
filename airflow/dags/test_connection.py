from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.postgres_hook import PostgresHook
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from datetime import datetime

def test_postgres():
    hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = hook.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    print("✅ Postgres connection successful!")
    cursor.close()
    conn.close()

def test_snowflake():
    hook = SnowflakeHook(snowflake_conn_id='snowflake_default')
    conn = hook.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_VERSION();")
    version = cursor.fetchone()
    print(f"✅ Snowflake connection successful! Version: {version}")
    cursor.close()
    conn.close()

with DAG(
    dag_id="test_connections_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    test_pg = PythonOperator(
        task_id="test_postgres_conn",
        python_callable=test_postgres,
    )

    test_sf = PythonOperator(
        task_id="test_snowflake_conn",
        python_callable=test_snowflake,
    )

    test_pg >> test_sf