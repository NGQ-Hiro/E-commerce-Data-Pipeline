import os
import logging
import psycopg2
import tempfile
from psycopg2.extras import LogicalReplicationConnection
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.sensors.gcs import GCSObjectsWithPrefixExistenceSensor
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from google.cloud import bigquery

# --- CONFIGURATION ---
GCP_CONN_ID = os.getenv('GCP_CONN_ID', 'google_cloud_default')
POSTGRES_CONN_ID = os.getenv('POSTGRES_CONN_ID', 'postgres_default')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'olist-ecommerce-bucket')
PROJECT_ID = os.getenv('PROJECT_ID', 'e-commerce-484010')
BRONZE = os.getenv('BRONZE', 'bronze')
PUBLICATION_NAME = os.getenv('PUBLICATION_NAME', 'dbz_publication')
SLOT_NAME = os.getenv('SLOT_NAME', 'snap_shot')

@dag(schedule=None, catchup=False)
def test():
    @task
    def create_external_snapshot_tables_task():
        from utils.schema import get_schema, SCHEMAS
        
        bq_hook = BigQueryHook(gcp_conn_id=GCP_CONN_ID)
        client = bq_hook.get_client(project_id=PROJECT_ID)

        # Create external tables for all schemas
        for table_name in SCHEMAS.keys():
            schema = get_schema(table_name=table_name)
            
            # Config format external table
            ext_cfg_csv = bigquery.ExternalConfig("CSV")
            ext_cfg_csv.source_uris = [f"gs://{BUCKET_NAME}/{table_name}/snapshot/{table_name}.csv"]
            ext_cfg_csv.schema = schema
            ext_cfg_csv.options.skip_leading_rows = 1
            ext_cfg_csv.options.field_delimiter = ','
            ext_cfg_csv.options.quote_character = '"'
            ext_cfg_csv.options.allow_quoted_newlines = True
            
            table_ref = bigquery.Table(f"{PROJECT_ID}.{BRONZE}.{table_name}_snapshot_external")
            table_ref.external_data_configuration = ext_cfg_csv
            client.create_table(table_ref, exists_ok=True)
            logging.info(f"✅ Created Snapshot Table for {table_name}")

    create_external_snapshot_tables_task()

test()
