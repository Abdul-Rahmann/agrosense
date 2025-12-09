# AgroSense - Smart Agriculture IoT Data Pipeline

## Project Overview

**Objective**: Build an end-to-end data pipeline for smart agriculture monitoring with IoT sensor data, machine learning predictions, and visualization dashboards.

**Business Value**: 
- Optimize crop yields through data-driven decisions
- Reduce water usage with smart irrigation
- Automated farm monitoring and alerts

## Dashboard Preview

![AgroSense Landing Page](assets/landing_page.png)

### Crop Yield Prediction Page

 ![AgroSense Crop Yield Prediction](assets/crop_prediction_page.png)

**Live Farm Monitoring Dashboard** featuring:
- 🌡️ Real-time sensor readings (temperature, humidity, soil moisture, pH)
- ⚠️ Active alerts and anomaly detection
- 📈 7-day trend visualizations with interactive charts
- 💧 Irrigation recommendations based on soil conditions

**Tech Stack**: Streamlit + Plotly + Snowflake direct connection

## Architecture

                ┌──────────────────────────┐
                │      External APIs       │
                │  - Weather (VisualX)     │
                │  - Soil (AgroMonitor)    │
                └─────────────┬────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Airflow DAGs    │
                    │ (Daily Extraction)│
                    └─────────┬─────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │   PostgreSQL (Raw)   │
                   │  weather + soil data │
                   └───────────┬──────────┘
                               │
                               ▼
                ┌────────────────────────────────┐
                │        Snowflake Warehouse      │
                │    (Analytics + Cleaned Data)   │
                └──────────────────┬──────────────┘
                                   │
                                   ▼
                            ┌──────────┐
                            │   dbt    │
                            │ Models   │
                            │ Stg→Int→Marts
                            └─────┬────┘
                                  │
                                  ▼
                   ┌────────────────────────────────┐
                   │   ML Pipeline (MLflow + RF)    │
                   │  - Weekly training              │
                   │  - Daily prediction             │
                   └──────────────┬─────────────────┘
                                  │
                                  ▼
                     ┌────────────────────┐
                     │ PostgreSQL (Preds) │
                     │ ML predictions tbl │
                     └───────────┬────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ Streamlit Dashboard    │
                    │  - Real-time sensors   │
                    │  - Alerts              │
                    │  - Yield predictions   │
                    └────────────────────────┘

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Orchestration** | Apache Airflow | Workflow management, DAG scheduling |
| **Database** | PostgreSQL | Raw data storage, operational data, predictions |
| **Data Warehouse** | Snowflake | Analytics, aggregated data |
| **Transformation** | dbt | Data modeling, feature engineering |
| **ML Tracking** | MLflow | Experiment tracking, model registry |
| **ML Framework** | scikit-learn, pandas | Predictive modeling (Random Forest) |
| **Visualization** | Streamlit, Plotly | Real-time dashboards and monitoring |
| **Containerization** | Docker | Environment consistency |
| **Database Connector** | psycopg, snowflake-connector | Python-Database interfaces |

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

-- ML Predictions table
CREATE TABLE IF NOT EXISTS agrosense.crop_yield_predictions (
    id SERIAL PRIMARY KEY,
    area VARCHAR(255) NOT NULL,
    crop_type VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    scenario VARCHAR(50) NOT NULL,
    predicted_yield_hg_ha DECIMAL(10, 2) NOT NULL,
    predicted_yield_kg_ha DECIMAL(10, 2) NOT NULL,
    predicted_yield_tonnes_ha DECIMAL(12, 4),
    model_version VARCHAR(50),
    prediction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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

-- Predictions table indexes
CREATE INDEX idx_predictions_area_crop ON agrosense.crop_yield_predictions(area, crop_type);
CREATE INDEX idx_predictions_date ON agrosense.crop_yield_predictions(prediction_date);
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

### Data Extraction & Loading DAGs

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

#### 3. `load_postgres_to_snowflake`
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

### Machine Learning DAGs

#### 5. `train_crop_yield_model`
- **Schedule**: Weekly on Sundays at 2 AM UTC (`0 2 * * 0`)
- **Purpose**: Retrain crop yield prediction model with latest data
- **Tasks**:
  1. `load_data` - Load training data from Snowflake (`fct_ml_training_dataset`)
  2. `preprocess_data` - Feature engineering and train/test split
  3. `train_model` - Train Random Forest model and log to MLflow
  4. `send_training_summary` - Log training metrics and model performance
  5. `cleanup_temp_files` - Clean up temporary files
- **Model Tracking**: Logs experiments to MLflow with run ID
- **Model Artifacts**: Saves trained model and encoders to `ml_models/models/crop_yield/`

#### 6. `predict_crop_yield`
- **Schedule**: Daily at 6 AM UTC (`0 6 * * *`)
- **Purpose**: Generate daily crop yield predictions for current growing season
- **Tasks**:
  1. `load_current_conditions` - Load current conditions from Snowflake (`fct_current_conditions`)
  2. `make_predictions` - Generate predictions using production model from MLflow registry
  3. `save_to_database` - Save predictions to PostgreSQL `crop_yield_predictions` table
  4. `analyze_scenarios` - Analyze predictions across different scenarios
- **Model Source**: Loads from MLflow Model Registry (Production stage) or latest trained model
- **Output**: Predictions in hg/ha, kg/ha, and tonnes/ha with scenario analysis

## Machine Learning Models

### 1. Crop Yield Prediction Model

**Model Type**: Random Forest Regression

**Performance Metrics**:
- **Test R²**: 0.9892 (98.92% variance explained)
- **Test RMSE**: 8,853.31 hg/ha
- **Test MAE**: 3,597.14 hg/ha
- **Mean APE**: 8.77%
- **Median APE**: 2.08%

**Model Parameters**:
```python
{
    'n_estimators': 100,
    'max_depth': 20,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
    'random_state': 42,
    'n_jobs': -1
}
```

**Input Features**:
- Area (geographic region)
- Crop type
- Year
- Average rainfall (mm/year)
- Pesticides usage (tonnes)
- Average temperature
- Year in decade
- Era (historical period)

**Output**: Expected yield in hg/ha, kg/ha, and tonnes/ha

**Training Process**:
1. Data loaded from `fct_ml_training_dataset` in Snowflake
2. Label encoding for categorical features (Area, Crop Type, Era)
3. 80/20 train/test split
4. Random Forest training with hyperparameters
5. Model evaluation and metrics calculation
6. MLflow experiment tracking and model registry
7. Model artifacts saved (model.pkl, encoders.pkl)

**Prediction Pipeline**:
1. Load current conditions from `fct_current_conditions`
2. Apply same preprocessing (label encoding)
3. Load production model from MLflow registry
4. Generate predictions for multiple scenarios
5. Save to PostgreSQL for dashboard visualization
6. Scenario analysis (optimal, average, drought conditions)

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

## MLflow Integration

### Experiment Tracking
- **Tracking URI**: Configured in `ml_models/config/config.yml`
- **Experiments**: Each training run logged with parameters, metrics, and artifacts
- **Run Metadata**: Training date, data size, feature count, model performance

### Model Registry
- **Model Name**: `crop_yield_predictor`
- **Stages**: Development → Staging → Production
- **Versioning**: Automatic versioning with each training run
- **Artifacts**: Model file, encoders, training metrics, feature importance

### Model Deployment
- Production model automatically loaded from registry in prediction DAG
- Fallback to latest trained model if registry unavailable
- Model version tracking in predictions table

## Dashboard & Visualization

### Streamlit Dashboard

**Current Features**:
- **Real-time Sensor Monitoring**
  - Current temperature, humidity, soil moisture, pH levels
  - Color-coded alerts for anomalies
  - Last updated timestamp
  
- **Active Alerts**
  - Low/high soil moisture warnings
  - Temperature anomaly detection
  - Irrigation recommendations
  
- **7-Day Trends**
  - Temperature trends over time
  - Humidity patterns
  - Soil moisture changes
  - pH level monitoring
  
- **Raw Data Access**
  - Last 100 sensor readings in tabular format
  - CSV download capability
  - Timestamp filtering

**Technical Stack**:
- Streamlit for UI framework
- Plotly for interactive charts
- Direct Snowflake connection via `snowflake-connector-python`
- Data caching (5-minute TTL) for performance
- Real-time refresh capability

**Data Source**: Connects to Snowflake `fct_sensor_monitoring` mart for real-time data

**Planned Enhancements**:
- Crop yield prediction visualization page
- Historical prediction accuracy tracking
- Multi-farm comparison view
- Weather forecast integration
- Mobile-responsive design

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
│   │   ├── extract_sensor_data.py         # Soil sensor data extraction
│   │   ├── extract_weather_data.py        # Weather data extraction
│   │   ├── postres_to_snowflake.py        # PostgreSQL to Snowflake ETL
│   │   ├── test_connection.py             # Connection testing
│   │   ├── train_crop_yield_model.py      # Weekly model training
│   │   └── predict_crop_yield.py          # Daily predictions
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
│   ├── config/
│   │   ├── config.py
│   │   └── config.yml                     # MLflow and Snowflake config
│   ├── data_loader/
│   │   └── snowflake_loader.py            # Snowflake data loader
│   ├── src/
│   │   ├── models/
│   │   │   ├── base_model.py
│   │   │   ├── crop_yield_predictor.py    # Main prediction model
│   │   │   ├── anomaly_detector.py
│   │   │   ├── irrigation_optimizer.py
│   │   │   └── soil_health_scorer.py
│   │   ├── evaluation/
│   │   ├── preprocessing/
│   │   ├── training/
│   │   │   └── trainer.py
│   │   └── utils/
│   ├── models/
│   │   └── crop_yield/
│   │       ├── model.pkl                  # Trained model artifact
│   │       └── encoders.pkl               # Label encoders
│   ├── notebooks/
│   │   ├── 01_crop_yield_model_training.ipynb
│   │   └── feature_importance.png
│   ├── scripts/
│   │   └── train_crop_yield.py
│   └── tests/
│
├── dashboard/
│   └── streamlit_app.py                   # Streamlit dashboard
│
└── assets/
    └── dashboard.png                      # Dashboard screenshot
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

### ✅ Phase 4: ML Models & Visualization (COMPLETE)
- [x] MLflow experiment tracking setup
- [x] Crop yield prediction model training (98.92% R²)
- [x] Weekly model retraining pipeline (`train_crop_yield_model` DAG)
- [x] Daily prediction generation (`predict_crop_yield` DAG)
- [x] Model registry with Production stage
- [x] Model versioning and artifact management
- [x] Predictions database table
- [x] Streamlit dashboard with real-time monitoring
- [x] Interactive sensor trend visualizations
- [x] Alert system for anomaly detection

### 🔄 Phase 5: Advanced Features (IN PROGRESS)
- [ ] Email/SMS alert notifications
- [ ] Additional dashboard pages (predictions, historical analysis)
- [ ] Weather forecast integration for predictive irrigation
- [ ] Model performance tracking over time
- [ ] A/B testing for model versions
- [ ] Multi-farm deployment capability
- [ ] Mobile app development
- [ ] Integration with farm equipment IoT devices

## Environment Variables

Create a `.env` file with the following:

```bash
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agrosense_db
POSTGRES_USER=agrosense
POSTGRES_PASSWORD=your_password_here

# API Keys
VISUAL_CROSSING_API_KEY=your_key_here
AGROMONITORING_API_KEY=your_key_here

# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=AGROSENSE_DB
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_SCHEMA=AGROSENSE_SCH
SNOWFLAKE_ROLE=ACCOUNTADMIN

# Airflow Configuration
AIRFLOW_UID=50000
AIRFLOW_PROJ_DIR=.

# MLflow Configuration
MLFLOW_TRACKING_URI=postgresql://mlflow:mlflow@postgres:5432/mlflow
MLFLOW_BACKEND_STORE_URI=postgresql://mlflow:mlflow@postgres:5432/mlflow
```

## Key Resources & Links

### Documentation
- **Apache Airflow**: https://airflow.apache.org/docs/
- **dbt Documentation**: https://docs.getdbt.com/
- **Snowflake Docs**: https://docs.snowflake.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **MLflow**: https://mlflow.org/docs/latest/index.html
- **Streamlit**: https://docs.streamlit.io/
- **scikit-learn**: https://scikit-learn.org/stable/documentation.html

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
git clone https://github.com/Abdul-Rahmann/agrosense.git
cd agrosense

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/airflow-requirements.txt
pip install -r requirements/dbt-requirements.txt
pip install -r requirements/mlflow-requirements.txt
```

#### 2. Configure Environment Variables
Create a `.env` file in the root directory with all required credentials (see Environment Variables section above).

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
docker-compose logs -f mlflow
```

#### 5. Run dbt Models
```bash
cd agrosense_dbt

# Load seed data
dbt seed

# Run all models
dbt run

# Test data quality
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

#### 6. Initialize Airflow Variables
Set up tracking variables for incremental data processing:

```bash
# Set initial tracking IDs for each pipeline
docker exec -it airflow_scheduler airflow variables set weather_last_processed_id 0
docker exec -it airflow_scheduler airflow variables set soil_last_processed_id 0
docker exec -it airflow_scheduler airflow variables set yield_predictions_last_processed_id 0
```

These variables help track the last processed records to avoid duplicate data loading.

#### 7. Enable Airflow DAGs
1. Access Airflow UI: http://localhost:8080
2. Enable the following DAGs:
   - `extract_sensor_data`
   - `extract_weather_data`
   - `load_postgres_to_snowflake`
   - `train_crop_yield_model`
   - `predict_crop_yield`

#### 8. Train Initial Model
```bash
# Manually trigger first training run
# Or wait for scheduled Sunday 2 AM UTC run
# Monitor in Airflow UI

# Check MLflow for experiment tracking
# Access MLflow UI: http://localhost:5000
```

#### 9. Launch Dashboard
```bash
cd dashboard
streamlit run streamlit_app.py

# Access dashboard: http://localhost:8501
```

### Monitoring & Operations

#### Airflow Monitoring
- **Airflow UI**: http://localhost:8080
- **DAG Runs**: Monitor execution status, logs, and task durations
- **Alerts**: Check for failed tasks and retry attempts

#### MLflow Monitoring
- **MLflow UI**: http://localhost:5000
- **Experiments**: View training runs and compare metrics
- **Model Registry**: Check model versions and stages

#### Data Quality
- **dbt Tests**: Run `dbt test` to validate data quality
- **dbt Docs**: View lineage and model documentation at http://localhost:8080 (after `dbt docs serve`)

#### Database Queries
```sql
-- Check latest sensor readings
SELECT * FROM agrosense.weather ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM agrosense.soil ORDER BY timestamp DESC LIMIT 10;

-- Check predictions
SELECT * FROM agrosense.crop_yield_predictions 
ORDER BY prediction_date DESC LIMIT 20;

-- Analyze prediction accuracy (when actual yields available)
SELECT 
    crop_type,
    AVG(predicted_yield_kg_ha) as avg_predicted,
    COUNT(*) as prediction_count
FROM agrosense.crop_yield_predictions
GROUP BY crop_type;
```

### API Client Usage

The `data_generator/` folder contains API client utilities for manual data collection:

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

## Success Metrics

### Data Pipeline Performance
- ✅ **Data Quality**: 99%+ data quality score
- ✅ **Latency**: <1 hour end-to-end pipeline latency
- ✅ **Scheduled Runs**: Daily execution since Sept 28, 2025 (50+ days)
- ✅ **Data Coverage**: Weather + Soil + Crop Yield datasets integrated
- ✅ **Reliability**: Automated retries and comprehensive error handling

### Machine Learning Performance
- ✅ **Model Accuracy**: 98.92% R² score on test data
- ✅ **Mean Prediction Error**: 8.77% APE (excellent for agricultural prediction)
- ✅ **Median Prediction Error**: 2.08% APE (very low median error)
- ✅ **Model Training**: Weekly automated retraining pipeline
- ✅ **Predictions**: Daily generation and storage
- ✅ **Experiment Tracking**: Full MLflow integration

### Dashboard & Visualization
- ✅ **Real-time Monitoring**: Live sensor data with <5 minute refresh
- ✅ **Alert Detection**: Automated anomaly detection and warnings
- ✅ **Data Visualization**: Interactive 7-day trend charts
- ✅ **Data Access**: CSV export capability for analysis

## Data Collection History

- **First Data Collection**: September 28, 2025
- **Continuous Operation**: 50+ days of automated daily runs
- **Success Rate**: >99% (multiple retry mechanisms ensure reliability)
- **Data Sources**: 
  - Weather data: Collected daily via Visual Crossing API
  - Soil sensor data: Collected daily via Agromonitoring API
  - Historical crop yield: Kaggle dataset seeded in dbt (static reference data)
- **ML Training**: Weekly retraining since October 2025
- **Predictions**: Daily predictions since November 2025

---

## Next Steps

### Immediate Priorities

1. **Dashboard Enhancements**
   - Add prediction visualization page showing crop yield forecasts
   - Historical prediction accuracy tracking
   - Scenario comparison view (optimal vs drought conditions)
   - Weather forecast integration

2. **Alerting System**
   - Implement email notifications for critical alerts
   - SMS integration for urgent irrigation recommendations
   - Slack/Discord webhooks for team notifications
   - Alert history and acknowledgment tracking

3. **Model Improvements**
   - Hyperparameter tuning using Optuna or GridSearchCV
   - Feature importance analysis and selection
   - Ensemble methods (combine multiple models)
   - Cross-validation across different regions
   - Seasonal pattern recognition
   - Weather forecast integration for predictive modeling

4. **Additional ML Models**
   - Deploy irrigation optimization model
   - Implement soil health scoring system
   - Plant disease prediction using image data
   - Pest outbreak prediction

### Future Enhancements

1. **Multi-Farm Support**
   - Multi-tenant architecture
   - Farm-specific model fine-tuning
   - Comparative analytics across farms
   - Best practice sharing platform

2. **Advanced Analytics**
   - Climate change impact analysis
   - Long-term yield trend forecasting
   - Economic optimization (ROI calculations)
   - Sustainability metrics tracking

3. **Integration & Automation**
   - Direct integration with farm equipment IoT
   - Automated irrigation system control
   - Mobile app for field workers
   - API for third-party integrations

4. **Research & Development**
   - Deep learning models (LSTMs for time series)
   - Computer vision for crop health assessment
   - Satellite imagery integration
   - Edge computing for real-time processing

---

## Acknowledgments

- **Data Sources**: Visual Crossing Weather API, Agromonitoring API, Kaggle
- **Technologies**: Apache Airflow, dbt, Snowflake, MLflow, Streamlit
- **Community**: Open-source contributors of all the amazing tools used in this project

---


**Built with ❤️ for sustainable agriculture and data-driven farming**