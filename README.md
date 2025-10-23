# AgroSense - Smart Agriculture IoT Data Pipeline

## Project Overview

**Objective**: Build an end-to-end data pipeline for smart agriculture monitoring with IoT sensor data, machine learning predictions, and visualization dashboards.

**Business Value**: 
- Optimize crop yields through data-driven decisions
- Reduce water usage with smart irrigation
- Early detection of plant diseases/stress
- Automated farm monitoring and alerts

## Architecture

```
APIs (Visual Crossing, Agromonitoring) 
    ↓
Airflow DAGs (Daily Extraction)
    ↓
PostgreSQL (Raw Data - agrosense schema)
    ↓
Snowflake (Analytics Warehouse)
    ↓
dbt Models (Staging → Intermediate → Marts)
    ↓
ML Training Dataset → MLflow (Tracking) → Predictions → Dashboard
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Orchestration** | Apache Airflow | Workflow management, DAG scheduling |
| **Database** | PostgreSQL | Raw data storage, operational data |
| **Data Warehouse** | Snowflake | Analytics, aggregated data |
| **Transformation** | dbt | Data modeling, feature engineering |
| **ML Tracking** | MLflow | Experiment tracking, model registry |
| **Containerization** | Docker | Environment consistency |
| **Database Connector** | psycopg | Python-PostgreSQL interface |
| **ML Framework** | scikit-learn, pandas | Predictive modeling |
| **Visualization** | Streamlit/Plotly | Dashboards and reporting |

## Data Sources

### API Sources

#### 1. Visual Crossing Weather API
- **Endpoint**: `https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/`
- **Purpose**: Historical and forecast weather data
- **Data Points**:
  - Temperature
  - Humidity
  - Solar radiation
  - Atmospheric pressure
- **Documentation**: [Visual Crossing Docs](https://www.visualcrossing.com/resources/documentation/weather-api/)
- **Collection**: Daily via Airflow DAG `extract_weather_data`

#### 2. Agromonitoring Soil API
- **Endpoint**: `https://api.agromonitoring.com/agro/1.0/soil`
- **Purpose**: Soil conditions and temperature data
- **Data Points**:
  - Surface temperature (t_0_cm)
  - Soil temperature at 10cm depth (t_10_cm)
  - Soil moisture
  - pH levels at multiple depths (0-5cm, 5-15cm, 15-30cm, 30-60cm, 60-100cm, 100-200cm)
- **Documentation**: [Agromonitoring API Docs](https://agromonitoring.com/api)
- **Collection**: Daily via Airflow DAG `extract_sensor_data`

#### 3. Crop Yield Dataset
- **Source**: Kaggle - [Crop Yield Prediction Dataset](https://www.kaggle.com/datasets/patelris/crop-yield-prediction-dataset)
- **File**: `yield_df.csv` → Seeded in dbt as `seeds/crop_yield.csv`
- **Purpose**: Historical crop yield data for ML model training
- **Data Points**:
  - Crop type (item)
  - Year
  - Area (hectares)
  - Yield (hg/ha)
  - Average rainfall (mm/year)
- **Usage**: Loaded via `dbt seed` and transformed in staging layer (`stg_crop_yield.sql`)

## Database Schema Design

### PostgreSQL (Raw Data Layer)

```sql
CREATE SCHEMA IF NOT EXISTS agrosense AUTHORIZATION agrosense;

ALTER ROLE agrosense SET search_path TO agrosense, public;

SET timezone = 'UTC';

-- Weather data table
CREATE TABLE IF NOT EXISTS agrosense.weather (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL(8,5) NOT NULL,
    longitude DECIMAL(8,5) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    solar_radiation DECIMAL(8,2),
    pressure DECIMAL(7,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_weather_record UNIQUE (latitude, longitude, timestamp)
);

-- Soil data table
CREATE TABLE IF NOT EXISTS agrosense.soil (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    t_0_cm DECIMAL(5,2),
    t_10_cm DECIMAL(5,2),
    moisture DECIMAL(5,2),
    ph_0_5cm DECIMAL(5,2),
    ph_5_15cm DECIMAL(5,2),
    ph_15_30cm DECIMAL(5,2),
    ph_30_60cm DECIMAL(5,2),
    ph_60_100cm DECIMAL(5,2),
    ph_100_200cm DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance
```sql
-- Weather table indexes
CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON agrosense.weather(timestamp);
CREATE INDEX IF NOT EXISTS idx_weather_location ON agrosense.weather(latitude, longitude);

-- Soil table indexes
CREATE INDEX IF NOT EXISTS idx_soil_timestamp ON agrosense.soil(timestamp);
```

### Snowflake (Analytics Layer)

Data is loaded from PostgreSQL to Snowflake via the `load_postgres_to_snowflake` DAG with separate tasks:
- `load_to_snowflake` - Loads weather data
- `load_soil_to_snowflake` - Loads soil data

## dbt Project Structure

### Data Flow
```
Sources (Snowflake Raw Tables)
    ↓
Staging Models (stg_*)
    ↓
Intermediate Models (int_*)
    ↓
Marts (Core & Analytics)
```

### Models

#### Staging Layer (`models/staging/`)
- **`stg_weather.sql`** - Cleaned weather data from Snowflake
- **`stg_soil.sql`** - Cleaned soil data from Snowflake
- **`stg_crop_yield.sql`** - Cleaned crop yield data from seed

#### Intermediate Layer (`models/intermediate/`)
- **`int_sensor_readings_unified.sql`** - Unified view of weather and soil sensors by timestamp
- **`int_daily_conditions.sql`** - Daily aggregations of sensor readings
- **`int_crop_yield_features.sql`** - Feature engineering for crop yield predictions

#### Core Marts (`models/marts/core/`)
- **`dim_crop_benchmarks.sql`** - Dimension table with crop type benchmarks and averages
- **`fct_sensor_monitoring.sql`** - Fact table with real-time sensor monitoring and alerts
- **`fct_current_conditions.sql`** - Current farm conditions for predictions
- **`fct_ml_training_dataset.sql`** - ML-ready dataset for model training

#### Analytics Marts (`models/marts/analytics/`)
- **`rpt_daily_farm_summary.sql`** - Daily farm operations summary report
- **`rpt_irrigation_recommendations.sql`** - Irrigation recommendations based on soil moisture

### Data Quality Tests
Comprehensive schema tests implemented across all layers:
- Not null constraints on critical fields
- Unique constraints on primary keys
- Accepted values tests for categorical fields
- Relationship tests between fact and dimension tables

## Airflow DAGs

### Active DAGs

#### 1. `extract_sensor_data`
- **Schedule**: Daily at midnight (UTC)
- **Tasks**:
  - `fetch_sensor_data` - Calls Agromonitoring API
  - `insert_sensor_data` - Inserts into PostgreSQL `agrosense.soil` table
- **Retry**: Up to 6 attempts with exponential backoff

#### 2. `extract_weather_data`
- **Schedule**: Daily at midnight (UTC)
- **Tasks**:
  - `fetch_weather_data` - Calls Visual Crossing API
  - `insert_weather_data` - Inserts into PostgreSQL `agrosense.weather` table
- **Retry**: Up to 6 attempts with exponential backoff

#### 3. `load_postgres_to_snowflake` (formerly `postres_to_snowflake`)
- **Schedule**: Daily at midnight (UTC)
- **Tasks**:
  - `load_to_snowflake` - Transfers weather data to Snowflake
  - `load_soil_to_snowflake` - Transfers soil data to Snowflake
- **Dependency**: Runs after data extraction DAGs complete

#### 4. `test_connections_dag`
- **Purpose**: Connection testing for PostgreSQL and Snowflake
- **Tasks**:
  - `test_postgres_conn`
  - `test_snowflake_conn`

## Machine Learning Models

### 1. Crop Yield Prediction
- **Input Features**: Weather history, soil conditions, crop type, rainfall
- **Output**: Expected yield (hg/ha)
- **Training Data**: `fct_ml_training_dataset` in dbt marts
- **Algorithm**: Random Forest Regression

### 2. Irrigation Optimization
- **Input Features**: Soil moisture, weather forecast, crop requirements
- **Output**: Irrigation recommendations (None, Light, Moderate, Heavy)
- **Report**: `rpt_irrigation_recommendations` in dbt analytics marts
- **Logic**: Rules-based system using moisture thresholds

### 3. Sensor Anomaly Detection
- **Input Features**: Temperature, humidity, pH levels
- **Output**: Alert flags (OK, ANOMALY, CRITICAL)
- **Implementation**: `fct_sensor_monitoring` with threshold-based alerts
- **Algorithm**: Statistical outlier detection

### 4. Soil Health Scoring
- **Input Features**: pH levels across depths, moisture, temperature gradients
- **Output**: Soil health recommendations
- **Data Source**: Multi-depth pH profiling from soil table

## Project Structure

```
agrosense/
├── README.md
├── docker-compose.yml
├── .env
├── .gitignore
├── venv/                         # Python virtual environment
│
├── requirements/
│   ├── airflow-requirements.txt
│   ├── dbt-requirements.txt
│   └── mlflow-requirements.txt
│
├── dockerfiles/
│   ├── Dockerfile.airflow
│   ├── Dockerfile.dbt
│   └── Dockerfile.mlflow
│
├── sql/
│   ├── 01_postgres_setup.sql      # PostgreSQL schema setup
│   ├── 02_airflow_db.sql          # Airflow database init
│   ├── 03_mlflow_db.sql           # MLflow database init
│   └── 03_snowflake_setup.txt     # Snowflake setup instructions
│
├── data_generator/
│   ├── mock_data.py               # Mock data generation utilities
│   ├── sensor_api_client.py       # Agromonitoring API client
│   └── weather_api_client.py      # Visual Crossing API client
│
├── airflow/
│   ├── dags/
│   │   ├── extract_sensor_data.py
│   │   ├── extract_weather_data.py
│   │   ├── postres_to_snowflake.py
│   │   └── test_connection.py
│   ├── logs/
│   ├── config/
│   └── plugins/
│
├── agrosense_dbt/
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── sources.yml
│   │   ├── staging/
│   │   │   ├── schema.yml
│   │   │   ├── stg_weather.sql
│   │   │   ├── stg_soil.sql
│   │   │   └── stg_crop_yield.sql
│   │   ├── intermediate/
│   │   │   ├── schema.yml
│   │   │   ├── int_sensor_readings_unified.sql
│   │   │   ├── int_daily_conditions.sql
│   │   │   └── int_crop_yield_features.sql
│   │   └── marts/
│   │       ├── core/
│   │       │   ├── schema.yml
│   │       │   ├── dim_crop_benchmarks.sql
│   │       │   ├── fct_sensor_monitoring.sql
│   │       │   ├── fct_current_conditions.sql
│   │       │   └── fct_ml_training_dataset.sql
│   │       └── analytics/
│   │           ├── schema.yml
│   │           ├── rpt_daily_farm_summary.sql
│   │           └── rpt_irrigation_recommendations.sql
│   ├── seeds/
│   │   └── crop_yield.csv
│   ├── macros/
│   ├── tests/
│   ├── analyses/
│   ├── snapshots/
│   ├── logs/
│   └── target/
│
├── ml_models/
│   ├── src/
│   ├── models/
│   └── notebooks/
│
└── dashboard/
    └── streamlit_app.py
```

## Implementation Status

### ✅ Phase 1: Foundation Setup (COMPLETE)
- [x] PostgreSQL database with agrosense schema
- [x] Airflow installation and configuration
- [x] Visual Crossing Weather API integration
- [x] Agromonitoring Soil API integration
- [x] Docker environment setup

### ✅ Phase 2: Data Pipeline (COMPLETE)
- [x] Airflow DAG for weather data extraction
- [x] Airflow DAG for soil data extraction
- [x] PostgreSQL to Snowflake pipeline
- [x] dbt staging models for all sources
- [x] dbt intermediate transformation models
- [x] Data quality tests and validation
- [x] Scheduled daily execution (running since Sept 28, 2025)

### ✅ Phase 3: Analytics & ML Preparation (COMPLETE)
- [x] dbt core marts (dimensions and facts)
- [x] dbt analytics marts (reports)
- [x] ML training dataset preparation
- [x] Feature engineering in dbt
- [x] Crop yield seed data integration
- [x] Sensor monitoring with alerts

### 🔄 Phase 4: ML Models & Visualization (IN PROGRESS)
- [ ] ML model training pipeline in Airflow
- [ ] MLflow experiment tracking setup
- [ ] Model registry and versioning
- [ ] Model deployment and prediction scheduling
- [ ] Streamlit dashboard development
- [ ] Real-time monitoring interface
- [ ] Model performance tracking
- [ ] Alert notification system

## Environment Variables

Create a `.env` file with the following:

```bash
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agrosense
POSTGRES_USER=agrosense
POSTGRES_PASSWORD=your_password_here

# API Keys
VISUAL_CROSSING_API_KEY=your_key_here
AGROMONITORING_API_KEY=your_key_here

# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=AGROSENSE
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_SCHEMA=RAW

# Airflow Configuration
AIRFLOW_UID=50000
AIRFLOW_PROJ_DIR=.
```

## Key Resources & Links

### Documentation
- **Apache Airflow**: https://airflow.apache.org/docs/
- **dbt Documentation**: https://docs.getdbt.com/
- **Snowflake Docs**: https://docs.snowflake.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **MLflow**: https://mlflow.org/docs/latest/index.html

### APIs & Data Sources
- **Visual Crossing Weather**: https://www.visualcrossing.com/resources/documentation/weather-api/
- **Agromonitoring**: https://agromonitoring.com/api
- **Crop Yield Dataset (Kaggle)**: https://www.kaggle.com/datasets/patelris/crop-yield-prediction-dataset

### ML Resources
- **Agricultural ML Papers**: Google Scholar "precision agriculture machine learning"
- **Crop Yield Prediction**: Research on weather-based modeling
- **Soil Health Analysis**: Multi-depth soil profiling research

## Running the Project

### Prerequisites
1. Docker and Docker Compose installed
2. Python 3.8+ with virtual environment
3. API keys from Visual Crossing and Agromonitoring
4. Snowflake account with database created
5. PostgreSQL client tools (optional, for manual queries)

### Initial Setup

#### 1. Clone and Setup Environment
```bash
git clone <repository-url>
cd agrosense

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (optional for local development)
pip install -r requirements/airflow-requirements.txt
pip install -r requirements/dbt-requirements.txt
pip install -r requirements/mlflow-requirements.txt
```

#### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```bash
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agrosense
POSTGRES_USER=agrosense
POSTGRES_PASSWORD=your_password_here

# API Keys
VISUAL_CROSSING_API_KEY=your_key_here
AGROMONITORING_API_KEY=your_key_here

# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=AGROSENSE
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_SCHEMA=RAW

# Airflow Configuration
AIRFLOW_UID=50000
AIRFLOW_PROJ_DIR=.

# MLflow Configuration
MLFLOW_TRACKING_URI=postgresql://mlflow:mlflow@postgres:5432/mlflow
```

#### 3. Initialize Databases
```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Run setup scripts
psql -h localhost -U postgres -f sql/01_postgres_setup.sql
psql -h localhost -U postgres -f sql/02_airflow_db.sql
psql -h localhost -U postgres -f sql/03_mlflow_db.sql

# Setup Snowflake (follow instructions in sql/03_snowflake_setup.txt)
```

#### 4. Start Services with Docker Compose
```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f airflow-scheduler
```

### Setup Steps
1. Clone the repository
2. Configure `.env` file with credentials
3. Start Airflow: `docker-compose up -d`
4. Access Airflow UI: http://localhost:8080
5. Enable DAGs:
   - `extract_sensor_data`
   - `extract_weather_data`
   - `load_postgres_to_snowflake`
6. Run dbt models:
   ```bash
   cd agrosense_dbt
   dbt seed  # Load crop yield data
   dbt run   # Run all models
   dbt test  # Validate data quality
   ```

### API Client Usage

The `data_generator/` folder contains API client utilities:

```python
# Example: Fetch weather data
from data_generator.weather_api_client import WeatherAPIClient

client = WeatherAPIClient(api_key="your_key")
weather_data = client.get_weather(latitude=40.7128, longitude=-74.0060)

# Example: Fetch soil data
from data_generator.sensor_api_client import SensorAPIClient

client = SensorAPIClient(api_key="your_key")
soil_data = client.get_soil_data()
```

### Monitoring
- **Airflow UI**: http://localhost:8080
- **Airflow Logs**: `airflow/logs/` directory
- **DAG Runs**: Daily scheduled runs at midnight UTC
- **dbt Logs**: `agrosense_dbt/logs/dbt.log`
- **Data Quality**: dbt test results in target directory
- **MLflow UI**: http://localhost:5000 (when implemented)

## Success Metrics

- **Data Pipeline**: 99%+ data quality, <1 hour latency ✅
- **Scheduled Runs**: Daily execution since Sept 28, 2025 ✅
- **Data Coverage**: Weather + Soil + Crop Yield datasets ✅
- **ML Models**: Training dataset prepared, models pending deployment 🔄
- **Dashboard**: Development pending 🔄
- **System**: Automated retries, error handling ✅

## Data Collection History

Based on Airflow logs:
- **First Data Collection**: September 28, 2025
- **Continuous Operation**: 25+ days of automated daily runs
- **Success Rate**: High (multiple retry mechanisms in place)
- **Data Sources**: 
  - Weather data: Collected daily via Visual Crossing API
  - Soil sensor data: Collected daily via Agromonitoring API
  - Historical crop yield: Kaggle dataset seeded in dbt (static reference data)

---

## Next Steps

### Immediate Priorities
1. **ML Model Development**
   - Train crop yield prediction model using `fct_ml_training_dataset`
   - Deploy model training as Airflow DAG
   - Schedule regular model retraining

2. **Dashboard Development**
   - Build Streamlit app connecting to Snowflake marts
   - Display real-time sensor readings from `fct_sensor_monitoring`
   - Show daily summaries from `rpt_daily_farm_summary`
   - Present irrigation recommendations from `rpt_irrigation_recommendations`

3. **Alerting System**
   - Implement email/SMS notifications for critical alerts
   - Connect to alert flags in `fct_sensor_monitoring`
   - Set up monitoring for DAG failures

### Future Enhancements
- Additional crop types and regions
- Weather forecast integration for predictive irrigation
- Mobile app development
- Integration with farm equipment IoT devices