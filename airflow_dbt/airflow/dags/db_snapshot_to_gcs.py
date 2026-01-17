import io
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
GCP_CONN_ID = 'google_cloud_default'
POSTGRES_CONN_ID = 'postgres_default'
BUCKET_NAME = 'olist-ecommerce-bucket'
PROJECT_ID = 'e-commerce-484010'
DATASET_NAME = 'bronze'
PUBLICATION_NAME = 'dbz_publication'
SLOT_NAME = 'snap_shot'

# --- HELPER FUNCTIONS (Giữ nguyên) ---
def create_publication_if_not_exists(cursor, pub_name):
    try:
        cursor.execute(f"CREATE PUBLICATION {pub_name} FOR ALL TABLES;")
        logging.info(f"Created Publication: {pub_name}")
    except psycopg2.errors.DuplicateObject:
        cursor.connection.rollback()
        logging.info(f"Publication {pub_name} already exists. Skipping.")

def create_slot_and_get_snapshot(cursor, slot_name):
    create_sql = f"CREATE_REPLICATION_SLOT {slot_name} LOGICAL pgoutput EXPORT_SNAPSHOT;"
    try:
        cursor.execute(create_sql)
        result = cursor.fetchone()
        return result[2]
    except psycopg2.errors.DuplicateObject:
        cursor.connection.rollback()
        logging.warning(f"Slot '{slot_name}' exists. Recreating...")
        cursor.execute(f"SELECT pg_drop_replication_slot('{slot_name}');")
        cursor.execute(create_sql)
        return cursor.fetchone()[2]

def get_public_tables(cursor, snapshot_id):
    cursor.execute("BEGIN ISOLATION LEVEL REPEATABLE READ;")
    cursor.execute(f"SET TRANSACTION SNAPSHOT '{snapshot_id}';")
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    return [row[0] for row in cursor.fetchall()]

def stream_table_to_gcs(pg_cursor, table_name, bucket_name, gcs_hook):
    logging.info(f"Streaming table {table_name}...")
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb+', delete=False) as temp_file:
            temp_file_path = temp_file.name
            sql = f"COPY (SELECT * FROM public.\"{table_name}\") TO STDOUT WITH CSV HEADER"
            pg_cursor.copy_expert(sql, temp_file)
        
        gcs_hook.upload(
            bucket_name=bucket_name,
            object_name=f"{table_name}/snapshot/{table_name}.csv",
            filename=temp_file_path,
            mime_type='text/csv'
        )
    finally:
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
        
        conn_repl = psycopg2.connect(
            host=conn_args.host, user=conn_args.login, password=conn_args.password,
            port=conn_args.port, dbname=conn_args.schema,
            connection_factory=LogicalReplicationConnection
        )
        cur_repl = conn_repl.cursor()

        try:
            create_publication_if_not_exists(cur_repl, PUBLICATION_NAME)
            snapshot_id = create_slot_and_get_snapshot(cur_repl, SLOT_NAME)

            conn_worker = pg_hook.get_conn()
            cur_worker = conn_worker.cursor()
            
            try:
                tables = get_public_tables(cur_worker, snapshot_id)
                for table in tables:
                    stream_table_to_gcs(cur_worker, table, BUCKET_NAME, gcs_hook)
                conn_worker.commit()
                return tables
            finally:
                cur_worker.close()
                conn_worker.close()
        finally:
            cur_repl.close()
            conn_repl.close()

    @task 
    def ensure_dataset():
        # MOVE CLIENT INSIDE TASK
        bq_hook = BigQueryHook(gcp_conn_id=GCP_CONN_ID)
        client = bq_hook.get_client(project_id=PROJECT_ID)
        
        dataset_id = f"{PROJECT_ID}.{DATASET_NAME}"
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US" 
        client.create_dataset(dataset, exists_ok=True)
        logging.info(f"Ensured dataset '{dataset_id}' exists.")

    @task
    def create_external_snapshot_tables_task(table_name: str):
        # MOVE CLIENT INSIDE TASK & INPUT IS STRING (NOT LIST)
        bq_hook = BigQueryHook(gcp_conn_id=GCP_CONN_ID)
        client = bq_hook.get_client(project_id=PROJECT_ID)

        ext_cfg_csv = bigquery.ExternalConfig("CSV")
        ext_cfg_csv.source_uris = [f"gs://{BUCKET_NAME}/{table_name}/snapshot/{table_name}.csv"]
        ext_cfg_csv.autodetect = True
        ext_cfg_csv.options.skip_leading_rows = 1
        
        table_ref = bigquery.Table(f"{PROJECT_ID}.{DATASET_NAME}.{table_name}_snapshot_external")
        table_ref.external_data_configuration = ext_cfg_csv
        client.create_table(table_ref, exists_ok=True)
        logging.info(f"Created Snapshot Table for {table_name}")

    @task
    def create_external_cdc_tables_task(table_name: str):
        # MOVE CLIENT INSIDE TASK & INPUT IS STRING (NOT LIST)
        bq_hook = BigQueryHook(gcp_conn_id=GCP_CONN_ID)
        client = bq_hook.get_client(project_id=PROJECT_ID)

        ext_cfg_json = bigquery.ExternalConfig("NEWLINE_DELIMITED_JSON")
        ext_cfg_json.source_uris = [f"gs://{BUCKET_NAME}/{table_name}/cdc/*"]
        ext_cfg_json.autodetect = True
        ext_cfg_json.ignore_unknown_values = True
        
        table_ref_cdc = bigquery.Table(f"{PROJECT_ID}.{DATASET_NAME}.{table_name}_cdc_external")
        table_ref_cdc.external_data_configuration = ext_cfg_json
        client.create_table(table_ref_cdc, exists_ok=True)
        logging.info(f"Created CDC Table for {table_name}")

    # --- FLOW ---
    
    # 1. Chạy Snapshot và lấy danh sách bảng
    tables = db_snapshot_to_gcs_task()
    
    # 2. Tạo Dataset (Chạy 1 lần)
    init_dataset = ensure_dataset()
    
    # 3. Tạo bảng Snapshot (Parallel Mapping cho từng bảng)
    # Lưu ý: snapshot task phải chạy xong dataset task
    tables >> init_dataset
    
    snapshot_creation = create_external_snapshot_tables_task.expand(table_name=tables)
    init_dataset >> snapshot_creation

    # 4. Sensor: Đợi file CDC cho từng bảng
    wait_for_cdc = GCSObjectsWithPrefixExistenceSensor.partial(
        task_id='wait_for_cdc_files',
        bucket=BUCKET_NAME,
        google_cloud_conn_id=GCP_CONN_ID,
        mode='reschedule',
        poke_interval=180,
        timeout=6000,
        soft_fail=True
    ).expand(
        prefix=tables.map(lambda t: f"{t}/cdc/")
    )

    # 5. Tạo bảng CDC (Chạy sau khi Sensor hoàn tất)
    # Ta map lại function create table với danh sách tables gốc
    cdc_creation = create_external_cdc_tables_task.expand(table_name=tables)
    
    # Nối dây: Sensor xong -> Mới tạo bảng
    # Lưu ý: Trong Airflow cơ bản, việc nối 2 mapped task như này sẽ tạo ra "Barrier"
    # (Tức là đợi TOÀN BỘ sensor xong mới chạy TOÀN BỘ create task). 
    # Nhưng nó an toàn và đúng logic bạn cần.
    wait_for_cdc >> cdc_creation

dag_instance = postgres_to_bigquery_pipeline_refactored()