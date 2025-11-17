"""
Data loading module for Snowflake.
Handles Snowflake connection and data loading.
"""

import pandas as pd, os, yaml, logging
from snowflake.connector import connect
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """Loads data from Snowflake for model development"""

    def __init__(self):
        load_dotenv()
        # with open(config_path, 'r') as f:
        #     self.config = yaml.safe_load(f)

    def load_from_snowflake(self, query):
        """Loads data from Snowflake"""
        logger.info("Loading data from Snowflake...")

        # sf_config = self.config['snowflake']
        conn = connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            database=os.getenv('SNOWFLAKE_DB'),
            warehouse=os.getenv('SNOWFLAKE_WH'),
            role=os.getenv('SNOWFLAKE_ROLE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA')
        )
        logger.info("Loading data from Snowflake...")
        # query = sf_config['query']
        df = pd.read_sql(query, conn)
        conn.close()

        logger.info(f"Data loaded successfully. shape: {df.shape}")
        return df

    def load_from_csv(self, filepath):
        """Load data from CSV file (for testing)."""
        logger.info(f"Loading data from {filepath}...")
        df = pd.read_csv(filepath)
        logger.info(f"Data loaded successfully. Shape: {df.shape}")
        return df
