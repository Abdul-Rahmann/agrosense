with source as (
    select * from {{ source("agrosense_snowflake", "weather") }}
),

final as (
    select
        "id" as id,
        "latitude" as latitude,
        "longitude" as longitude,
        to_timestamp("timestamp" / 1000000000) as timestamp,
        "temperature" as temperature,
        "humidity" as humidity,
        "solar_radiation" as solar_radiation,
        "pressure" as pressure,
        to_timestamp("created_at" / 1000000000)  as created_at
    from source
)

select * from final