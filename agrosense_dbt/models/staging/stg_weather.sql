with source as (
    select * from {{ source('agrosense_source', 'weather') }}
),

final as (
    select
        'id' as weather_id,  -- No manual quotes needed!
        'latitude',
        'longitude',
        'timestamp',
        'temperature',
        'humidity',
        'solar_radiation',
        'pressure',
        'created_at'
    from source
)

select * from final