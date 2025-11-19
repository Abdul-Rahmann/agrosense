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

CREATE TABLE IF NOT EXISTS agrosense.crop_yield_predictions (
    id SERIAL PRIMARY KEY,
    area VARCHAR(255) NOT NULL,
    crop_type VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    scenario VARCHAR(50) NOT NULL,
    predicted_yield_hg_ha DECIMAL(10, 2) NOT NULL,
    predicted_yield_kg_ha DECIMAL(10, 2) NOT NULL,
    prediction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_predictions_area_crop ON agrosense.crop_yield_predictions(area, crop_type);
CREATE INDEX idx_predictions_date ON agrosense.crop_yield_predictions(prediction_date);

ALTER TABLE agrosense.crop_yield_predictions OWNER TO agrosense;
