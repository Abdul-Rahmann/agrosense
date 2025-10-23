CREATE DATABASE mlflow_db OWNER agrosense;

ALTER SCHEMA public OWNER TO agrosense;


-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'MLflow- database setup completed successfully';
END $$;