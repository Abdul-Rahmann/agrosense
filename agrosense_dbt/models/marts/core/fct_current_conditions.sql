-- Latest sensor readings formatted for inference
-- This is what your ML model will use for real-time predictions
with recent_readings as (
    select
        reading_timestamp,
        air_temp,
        humidity,
        soil_moisture,
        ph_surface,
        solar_radiation
    from {{ ref('int_sensor_readings_unified') }}
    where reading_timestamp >= current_timestamp - interval '24 hours'
),

with_rolling_avg as (
    select
        reading_timestamp,
        air_temp,
        humidity,
        soil_moisture,
        ph_surface,
        solar_radiation,
        -- Calculate rolling averages
        avg(air_temp) over (
            order by reading_timestamp
            rows between 167 preceding and current row
        ) as temp_7day_avg
    from recent_readings
)

select
    current_timestamp as prediction_timestamp,
    avg(air_temp) as avg_temp,
    avg(humidity) as humidity,
    avg(soil_moisture) as soil_moisture,
    avg(ph_surface) as ph,
    avg(solar_radiation) as solar_radiation,
    avg(temp_7day_avg) as temp_7day_avg
from with_rolling_avg
group by prediction_timestamp