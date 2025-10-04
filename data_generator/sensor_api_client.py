import os
import sys
import pathlib
import requests
import psycopg
import datetime
from dotenv import load_dotenv

sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()))

from data_generator.mock_data import mock_soil_data, get_ph_profile

load_dotenv()

BASE_URL = f"https://api.agromonitoring.com/agro/1.0/soil"
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

def fetch_soil_data(lon, lat, key):
    try:
        url =  f"{BASE_URL}?lat={lat}&lon={lon}&appid={key}"
        print("URL: ",url)
        response = requests.get(url)
        if response.status_code == 200:
            print("Data Fetched Successfully!")
            return response.json() | get_ph_profile()
        else:
            return None
    except requests.RequestException as e:
        print(f"An error occurred while fetching the api data: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

def insert_sensor_data(data, DATABASE_CONFIG):
    try:
        with psycopg.connect(**DATABASE_CONFIG) as conn:
            with conn.cursor() as cur:
                query = """
                INSERT INTO agrosense.soil (
                    timestamp, 
                    t_0_cm, 
                    t_10_cm,
                    moisture,
                    ph_0_5cm,
                    ph_5_15cm,
                    ph_15_30cm,
                    ph_30_60cm,
                    ph_60_100cm,
                    ph_100_200cm
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                row = (
                    datetime.datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d %H:%M:%S'),
                    data['t0'],
                    data['t10'],
                    data['moisture'],
                    data['0-5cm'],
                    data['5-15cm'],
                    data['15-30cm'],
                    data['30-60cm'],
                    data['60-100cm'],
                    data['100-200cm']
                )
                cur.execute(query, row)
                conn.commit()
                print(f"Inserted {len(row)} soil data inserted successfully.")

    except psycopg.Error as e:
        print(f"An error occurred while inserting weather data: {e}")

# api_response = mock_soil_data()
# api_response = fetch_soil_data(LON, LAT, API_KEY)
# insert_sensor_data(api_response, DATABASE_CONFIG)
