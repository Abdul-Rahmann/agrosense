-- daily aggregates for matching with crop yield data (which is yearly)
select
    date_trunc('day', reading_timestamp) as date,
    avg(air_temp) as avg_daily_temp,
    min(air_temp) as min_daily_temp,
    max(air_temp) as max_daily_temp,
    avg(humidity) as avg_humidity,
    avg(soil_moisture) as avg_soil_moisture,
    avg(ph_surface) as avg_ph,
    sum(solar_radiation) as total_solar_radiation,
    count(*) as reading_count
from {{ ref('int_sensor_readings_unified') }}
group by 1