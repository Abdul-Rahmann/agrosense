-- Smart irrigation logic based on soil moisture + weather
select
    current_date as recommendation_date,
    avg(soil_moisture) as current_moisture,
    avg(air_temp) as current_temp,
    case
        when avg(soil_moisture) < 30 and avg(air_temp) > 25 then 'IRRIGATE_NOW'
        when avg(soil_moisture) < 40 and avg(air_temp) > 20 then 'IRRIGATE_SOON'
        when avg(soil_moisture) > 70 then 'SKIP_IRRIGATION'
        else 'MONITOR'
    end as recommendation,
    -- Estimated water needed (simplified formula)
    case
        when avg(soil_moisture) < 30 then (40 - avg(soil_moisture)) * 10
        else 0
    end as estimated_water_mm
from {{ ref('int_sensor_readings_unified') }}
where reading_timestamp >= current_timestamp - interval '2 hours'