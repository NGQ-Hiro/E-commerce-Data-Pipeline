from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2026, 1, 1),
}

# Define DAG
dag = DAG(
    'daily_dbt',
    default_args=default_args,
    description='Test dbt BigQuery run',
    catchup=False,
    tags=['test', 'dbt', 'bigquery'],
)

# Task: dbt run (run transformations)
dbt_run = DockerOperator(
    task_id='dbt_run',
    image='ghcr.io/dbt-labs/dbt-bigquery:latest',
    command='run',
    working_dir='/usr/app',
    auto_remove='success',
    docker_url='unix://var/run/docker.sock',
    network_mode='airflow_dbt_my-network',
    mounts=[
        Mount(source='/home/newuser/Project/e-commerce/airflow_dbt/dbt/e_commerce', 
              target='/usr/app', 
              type='bind'),
        Mount(source='/home/newuser/Project/e-commerce/airflow_dbt/dbt/profiles.yml', 
              target='/root/.dbt/profiles.yml', 
              type='bind'),
    ],
    dag=dag,
)
