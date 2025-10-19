-- derived features to historical crop data for ML training
select
    *,
    hg_ha_yield / average_rainfall_mm_per_year as yield_per_mm_rain,
    pesticides_tonnes / hg_ha_yield as pesticides_per_yield_unit,
    case
        when avg_temp < 15 then 'cold'
        when avg_temp between 15 and 25 then 'optimal'
        else 'hot'
    end as temp_category
from {{ ref('stg_crop_yield') }}