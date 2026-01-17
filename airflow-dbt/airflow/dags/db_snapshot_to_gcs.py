import csv
import io
import logging
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.google.cloud.hooks.gcs import GCSHook

@task
def stream_snapshot_to_gcs():
    # 1. Kết nối Postgres
    pg_hook = PostgresHook(postgres_conn_id='my_postgres_conn')
    conn = pg_hook.get_conn()
    conn.set_isolation_level(3) # REPEATABLE READ
    
    cursor = conn.cursor()
    
    # 2. Tạo Transaction & Snapshot
    # Lưu ý: Cần tạo slot trước bằng tay hoặc code riêng
    cursor.execute("SELECT pg_export_snapshot();")
    snapshot_id = cursor.fetchone()[0]
    logging.info(f"Created Snapshot ID: {snapshot_id}")
    
    # Lấy danh sách bảng
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    tables = [row[0] for row in cursor.fetchall()]
    
    gcs_hook = GCSHook(gcp_conn_id='my_gcp_conn')
    bucket_name = 'my-datalake-bucket'
    
    # 3. Loop qua từng bảng và stream lên GCS
    for table in tables:
        logging.info(f"Streaming table {table}...")
        
        # Mở connection con (worker) để dump data
        # Lý do: Cần giữ conn chính để duy trì Snapshot ID
        conn_worker = pg_hook.get_conn()
        cursor_worker = conn_worker.cursor()
        
        # Join vào snapshot cũ
        cursor_worker.execute("BEGIN ISOLATION LEVEL REPEATABLE READ;")
        cursor_worker.execute(f"SET TRANSACTION SNAPSHOT '{snapshot_id}';")
        
        # Dùng copy_expert để lấy data dạng CSV ra buffer memory
        # Lưu ý: Nếu bảng quá lớn (> vài GB), cần viết logic chia nhỏ (chunking)
        # hoặc dùng NamedTemporaryFile để tránh tràn RAM Airflow Worker.
        output = io.StringIO()
        sql = f"COPY (SELECT * FROM public.\"{table}\") TO STDOUT WITH CSV HEADER"
        cursor_worker.copy_expert(sql, output)
        
        # Upload lên GCS từ memory
        gcs_hook.upload(
            bucket_name=bucket_name,
            object_name=f"snapshot/{table}.csv",
            data=output.getvalue(),
            mime_type='text/csv'
        )
        
        output.close()
        cursor_worker.close()
        conn_worker.close()

    # 4. Commit & Clean up
    conn.commit()
    conn.close()