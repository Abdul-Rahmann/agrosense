-- Creating a synthetic current conditions for crop yield prediction cos there aren't any free API I could source data from
-- Having different scenarios for each crop/region for this use case
-- 1. Optimistic: better conditions,
-- 2. Pessimistic: drought, high temp
-- 3. Conservative: minimal inputs

with base_scenarios as (
    select
        area,
        item as crop_type,
        avg(average_rainfall_mm_per_year) as baseline_rainfall,
        avg(pesticides_tonnes) as baseline_pesticides,
        avg(avg_temp) as baseline_temp
    from {{ ref('stg_crop_yield') }}
    where year >= 2008
    group by area, item
),

scenarios as (
    -- Create multiple scenarios for each crop/region
    select
        area,
        crop_type,
        2025 as year,
        'baseline' as scenario,
        baseline_rainfall as average_rainfall_mm_per_year,
        baseline_pesticides as pesticides_tonnes,
        baseline_temp as avg_temp
    from base_scenarios
    
    union all
    
    -- Optimistic scenario (better conditions)
    select
        area,
        crop_type,
        2025 as year,
        'optimistic' as scenario,
        baseline_rainfall * 1.15 as average_rainfall_mm_per_year,
        baseline_pesticides * 1.10 as pesticides_tonnes,
        baseline_temp - 0.5 as avg_temp
    from base_scenarios
    
    union all
    
    -- Pessimistic scenario (drought, high temp)
    select
        area,
        crop_type,
        2025 as year,
        'pessimistic' as scenario,
        baseline_rainfall * 0.75 as average_rainfall_mm_per_year,
        baseline_pesticides * 1.20 as pesticides_tonnes,
        baseline_temp + 1.5 as avg_temp
    from base_scenarios
    
    union all
    
    -- Conservative scenario (minimal inputs)
    select
        area,
        crop_type,
        2025 as year,
        'conservative' as scenario,
        baseline_rainfall * 0.95 as average_rainfall_mm_per_year,
        baseline_pesticides * 0.80 as pesticides_tonnes,
        baseline_temp as avg_temp
    from base_scenarios
),
final as (select
    area,
    crop_type,
    year,
    scenario,
    average_rainfall_mm_per_year,
    pesticides_tonnes,
    avg_temp,
    pesticides_tonnes / average_rainfall_mm_per_year as pesticide_intensity,
    year % 10 as year_in_decade,
    case when year >= 2010 then 'modern' else 'historical' end as era,
    current_timestamp as prediction_requested_at

from scenarios
where average_rainfall_mm_per_year > 0
)

select * from final