with source as (
    select * from {{ source("agrosense_snowflake","crop_yield") }}
),

final as (
    select
        area,
        item,
        year,
        hg_ha_yield,
        average_rain_fall_mm_per_year as average_rainfall_mm_per_year,
        pesticides_tonnes,
        avg_temp
    from source
)

select * from final