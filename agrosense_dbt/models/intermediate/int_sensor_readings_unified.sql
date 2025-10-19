-- feeds into ML feature engineering
with weather as (
    select
        timestamp,
        latitude,
        longitude,
        temperature as air_temp,
        humidity,
        solar_radiation,
        pressure
    from {{ ref('stg_weather') }}
),

soil as (
    select
        timestamp,
        t_0_cm as soil_temp_surface,
        t_10_cm as soil_temp_10cm,
        moisture as soil_moisture,
        ph_0_5cm as ph_surface
    from {{ ref('stg_soil') }}
),

weather_rounded as (
    select
        date_trunc('minute', timestamp) as timestamp_minute,
        latitude,
        longitude,
        air_temp,
        humidity,
        solar_radiation,
        pressure
    from weather
),

soil_rounded as (
    select
        date_trunc('minute', timestamp) as timestamp_minute,
        soil_temp_surface,
        soil_temp_10cm,
        soil_moisture,
        ph_surface
    from soil
),

joined as (
    select
        w.timestamp_minute as reading_timestamp,
        w.latitude,
        w.longitude,
        w.air_temp,
        w.humidity,
        w.solar_radiation,
        w.pressure,
        s.soil_temp_surface,
        s.soil_temp_10cm,
        s.soil_moisture,
        s.ph_surface
    from weather_rounded w
    inner join soil_rounded s
        on w.timestamp_minute = s.timestamp_minute
)

select * from joined