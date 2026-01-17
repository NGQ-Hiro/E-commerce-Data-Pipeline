import io
import os
import logging
import psycopg2
import tempfile
from psycopg2.extras import LogicalReplicationConnection
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator

# --- CONFIGURATION ---
GCP_CONN_ID = 'google_cloud_default'
POSTGRES_CONN_ID = 'postgres_default'
BUCKET_NAME = 'olist-ecommerce-bucket'
PROJECT_ID = 'e-commerce-484010'
DATASET_NAME = 'bronze'
PUBLICATION_NAME = 'dbz_publication'
SLOT_NAME = 'snap_shot'

# --- HELPER FUNCTIONS (Tách logic ra ngoài) ---

def create_publication_if_not_exists(cursor, pub_name):
    """Tạo Publication nếu chưa tồn tại"""
    try:
        cursor.execute(f"CREATE PUBLICATION {pub_name} FOR ALL TABLES;")
        logging.info(f"Created Publication: {pub_name}")
    except psycopg2.errors.DuplicateObject:
        cursor.connection.rollback()
        logging.info(f"Publication {pub_name} already exists. Skipping.")

def create_slot_and_get_snapshot(cursor, slot_name):
    """Tạo Replication Slot và trả về Snapshot ID"""
    try:
        cursor.execute(
            f"CREATE_REPLICATION_SLOT {slot_name} LOGICAL pgoutput EXPORT_SNAPSHOT;"
        )
        result = cursor.fetchone()
        snapshot_id = result[2]
        logging.info(f"Created Slot '{slot_name}' | Snapshot ID: {snapshot_id}")
        return snapshot_id
    except psycopg2.errors.DuplicateObject:
        cursor.connection.rollback()
        raise ValueError(f"Slot '{slot_name}' already exists! Please drop it first.")

def get_public_tables(cursor, snapshot_id):
    """Lấy danh sách bảng trong schema public tại thời điểm Snapshot"""
    # Set transaction về quá khứ
    cursor.execute("BEGIN ISOLATION LEVEL REPEATABLE READ;")
    cursor.execute(f"SET TRANSACTION SNAPSHOT '{snapshot_id}';")
    
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    return [row[0] for row in cursor.fetchall()]

def stream_table_to_gcs(pg_cursor, table_name, bucket_name, gcs_hook):
    """Thực hiện Dump 1 bảng xuống file tạm và upload lên GCS"""
    logging.info(f"Streaming table {table_name}...")
    temp_file_path = None
    try:
        # 1. Write to Disk
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_file_path = temp_file.name
            sql = f"COPY (SELECT * FROM public.\"{table_name}\") TO STDOUT WITH CSV HEADER"
            pg_cursor.copy_expert(sql, temp_file)
        logging.info(f"Snapshot {table_name} to {temp_file_path}")
        
        # 2. Upload to GCS
        gcs_hook.upload(
            bucket_name=bucket_name,
            object_name=f"{table_name}/snapshot/{table_name}.csv",
            filename=temp_file_path,
            mime_type='text/csv'
        )
        logging.info(f"Uploaded {table_name} successfully.")
        
    finally:
        # 3. Clean Disk
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# --- MAIN DAG ---

@dag(schedule=None, catchup=False)
def postgres_to_bigquery_pipeline_refactored():

    @task
    def db_snapshot_to_gcs_task() -> list:
        # 1. Setup Connections
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        conn_args = pg_hook.get_connection(POSTGRES_CONN_ID)
        gcs_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        
        # Connect Replication (Connection Cha for snapshot)
        conn_repl = psycopg2.connect(
            host=conn_args.host, user=conn_args.login, password=conn_args.password,
            port=conn_args.port, dbname=conn_args.schema,
            connection_factory=LogicalReplicationConnection
        )
        cur_repl = conn_repl.cursor()

        try:
            # 2. Setup Logic (Gọi Helper Functions)
            create_publication_if_not_exists(cur_repl, PUBLICATION_NAME)
            snapshot_id = create_slot_and_get_snapshot(cur_repl, SLOT_NAME)

            # 3. Dump Data Logic
            # Mở connection worker
            conn_worker = pg_hook.get_conn()
            cur_worker = conn_worker.cursor()
            
            try:
                # Lấy danh sách bảng (đã được set snapshot bên trong hàm)
                tables = get_public_tables(cur_worker, snapshot_id)
                
                # Loop qua từng bảng để dump
                for table in tables:
                    stream_table_to_gcs(cur_worker, table, BUCKET_NAME, gcs_hook)
                
                conn_worker.commit()
                return tables

            finally:
                cur_worker.close()
                conn_worker.close()

        finally:
            # 4. Cleanup Replication (Giữ Slot, đóng kết nối)
            cur_repl.close()
            conn_repl.close()

    @task
    def create_external_tables_task(tables: list):
        # Code tạo bảng BigQuery giữ nguyên
        from google.cloud import bigquery
        from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
        bq_hook = BigQueryHook(gcp_conn_id=GCP_CONN_ID)
        client = bq_hook.get_client(project_id=PROJECT_ID)

        for table_name in tables:
            # Create Snapshot Table
            ext_cfg_csv = bigquery.ExternalConfig("CSV")
            ext_cfg_csv.source_uris = [f"gs://{BUCKET_NAME}/{table_name}/snapshot/{table_name}.csv"]
            ext_cfg_csv.autodetect = True
            ext_cfg_csv.options.skip_leading_rows = 1
            table_ref = bigquery.Table(f"{PROJECT_ID}.{DATASET_NAME}.{table_name}_snapshot_external")
            table_ref.external_data_configuration = ext_cfg_csv
            client.create_table(table_ref, exists_ok=True)

            # Create CDC Table
            ext_cfg_json = bigquery.ExternalConfig("NEWLINE_DELIMITED_JSON")
            ext_cfg_json.source_uris = [f"gs://{BUCKET_NAME}/{table_name}/cdc/*"]
            ext_cfg_json.autodetect = True
            ext_cfg_json.ignore_unknown_values = True
            table_ref_cdc = bigquery.Table(f"{PROJECT_ID}.{DATASET_NAME}.{table_name}_cdc_external")
            table_ref_cdc.external_data_configuration = ext_cfg_json
            client.create_table(table_ref_cdc, exists_ok=True)

    # --- FLOW ---
    table_list = db_snapshot_to_gcs_task()
    create_external_tables_task(table_list)

dag_instance = postgres_to_bigquery_pipeline_refactored()