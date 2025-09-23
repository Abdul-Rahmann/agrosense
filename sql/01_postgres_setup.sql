CREATE SCHEMA IF NOT EXISTS agrosense AUTHORIZATION agrosense;

ALTER ROLE agrosense SET search_path TO agrosense, public;

CREATE TABLE IF NOT EXISTS agrosense.weather (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL(8,5) NOT NULL,
    longitude DECIMAL(8,5) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    solar_radiation DECIMAL(8,2),
    pressure DECIMAL(7,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_weather_record UNIQUE (latitude, longitude, timestamp)
);