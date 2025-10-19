-- Real-time monitoring for dashboard and alerts
select
    reading_timestamp,
    air_temp,
    humidity,
    soil_moisture,
    ph_surface,
    -- Data quality flags
    case when air_temp < -50 or air_temp > 60 then 'ANOMALY' else 'OK' end as temp_flag,
    case when soil_moisture < 0 or soil_moisture > 100 then 'ANOMALY' else 'OK' end as moisture_flag,
    -- Alert conditions
    case
        when soil_moisture < 20 then 'LOW_MOISTURE_ALERT'
        when soil_moisture > 80 then 'HIGH_MOISTURE_ALERT'
        else 'NORMAL'
    end as irrigation_alert
from {{ ref('int_sensor_readings_unified') }}
where reading_timestamp >= current_timestamp - interval '7 days'