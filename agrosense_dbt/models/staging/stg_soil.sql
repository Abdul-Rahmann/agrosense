with source as (
    select * from {{ source('agrosense_source', 'soil') }}
),

final as (
    select
        'id',
        'timestamp' as soil_timestamp,
        't_0_cm' as temperature_0cm,
        't_10_cm' as temperature_10cm,
        'moisture',
        'ph_0_5cm',
        'ph_5_15cm',
        'ph_15_30cm',
        'ph_30_60cm',
        'ph_60_100cm',
        'ph_100_200cm',
        'created_at'
    from source
)

select * from final