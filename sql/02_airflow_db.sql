CREATE DATABASE airflow_db OWNER agrosense;

ALTER SCHEMA public OWNER TO agrosense;

ALTER ROLE agrosense SET search_path TO public;