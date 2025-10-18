with source as (
    select * from {{ source("agrosense_snowflake", "soil") }}
),

final as (
    select
        "id" as id,
        "timestamp"::timestamp as timestamp,
        "t_0_cm"::float as t_0_cm,
        "t_10_cm"::float as t_10_cm,
        "moisture"::float as moisture,
        "ph_0_5cm"::float as ph_0_5cm,
        "ph_5_15cm"::float as ph_5_15cm,
        "ph_15_30cm"::float as ph_15_30cm,
        "ph_30_60cm"::float as ph_30_60cm,
        "ph_60_100cm"::float as ph_60_100cm,
        "ph_100_200cm"::float as ph_100_200cm,
        "created_at"::timestamp as created_at
    from source
)

select * from final