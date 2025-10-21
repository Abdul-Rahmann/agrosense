FROM ghcr.io/mlflow/mlflow:v2.22.2
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["mlflow", "server", "--backend-store-uri", "postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/mlflow_db", "--default-artifact-root", "/mlflow/artifacts", "--host", "0.0.0.0", "--port", "5000"]
