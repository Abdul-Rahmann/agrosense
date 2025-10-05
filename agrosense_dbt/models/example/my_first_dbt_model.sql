{{ config(materialized='table') }}

SELECT
    1 as id,
    'Example' as name,
    CURRENT_TIMESTAMP() as created_at