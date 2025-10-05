-- This model references the first model
SELECT
    id,
    name,
    created_at,
    'processed' as status
FROM {{ ref('my_first_dbt_model') }}
WHERE id = 1