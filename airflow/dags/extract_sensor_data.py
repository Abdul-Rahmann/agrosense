import os
from dotenv import load_dotenv
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from data_generator.sensor_api_client import fetch_soil_data, insert_sensor_data

LON = os.getenv('LON') or -74.0060
LAT = os.getenv('LAT') or 47.7128
DATABASE_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT')
}
API_KEY = os.getenv('SOIL_API_KEY')

default_args = {
    'owner': 'sam',
    'depends_on_past': False,
    'retries':5,
    'retry_delay':timedelta(minutes=2)
}

with DAG(
    dag_id='extract_sensor_data',
    default_args=default_args,
    description='Extract sensor data from API',
    start_date=datetime(2025, 9, 1),
    schedule='@daily',
    catchup=False,
    tags=['sensor','iot']
) as dag:

    def fetch_sensor_data_task(**context):
        fetched_data = fetch_soil_data(LON, LAT, API_KEY)
        context['ti'].xcom_push(key='sensor_data', value=fetched_data)

    fetch_data_task = PythonOperator(
        task_id='fetch_sensor_data',
        python_callable=fetch_sensor_data_task,
        provide_context=True
    )

    def insert_sensor_data_task(**context):
        fetched_data = context['ti'].xcom_pull(key='sensor_data', task_ids='fetch_sensor_data')
        print("FETCHED DATA:")
        print(fetched_data)
        insert_sensor_data(fetched_data, DATABASE_CONFIG)

    insert_data_task = PythonOperator(
        task_id='insert_sensor_data',
        python_callable=insert_sensor_data_task,
        provide_context=True
    )

    fetch_data_task >> insert_data_task
