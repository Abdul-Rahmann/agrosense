# Smart Agriculture IoT Data Pipeline

## Project Overview

**Objective**: Build an end-to-end data pipeline for smart agriculture monitoring with IoT sensor data, machine learning predictions, and visualization dashboards.

**Business Value**: 
- Optimize crop yields through data-driven decisions
- Reduce water usage with smart irrigation
- Early detection of plant diseases/stress
- Automated farm monitoring and alerts

## Architecture

```
Farm IoT APIs → Airflow → PostgreSQL → Snowflake → dbt → ML Models → Dashboard
     ↓              ↓          ↓           ↓        ↓        ↓         ↓
   Weather      Extract/   Raw Data    Analytics  Feature   Predictions  Insights
   Soil Data    Transform   Storage    Warehouse  Engineering            & Alerts
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Orchestration** | Apache Airflow | Workflow management, DAG scheduling |
| **Database** | PostgreSQL | Raw data storage, operational data |
| **Data Warehouse** | Snowflake | Analytics, aggregated data |
| **Transformation** | dbt | Data modeling, feature engineering |
| **Containerization** | Docker | Environment consistency |
| **Database Connector** | psycopg | Python-PostgreSQL interface |
| **ML Framework** | scikit-learn, pandas | Predictive modeling |
| **Visualization** | Streamlit/Plotly | Dashboards and reporting |

## Data Sources

### Primary Data Types
1. **Environmental Sensors**
   - Soil moisture, temperature, pH
   - Air temperature, humidity
   - Solar radiation, rainfall
   
2. **Crop Monitoring**
   - Growth stage indicators
   - Leaf wetness, canopy temperature
   - Plant health metrics

3. **Farm Operations**
   - Irrigation events
   - Fertilizer applications
   - Pesticide treatments

### API Sources
- **OpenWeatherMap API**: Weather data by location
  - [Documentation](https://openweathermap.org/api)
  - [Free tier](https://openweathermap.org/price): 1,000 calls/day
  
- **Mock IoT Data Generator**: Custom simulated sensor data
  - Realistic agricultural patterns
  - Multiple farm locations and sensors
  
- **USDA APIs**: Soil and crop data (optional)
  - [USDA NASS API](https://quickstats.nass.usda.gov/api)

## Machine Learning Models

### 1. Crop Yield Prediction
- **Input Features**: Weather history, soil conditions, growth stage
- **Output**: Expected yield per hectare, harvest timing
- **Algorithm**: Random Forest Regression

### 2. Irrigation Optimization
- **Input Features**: Soil moisture, weather forecast, crop water requirements
- **Output**: Optimal irrigation schedule and water amounts
- **Algorithm**: Decision Tree + Time Series Forecasting

### 3. Disease Risk Assessment
- **Input Features**: Temperature, humidity, leaf wetness duration
- **Output**: Risk probability for common plant diseases
- **Algorithm**: Classification (Logistic Regression/SVM)

### 4. Growth Stage Classification
- **Input Features**: Accumulated growing degree days, time series of environmental conditions
- **Output**: Current growth stage (germination, vegetative, flowering, etc.)
- **Algorithm**: Multi-class Classification

## Database Schema Design

### PostgreSQL (Raw Data Layer)

```sql
-- Sensor readings table
CREATE TABLE sensor_readings (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50),
    farm_id VARCHAR(50),
    field_id VARCHAR(50),
    timestamp TIMESTAMP,
    sensor_type VARCHAR(50),
    measurement VARCHAR(50),
    value DECIMAL(10,3),
    unit VARCHAR(20),
    quality_flag INTEGER
);

-- Weather data table
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    location_id VARCHAR(50),
    timestamp TIMESTAMP,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    rainfall DECIMAL(7,2),
    wind_speed DECIMAL(5,2),
    solar_radiation DECIMAL(8,2),
    pressure DECIMAL(7,2)
);

-- Farm operations table
CREATE TABLE farm_operations (
    id SERIAL PRIMARY KEY,
    farm_id VARCHAR(50),
    field_id VARCHAR(50),
    timestamp TIMESTAMP,
    operation_type VARCHAR(50),
    amount DECIMAL(10,3),
    unit VARCHAR(20),
    notes TEXT
);

-- Farms metadata
CREATE TABLE farms (
    farm_id VARCHAR(50) PRIMARY KEY,
    farm_name VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    total_area DECIMAL(10,2),
    crop_type VARCHAR(50),
    planting_date DATE
);
```

### Snowflake (Analytics Layer)
- **RAW**: Direct copies from PostgreSQL
- **STAGING**: Cleaned and validated data
- **MARTS**: Business logic and aggregations
- **ML**: Features and model results

## Project Structure

```
farm-iot-pipeline/
├── README.md
├── docker-compose.yml
├── .env.example
├── requirements.txt
│
├── airflow/
│   ├── dags/
│   │   ├── farm_data_ingestion.py
│   │   ├── ml_training_pipeline.py
│   │   └── data_quality_checks.py
│   ├── plugins/
│   └── config/
│
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── tests/
│   ├── macros/
│   └── dbt_project.yml
│
├── ml_models/
│   ├── src/
│   │   ├── data_preprocessing.py
│   │   ├── model_training.py
│   │   └── predictions.py
│   ├── models/
│   └── notebooks/
│
├── data_generator/
│   ├── mock_iot_api.py
│   ├── sensor_simulator.py
│   └── weather_api_client.py
│
├── dashboard/
│   ├── streamlit_app.py
│   ├── components/
│   └── static/
│
├── sql/
│   ├── postgres_setup.sql
│   └── snowflake_setup.sql
│
└── docs/
    ├── api_documentation.md
    ├── model_documentation.md
    └── deployment_guide.md
```

## Implementation Phases

### Phase 1: Foundation Setup (Week 1)
- [ ] Docker environment with all services
- [ ] PostgreSQL database setup
- [ ] Basic Airflow installation
- [ ] Mock IoT data generator
- [ ] Weather API integration

### Phase 2: Data Pipeline (Week 2)
- [ ] Airflow DAGs for data extraction
- [ ] PostgreSQL to Snowflake pipeline
- [ ] Basic dbt models
- [ ] Data quality checks

### Phase 3: ML Pipeline (Week 3)
- [ ] Feature engineering in dbt
- [ ] ML model training pipeline
- [ ] Model deployment in Airflow
- [ ] Prediction scheduling

### Phase 4: Visualization & Monitoring (Week 4)
- [ ] Streamlit dashboard
- [ ] Real-time monitoring
- [ ] Model performance tracking
- [ ] Alert system

## Key Resources & Links

### Documentation
- **Apache Airflow**: https://airflow.apache.org/docs/
- **dbt Documentation**: https://docs.getdbt.com/
- **Snowflake Docs**: https://docs.snowflake.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **PostgreSQL**: https://www.postgresql.org/docs/

### APIs & Data Sources
- **OpenWeatherMap**: https://openweathermap.org/api
- **USDA NASS**: https://quickstats.nass.usda.gov/api
- **Plant Disease APIs**: Various agricultural research APIs

### ML Resources
- **Agricultural ML Papers**: Google Scholar "precision agriculture machine learning"
- **Crop Yield Prediction**: Research papers on environmental factors
- **Irrigation Optimization**: Smart irrigation system algorithms

## Getting Started

1. **Clone and setup project structure**
2. **Configure environment variables**
3. **Start with Docker Compose**
4. **Create mock data generator**
5. **Build first Airflow DAG**
6. **Implement basic dbt models**

## Success Metrics

- **Data Pipeline**: 99%+ data quality, <1 hour latency
- **ML Models**: >85% accuracy for yield prediction, 20%+ water savings
- **Dashboard**: Real-time updates, actionable insights
- **System**: 99% uptime, automated error handling

---

## Next Steps
Ready to start implementation? Begin with the project setup and Docker environment configuration.