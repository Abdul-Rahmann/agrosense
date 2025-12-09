"""
AgroSense Dashboard v2.7
Cleaned & Optimized for Production
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.connector import connect
import os
import dotenv
from datetime import datetime, timedelta

# Load environment variables
dotenv.load_dotenv()

# -----------------------------------------------------------------------------
# CONFIGURATION & SETUP
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AgroSense AI - Smart Farm Monitor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UI polish
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stGraphContainer"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 20px;
    }
    .main-header {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/tractor.png", width=80)
    st.title("AgroSense AI")

    st.markdown("### 📅 Trends Filter")
    today = datetime.now()
    default_start = today - timedelta(days=7)

    date_range = st.date_input(
        "Select Range for Charts:",
        value=(default_start, today),
        max_value=today
    )

    st.caption("Filters apply to the trend charts below.")

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# -----------------------------------------------------------------------------
# DATA LOADING
# -----------------------------------------------------------------------------
@st.cache_resource
def get_snowflake_connection():
    return connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        database=os.getenv('SNOWFLAKE_DB', 'AGROSENSE_DB'),
        warehouse=os.getenv('SNOWFLAKE_WH', 'COMPUTE_WH'),
        role=os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN'),
        schema=os.getenv('SNOWFLAKE_SCHEMA', 'AGROSENSE_SCH')
    )

@st.cache_data(ttl=300)
def load_sensor_data(start_date, end_date):
    """Fetches sensor readings specifically for the selected date range."""
    conn = get_snowflake_connection()

    # SQL Pushdown: Filter in Snowflake to handle large datasets efficiently
    query = f"""
    SELECT 
        READING_TIMESTAMP, 
        AIR_TEMP, 
        HUMIDITY, 
        SOIL_MOISTURE, 
        PH_SURFACE, 
        TEMP_FLAG, 
        MOISTURE_FLAG, 
        IRRIGATION_ALERT
    FROM AGROSENSE_DB.AGROSENSE_SCH.FCT_SENSOR_MONITORING
    WHERE TO_DATE(READING_TIMESTAMP) >= '{start_date}'
      AND TO_DATE(READING_TIMESTAMP) <= '{end_date}'
    ORDER BY READING_TIMESTAMP DESC 
    """

    try:
        df = pd.read_sql(query, conn)
        df['READING_TIMESTAMP'] = pd.to_datetime(df['READING_TIMESTAMP'])
        return df
    except Exception as e:
        st.error(f"Error loading sensor data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_predictions():
    """Fetches the latest ML yield predictions."""
    conn = get_snowflake_connection()
    query = """
    SELECT * FROM AGROSENSE_DB.AGROSENSE_SCH.CROP_YIELD_PREDICTIONS
    WHERE "prediction_date" = (SELECT MAX("prediction_date") FROM AGROSENSE_DB.AGROSENSE_SCH.CROP_YIELD_PREDICTIONS)
    """
    try:
        df = pd.read_sql(query, conn)
        df['prediction_date'] = pd.to_datetime(df['prediction_date'])
        return df
    except Exception as e:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# MAIN LOGIC
# -----------------------------------------------------------------------------

# Handle Date Range Logic
if len(date_range) == 2:
    start_date, end_date = date_range
    df_sensors = load_sensor_data(start_date, end_date)
else:
    st.info("Please select a valid start and end date.")
    df_sensors = pd.DataFrame()

# -----------------------------------------------------------------------------
# HELPER: Chart Generator
# -----------------------------------------------------------------------------
def plot_metric(df, y_col, color, title, unit):
    fig = px.line(
        df,
        x='READING_TIMESTAMP',
        y=y_col,
        title=f"<b>{title}</b>",
        color_discrete_sequence=[color]
    )
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="",
        yaxis_title=unit,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    fig.update_traces(line=dict(width=2.5))
    fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
    return fig

# -----------------------------------------------------------------------------
# TABS
# -----------------------------------------------------------------------------
tab_dashboard, tab_predict = st.tabs(["🚜 Main Dashboard", "🔮 Yield Forecasts"])

# =============================================================================
# TAB 1: MAIN DASHBOARD
# =============================================================================
with tab_dashboard:
    if not df_sensors.empty:
        latest = df_sensors.iloc[0]

        # --- LIVE STATUS ---
        st.markdown('<div class="main-header">📡 Live Status (Latest in Range)</div>', unsafe_allow_html=True)

        alerts = []
        if latest['TEMP_FLAG'] == 'ANOMALY': alerts.append(f"High Temp ({latest['AIR_TEMP']}°C)")
        if latest['MOISTURE_FLAG'] == 'ANOMALY': alerts.append(f"Abnormal Moisture ({latest['SOIL_MOISTURE']}%)")
        if latest['IRRIGATION_ALERT'] != 'NORMAL': alerts.append(f"Irrigation Needed")

        if alerts:
            st.warning(f"⚠️ **Active Alerts:** {', '.join(alerts)}")

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Air Temp", f"{latest['AIR_TEMP']:.1f}°C")
        kpi2.metric("Humidity", f"{latest['HUMIDITY']:.0f}%")
        kpi3.metric("Soil Moisture", f"{latest['SOIL_MOISTURE']:.1f}%")
        kpi4.metric("Soil pH", f"{latest['PH_SURFACE']:.1f}")

        st.divider()

        # --- TRENDS ---
        st.markdown(f'<div class="main-header">📈 Historical Trends ({start_date} - {end_date})</div>', unsafe_allow_html=True)

        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)

        with row1_col1:
            st.plotly_chart(plot_metric(df_sensors, 'AIR_TEMP', '#FF6B6B', "🌡️ Air Temperature", "°C"), use_container_width=True)
        with row1_col2:
            st.plotly_chart(plot_metric(df_sensors, 'HUMIDITY', '#4ECDC4', "💧 Humidity", "%"), use_container_width=True)
        with row2_col1:
            fig_soil = plot_metric(df_sensors, 'SOIL_MOISTURE', '#45B7D1', "🌱 Soil Moisture", "%")
            fig_soil.add_hline(y=20, line_dash="dot", line_color="red", annotation_text="Critical Low")
            st.plotly_chart(fig_soil, use_container_width=True)
        with row2_col2:
            st.plotly_chart(plot_metric(df_sensors, 'PH_SURFACE', '#96CEB4', "⚗️ Soil pH", "pH"), use_container_width=True)

    elif len(date_range) == 2:
        st.warning(f"No data found in database for range: {start_date} to {end_date}")

# =============================================================================
# TAB 2: YIELD FORECASTS
# =============================================================================
with tab_predict:
    st.header("🔮 AI Crop Yield Prediction")
    df_pred = load_predictions()

    if not df_pred.empty:
        # Note: Handling lowercase columns from Postgres/Snowflake sync
        avg_yield = df_pred[df_pred['scenario'] == 'baseline']['predicted_yield_kg_ha'].mean()
        max_yield = df_pred['predicted_yield_kg_ha'].max()
        pred_date = df_pred['prediction_date'].iloc[0].strftime('%Y-%m-%d')

        m1, m2, m3 = st.columns(3)
        m1.metric("Baseline Forecast (Avg)", f"{avg_yield:,.0f} kg/ha")
        m2.metric("Max Potential Yield", f"{max_yield:,.0f} kg/ha", delta="Optimistic Scenario")
        m3.metric("Prediction Date", pred_date)

        st.markdown("---")

        st.subheader("🌪️ Scenario Analysis")
        fig_pred = px.bar(
            df_pred,
            x="crop_type",
            y="predicted_yield_kg_ha",
            color="scenario",
            barmode="group",
            text_auto='.2s',
            title="Yield Forecast by Crop & Scenario",
            color_discrete_map={
                'pessimistic': '#FF8080',
                'baseline': '#A0A0A0',
                'optimistic': '#90EE90',
                'conservative': '#87CEEB'
            }
        )
        st.plotly_chart(fig_pred, use_container_width=True)
    else:
        st.info("⚠️ No predictions found.")