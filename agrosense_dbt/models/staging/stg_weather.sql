with source as (
    select * from {{ source("agrosense_snowflake", "weather") }}
),

final as (
    select
        "id" as id,
        "latitude"::float as latitude,
        "longitude"::float as longitude,
        "timestamp"::timestamp as timestamp,
        "temperature"::float as temperature,
        "humidity"::float as humidity,
        "solar_radiation"::float as solar_radiation,
        "pressure"::float as pressure,
        "created_at"::timestamp as created_at
    from source
)

select * from final