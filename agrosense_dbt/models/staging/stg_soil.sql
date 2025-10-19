with source as (
    select * from {{ source("agrosense_snowflake", "soil") }}
),

final as (
    select
        "id" as id,
        to_timestamp("timestamp" / 1000000) as timestamp,
        "t_0_cm" as t_0_cm,
        "t_10_cm" as t_10_cm,
        "moisture" as moisture,
        "ph_0_5cm" as ph_0_5cm,
        "ph_5_15cm" as ph_5_15cm,
        "ph_15_30cm" as ph_15_30cm,
        "ph_30_60cm" as ph_30_60cm,
        "ph_60_100cm" as ph_60_100cm,
        "ph_100_200cm" as ph_100_200cm,
        to_timestamp("created_at" / 1000000) as created_at  -- Fix this too!
    from source
)

select * from final