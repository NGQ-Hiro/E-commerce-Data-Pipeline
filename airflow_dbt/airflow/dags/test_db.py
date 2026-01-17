from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from pendulum import datetime


def test_postgres_connection():
    hook = PostgresHook(postgres_conn_id="postgres_default")
    conn = hook.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    print("Connection OK, result:", result)


with DAG(
    dag_id="test_postgres_connection_v3",
    # start_date=datetime(2024, 1, 1, tz="UTC"),
    schedule=None,          # chỉ chạy khi trigger tay
    catchup=False,
    tags=["test", "db"],
) as dag:

    test_db = PythonOperator(
        task_id="test_postgres_connection",
        python_callable=test_postgres_connection,
    )
