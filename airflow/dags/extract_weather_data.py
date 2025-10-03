import os
from dotenv import load_dotenv
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

from data_generator.weather_api_client import fetch_weather_data, insert_weather_data

LAT = os.getenv('LAT') or 47.7128
LON = os.getenv('LON') or -74.0060
API_KEY = os.getenv('WEATHER_API_KEY')
DATABASE_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

default_args = {
    'owner': 'sam',
    'depends_on_past': False,
    'retries':5,
    'retry_delay':timedelta(minutes=2)
}

with DAG(
    dag_id='extract_weather_data',
    default_args=default_args,
    description='Extract weather data from API',
    start_date=datetime(2025, 9, 1),
    schedule='@daily',
    catchup=False,
    tags=['sensor','iot']
) as dag:

    def fetch_weather_data_task(**context):
        fetched_data = fetch_weather_data(LON, LAT, API_KEY)
        context['ti'].xcom_push(key='sensor_data', value=fetched_data)

    fetch_data_task = PythonOperator(
        task_id='fetch_weather_data',
        python_callable=fetch_weather_data_task,
        provide_context=True
    )

    def insert_weather_data_task(**context):
        fetched_data = context['ti'].xcom_pull(key='sensor_data', task_ids='fetch_sensor_data')
        print("FETCHED DATA:")
        print(fetched_data)
        insert_weather_data(fetched_data, DATABASE_CONFIG)

    insert_data_task = PythonOperator(
        task_id='insert_weather_data',
        python_callable=insert_weather_data_task,
        provide_context=True
    )

    fetch_data_task >> insert_data_task
