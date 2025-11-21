"""
AgroSense Dashboard - Simple Version
Single file, just works
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from snowflake.connector import connect
import os

import dotenv

dotenv.load_dotenv()

# Page config
st.set_page_config(
    page_title="AgroSense - Live Farm Monitor",
    page_icon="🌱",
    layout="wide"
)


@st.cache_resource
def get_snowflake_connection():
    return connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        database=os.getenv('SNOWFLAKE_DB'),
        warehouse=os.getenv('SNOWFLAKE_WH'),
        role=os.getenv('SNOWFLAKE_ROLE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA')
    )


@st.cache_data(ttl=300)
def load_sensor_data():
    conn = get_snowflake_connection()
    query = """
            SELECT READING_TIMESTAMP, \
                   AIR_TEMP, \
                   HUMIDITY, \
                   SOIL_MOISTURE, \
                   PH_SURFACE, \
                   TEMP_FLAG, \
                   MOISTURE_FLAG, \
                   IRRIGATION_ALERT
            FROM AGROSENSE_DB.AGROSENSE_SCH.FCT_SENSOR_MONITORING
            ORDER BY READING_TIMESTAMP DESC LIMIT 1000 \
            """
    df = pd.read_sql(query, conn)
    df['READING_TIMESTAMP'] = pd.to_datetime(df['READING_TIMESTAMP'])
    print(f"DATA{df}")
    return df


st.title("🌱 Live Farm Monitor")
st.markdown("Real-time sensor monitoring and alerts")

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

st.markdown("---")

try:
    df = load_sensor_data()

    latest = df.iloc[0]
    print(f"DATA{df}")

    alerts = df[
        (df['TEMP_FLAG'] == 'ANOMALY') |
        (df['MOISTURE_FLAG'] == 'ANOMALY') |
        (df['IRRIGATION_ALERT'] != 'NORMAL')
        ]

    # ALERTS
    if len(alerts) > 0:
        st.error(f"⚠️ {len(alerts)} Active Alert(s)")

        # Show alert details
        for _, row in alerts.head(5).iterrows():
            if row['IRRIGATION_ALERT'] == 'LOW_MOISTURE_ALERT':
                st.warning(f"💧 Low soil moisture: {row['SOIL_MOISTURE']:.1f}% - Consider irrigation")
            elif row['IRRIGATION_ALERT'] == 'HIGH_MOISTURE_ALERT':
                st.info(f"🌊 High soil moisture: {row['SOIL_MOISTURE']:.1f}% - Reduce irrigation")
            if row['TEMP_FLAG'] == 'ANOMALY':
                st.warning(f"🌡️ Temperature anomaly: {row['AIR_TEMP']:.1f}°C")
    else:
        st.success("✅ No active alerts - All systems normal")

    st.markdown("---")

    # CURRENT METRICS
    st.subheader("📊 Current Conditions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🌡️ Temperature", f"{latest['AIR_TEMP']:.1f}°C")

    with col2:
        st.metric("💧 Humidity", f"{latest['HUMIDITY']:.1f}%")

    with col3:
        moisture_icon = "⚠️" if latest['SOIL_MOISTURE'] < 20 else "💧"
        st.metric(f"{moisture_icon} Soil Moisture", f"{latest['SOIL_MOISTURE']:.1f}%")

    with col4:
        st.metric("⚗️ Soil pH", f"{latest['PH_SURFACE']:.1f}")

    st.caption(f"Last updated: {latest['READING_TIMESTAMP']}")

    st.markdown("---")

    # TRENDS
    st.subheader("📈 7-Day Trends")

    # Filter last 7 days
    last_7_days = df[df['READING_TIMESTAMP'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]

    if len(last_7_days) > 0:
        # Create charts
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Temperature (°C)', 'Humidity (%)', 'Soil Moisture (%)', 'pH')
        )

        # Temperature
        fig.add_trace(
            go.Scatter(x=last_7_days['READING_TIMESTAMP'], y=last_7_days['AIR_TEMP'],
                       name='Temp', line=dict(color='#FF6B6B', width=2)),
            row=1, col=1
        )

        # Humidity
        fig.add_trace(
            go.Scatter(x=last_7_days['READING_TIMESTAMP'], y=last_7_days['HUMIDITY'],
                       name='Humidity', line=dict(color='#4ECDC4', width=2)),
            row=1, col=2
        )

        # Soil Moisture
        fig.add_trace(
            go.Scatter(x=last_7_days['READING_TIMESTAMP'], y=last_7_days['SOIL_MOISTURE'],
                       name='Moisture', line=dict(color='#45B7D1', width=2)),
            row=2, col=1
        )

        # pH
        fig.add_trace(
            go.Scatter(x=last_7_days['READING_TIMESTAMP'], y=last_7_days['PH_SURFACE'],
                       name='pH', line=dict(color='#96CEB4', width=2)),
            row=2, col=2
        )

        fig.update_layout(height=600, showlegend=False, template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # RAW DATA
    with st.expander("📋 Raw Data (Last 100 readings)"):
        st.dataframe(
            df.head(100)[[
                'READING_TIMESTAMP', 'AIR_TEMP', 'HUMIDITY',
                'SOIL_MOISTURE', 'PH_SURFACE', 'IRRIGATION_ALERT'
            ]],
            use_container_width=True
        )

        # Download
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            f"sensor_data_{pd.Timestamp.now():%Y%m%d}.csv",
            "text/csv"
        )

except Exception as e:
    st.error(f"Error: {e}")
    st.exception(e)