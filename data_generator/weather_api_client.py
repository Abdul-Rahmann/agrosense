# API docs - https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/
import os
import sys
import pathlib
import requests
import psycopg
import datetime
from dotenv import load_dotenv

sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()))

from data_generator.mock_data import mock_weather_data

load_dotenv()

BASE_URL = r"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
LON = os.getenv('LON') or -74.0060
LAT = os.getenv('LAT') or 47.7128
DATABASE_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT')
}
API_KEY = os.getenv('WEATHER_API_KEY')

def fetch_weather_data(lon,lat,key):
    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        url = f"{BASE_URL}{lat},{lon}/{today}?key={key}"
        print(url)
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"An error occurred while fetching the api data: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

def insert_weather_data(data, DATABASE_CONFIG):
    try:
        with psycopg.connect(**DATABASE_CONFIG) as conn:
            with conn.cursor() as cur:
                query = """
                INSERT INTO agrosense.weather (
                    latitude, 
                    longitude, 
                    timestamp,
                    temperature,
                    humidity,
                    solar_radiation,
                    pressure
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (latitude, longitude, timestamp) DO NOTHING;
                """

                latitude = data['latitude']
                longitude = data['longitude']
                hourly_data = [
                    (
                        latitude,
                        longitude,
                        datetime.datetime.fromtimestamp(hour['datetimeEpoch']).strftime('%Y-%m-%d %H:%M:%S'),
                        (hour.get('temp') - 32) * 5.0 / 9.0 if hour.get('temp') is not None else None,  # Fahrenheit → Celsius
                        hour.get('humidity'),
                        hour.get('solarradiation'),
                        hour.get('pressure')
                    )
                    for day in data['days']
                    for hour in day['hours']
                ]
                cur.executemany(query, hourly_data)
                conn.commit()
                print(f"{len(hourly_data)} weather data inserted successfully.")

    except psycopg.Error as e:
        print(f"An error occurred while inserting weather data: {e}")

# api_response = fetch_weather_data(LAT,LON,API_KEY)
# api_response = mock_weather_data()
# insert_weather_data(api_response, DATABASE_CONFIG)
