
select
    item as crop_type,

    -- Yield statistics
    avg(hg_ha_yield) as avg_yield,
    percentile_cont(0.25) within group (order by hg_ha_yield) as p25_yield,
    percentile_cont(0.75) within group (order by hg_ha_yield) as p75_yield,
    max(hg_ha_yield) as max_yield,

    -- Optimal conditions
    avg(avg_temp) as optimal_temp,
    stddev(avg_temp) as temp_stddev,
    avg(average_rainfall_mm_per_year) as optimal_rainfall,
    avg(pesticides_tonnes) as typical_pesticide_use,

    count(*) as sample_size
from {{ ref('stg_crop_yield') }}
group by item
having count(*) >= 10  -- Only crops with enough samples