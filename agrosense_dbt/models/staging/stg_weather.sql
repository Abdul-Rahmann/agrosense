with source as (
    select * from {{ source("agrosense_snowflake", "weather") }}
),

final as (
    select
        "id" as id,
        "latitude" as latitude,
        "longitude" as longitude,
        "timestamp" as timestamp,
        "temperature" as temperature,
        "humidity" as humidity,
        "solar_radiation" as solar_radiation,
        "pressure" as pressure,
        "created_at" as created_at
    from source
)

select * from final