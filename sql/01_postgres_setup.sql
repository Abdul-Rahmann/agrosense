CREATE SCHEMA IF NOT EXISTS agrosense AUTHORIZATION agrosense;

ALTER ROLE agrosense SET search_path TO agrosense, public;

SET timezone = 'UTC';

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

CREATE TABLE IF NOT EXISTS agrosense.soil (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    t_0_cm DECIMAL(5,2),
    t_10_cm DECIMAL(5,2),
    moisture DECIMAL(5,2),
    ph_0_5cm DECIMAL(5,2),
    ph_5_15cm DECIMAL(5,2),
    ph_15_30cm DECIMAL(5,2),
    ph_30_60cm DECIMAL(5,2),
    ph_60_100cm DECIMAL(5,2),
    ph_100_200cm DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);