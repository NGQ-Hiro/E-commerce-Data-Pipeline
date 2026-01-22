from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

# Define DAG
dag = DAG(
    'test_dbt_bigquery_run',
    default_args=default_args,
    description='Test dbt BigQuery run',
    catchup=False,
    tags=['test', 'dbt', 'bigquery'],
)

# Task 1: Check dbt version
check_dbt_version = DockerOperator(
    task_id='check_dbt_version',
    image='ghcr.io/dbt-labs/dbt-bigquery:latest',
    command='dbt --version',
    working_dir='/usr/app',
    auto_remove=True,
    docker_url='unix://var/run/docker.sock',
    network_mode='my-network',
    dag=dag,
)

# Task 2: dbt debug (check connection to BigQuery)
dbt_debug = DockerOperator(
    task_id='dbt_debug',
    image='ghcr.io/dbt-labs/dbt-bigquery:latest',
    command='debug',
    working_dir='/usr/app',
    auto_remove=True,
    docker_url='unix://var/run/docker.sock',
    network_mode='my-network',
    mounts=[
        Mount(source='/home/hieu/E-commerce-Data-Pipeline/airflow_dbt/dbt/e_commerce', 
              target='/usr/app', 
              type='bind'),
        Mount(source='/home/hieu/E-commerce-Data-Pipeline/airflow_dbt/dbt/e_commerce/dbt/profiles.yml', 
              target='/root/.dbt/profiles.yml', 
              type='bind'),
    ],
    dag=dag,
)

# Task 3: dbt run (run transformations)
dbt_run = DockerOperator(
    task_id='dbt_run',
    image='ghcr.io/dbt-labs/dbt-bigquery:latest',
    command='run --select test',
    working_dir='/usr/app',
    auto_remove=True,
    docker_url='unix://var/run/docker.sock',
    network_mode='my-network',
    mounts=[
        Mount(source='/home/hieu/E-commerce-Data-Pipeline/airflow_dbt/dbt/e_commerce', 
              target='/usr/app', 
              type='bind'),
        Mount(source='/home/hieu/E-commerce-Data-Pipeline/airflow_dbt/dbt/e_commerce/dbt/profiles.yml', 
              target='/root/.dbt/profiles.yml', 
              type='bind'),
    ],
    dag=dag,
)


# Set task dependencies
check_dbt_version >> dbt_debug >> dbt_run
