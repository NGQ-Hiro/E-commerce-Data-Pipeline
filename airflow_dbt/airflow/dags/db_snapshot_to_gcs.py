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

# --- HELPER FUNCTIONS ---
def create_publication_if_not_exists(cursor, pub_name):
    try:
        cursor.execute(f"CREATE PUBLICATION {pub_name} FOR ALL TABLES;")
        logging.info(f"Created Publication: {pub_name}")
    except psycopg2.errors.DuplicateObject:
        cursor.connection.rollback()
        logging.info(f"Publication {pub_name} already exists. Skipping.")

def create_or_recreate_replication_slot(cursor, slot_name):
    create_sql = f"CREATE_REPLICATION_SLOT {slot_name} LOGICAL pgoutput EXPORT_SNAPSHOT;"
    try:
        cursor.execute(create_sql)
        result = cursor.fetchone()
        # slot_name lsn(wal) snapshot_id
        return result[2]
    except psycopg2.errors.DuplicateObject:
        cursor.connection.rollback()
        logging.warning(f"Slot '{slot_name}' exists. Recreating...")
        cursor.execute(f"SELECT pg_drop_replication_slot('{slot_name}');")
        cursor.execute(create_sql)
        return cursor.fetchone()[2]

def get_public_tables(cursor):
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    return [row[0] for row in cursor.fetchall()]

def stream_table_to_gcs(pg_cursor, table_name, bucket_name, gcs_hook):
    logging.info(f"Streaming table {table_name}...")
    temp_file_path = None
    try:
        # Vẫn giữ mode='wb+' (Binary)
        with tempfile.NamedTemporaryFile(mode='wb+', delete=False) as temp_file:
            temp_file_path = temp_file.name
            
            # [FIX QUAN TRỌNG]: Đổi sang cú pháp chuẩn COPY TO STDOUT
            # Cú pháp này ổn định hơn COPY (SELECT *) và tránh lỗi protocol
            sql = f"COPY public.\"{table_name}\" TO STDOUT WITH (FORMAT CSV, HEADER TRUE)"
            
            pg_cursor.copy_expert(sql, temp_file)
        
        gcs_hook.upload(
            bucket_name=bucket_name,
            object_name=f"{table_name}/snapshot/{table_name}.csv",
            filename=temp_file_path,
            mime_type='text/csv'
        )
        logging.info(f"Uploaded {table_name} successfully.")
        
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@dag(schedule=None, catchup=False)
def postgres_snapshot_cdc_to_bigquery_pipeline():

    @task
    def db_snapshot_to_gcs_task() -> list:
        # 1. Setup connection hooks & retrieve credentials
        postgres_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        postgres_conn_config = postgres_hook.get_connection(POSTGRES_CONN_ID)
        gcs_storage_hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
        
        # 2. Create REPLICATION connection (manages snapshot & slot lifecycle)
        replication_connection = psycopg2.connect(
            host=postgres_conn_config.host, 
            user=postgres_conn_config.login, 
            password=postgres_conn_config.password,
            port=postgres_conn_config.port, 
            dbname=postgres_conn_config.schema,
            connection_factory=LogicalReplicationConnection
        )
        replication_cursor = replication_connection.cursor()

        try:
            # 3. Setup replication infrastructure (publication + slot)
            create_publication_if_not_exists(replication_cursor, PUBLICATION_NAME)
            snapshot_id = create_or_recreate_replication_slot(replication_cursor, SLOT_NAME)

            # 4. Create DATA EXPORT connection (inherits snapshot from replication_connection)
            snapshot_export_connection = postgres_hook.get_conn()
            
            # CRITICAL: Disable autocommit to manage transactions manually
            # (prevents copy_expert from conflicting with implicit transactions)
            snapshot_export_connection.autocommit = True 
            
            export_cursor = snapshot_export_connection.cursor()
            
            try:
                # 5. Begin transaction at snapshot isolation level
                export_cursor.execute("BEGIN ISOLATION LEVEL REPEATABLE READ;")
                export_cursor.execute(f"SET TRANSACTION SNAPSHOT '{snapshot_id}';")
                
                # 6. Query all tables in public schema (uses snapshot isolation)
                tables = get_public_tables(export_cursor)
                
                # 7. Export each table as CSV to GCS (all at same point-in-time)
                for table in tables:
                    stream_table_to_gcs(export_cursor, table, BUCKET_NAME, gcs_storage_hook)
                
                # 8. Commit transaction
                export_cursor.execute("COMMIT;")
                logging.info(f"Successfully exported {len(tables)} tables to GCS")
                return tables

            except Exception as e:
                logging.error(f"Error during snapshot export: {e}")
                export_cursor.execute("ROLLBACK;")
                raise e
            finally:
                export_cursor.close()
                snapshot_export_connection.close()

        finally:
            replication_cursor.close()
            replication_connection.close()

    @task
    def create_external_snapshot_tables_task(table_name: str):
        # MOVE CLIENT INSIDE TASK & INPUT IS STRING (NOT LIST)
        bq_hook = BigQueryHook(gcp_conn_id=GCP_CONN_ID)
        client = bq_hook.get_client(project_id=PROJECT_ID)

        # Config format external table
        ext_cfg_csv = bigquery.ExternalConfig("CSV")
        ext_cfg_csv.source_uris = [f"gs://{BUCKET_NAME}/{table_name}/snapshot/{table_name}.csv"]
        ext_cfg_csv.autodetect = True
        ext_cfg_csv.options.skip_leading_rows = 1
        # Optional: Uncomment below if needed for special cases like order_reviews
        ext_cfg_csv.options.field_delimiter = ','
        ext_cfg_csv.options.quote_character = '"'
        ext_cfg_csv.options.allow_quoted_newlines = True
        
        table_ref = bigquery.Table(f"{PROJECT_ID}.{BRONZE}.{table_name}_snapshot_external")
        table_ref.external_data_configuration = ext_cfg_csv
        client.create_table(table_ref, exists_ok=True)
        logging.info(f"Created Snapshot Table for {table_name}")

    @task
    def create_external_cdc_tables_task(table_name: str):
        bq_hook = BigQueryHook(gcp_conn_id=GCP_CONN_ID)
        client = bq_hook.get_client(project_id=PROJECT_ID)

        # 1. Cấu hình External Table
        ext_cfg_json = bigquery.ExternalConfig("NEWLINE_DELIMITED_JSON")
        
        # Quét tất cả file con trong thư mục cdc
        # Lưu ý: Pub/Sub ghi vào cdc/dt=2026-01-21/...
        ext_cfg_json.source_uris = [f"gs://{BUCKET_NAME}/{table_name}/cdc/*"]
        ext_cfg_json.autodetect = True
        ext_cfg_json.ignore_unknown_values = True
        
        # 2. Cấu hình Hive Partitioning (QUAN TRỌNG)
        hive_partitioning_opts = bigquery.HivePartitioningOptions()
        
        # Dùng AUTO vì file có dạng chuẩn key=value ('dt=YYYY-MM-DD')
        # BigQuery sẽ tự hiểu đây là Partition Key mà không cần define Schema thủ công
        hive_partitioning_opts.mode = "AUTO"
        
        # Chỉ định thư mục gốc để BigQuery biết bắt đầu quét partition từ đâu
        hive_partitioning_opts.source_uri_prefix = f"gs://{BUCKET_NAME}/{table_name}/cdc"
        hive_partitioning_opts.require_partition_filter = False
        
        # Gán option vào config
        ext_cfg_json.hive_partitioning = hive_partitioning_opts
        
        # 3. Tạo Table Reference
        table_ref_cdc = bigquery.Table(f"{PROJECT_ID}.{BRONZE}.{table_name}_cdc_external")
        table_ref_cdc.external_data_configuration = ext_cfg_json

        # 4. Gọi lệnh tạo bảng
        client.create_table(table_ref_cdc, exists_ok=True)

    @task
    def filter_tables_with_cdc(all_tables: list) -> list:
        """Filter tables that need CDC (only these tables will be processed)"""
        # Define which tables need CDC processing
        filtered_tables = [
            "customers",
            "orders",
            "order_items",
            "sellers",
            "payments",
            "order_reviews"
        ]
        logging.info(f"Filtered {len(filtered_tables)} tables for CDC processing out of {len(all_tables)} total tables")
        return filtered_tables

    # @task
    # def create_table_bigquery(table_name: list):
    #     import utils
    #     from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
        
    #     pass

    # --- FLOW ---
    # Step 1: Export DB snapshot to GCS and get list of ALL tables
    all_tables = db_snapshot_to_gcs_task()
    
    # Step 2a: Create external snapshot tables for filtered tables
    snapshot_creation = create_external_snapshot_tables_task.expand(table_name=all_tables)

    # Step 3a: Create table in bigquery
    # bigquery_table = create_table_bigquery.expand(table_name=all_tables)

    # Step 2b: Filter to only tables that need CDC processing
    cdc_tables = filter_tables_with_cdc(all_tables)
    
    # Step 3b: Wait for CDC files for filtered tables (parallel with Step 3a)
    wait_for_cdc = GCSObjectsWithPrefixExistenceSensor.partial(
        task_id='wait_for_cdc_files',
        bucket=BUCKET_NAME,
        google_cloud_conn_id=GCP_CONN_ID,
        mode='reschedule',
        poke_interval=180,
        timeout=6000,
        soft_fail=True
    ).expand(
        prefix=cdc_tables.map(lambda t: f"{t}/cdc/")
    )
    
    # Step 4b: Create external CDC tables (depends only on CDC files being ready)
    cdc_creation = create_external_cdc_tables_task.expand(table_name=cdc_tables)
    
    # Define dependencies
    all_tables >> [snapshot_creation, cdc_tables]
    cdc_tables >> wait_for_cdc >> cdc_creation

dag_instance = postgres_snapshot_cdc_to_bigquery_pipeline()

# db ---- snapshot ----> GCS --->