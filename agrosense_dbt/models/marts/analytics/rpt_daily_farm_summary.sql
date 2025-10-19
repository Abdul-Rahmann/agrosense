-- Daily rollup for dashboard
select
    date,
    avg_daily_temp,
    avg_humidity,
    avg_soil_moisture,
    avg_ph,
    reading_count,
    -- Compare to yesterday
    avg_daily_temp - lag(avg_daily_temp) over (order by date) as temp_change_24h,
    -- Data quality
    case when reading_count < 20 then 'WARNING' else 'HEALTHY' end as sensor_status
from {{ ref('int_daily_conditions') }}
order by date desc