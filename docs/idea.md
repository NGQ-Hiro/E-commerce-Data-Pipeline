# Data source

- Olist.csv -> database
- One process python simulate transaction
- Using CDC (debezium) capture data change load to kafka and push to GCS bronze

# Batch Process

## Ingest

### Initial Load

- Create book mark in WAL (PostgreSQL) from consistency snapshot (whether transactions still happens data in snapshot will be consistent)
- Using tool read data change from that book mark

### Incremental Load (CDC)

- Using CDC tool to capture all change since that book mark
- Merge from this

## BigQuery External Table point to Raw CDC and snapshot in GCS

- BigQuery table that points directly to the folder in GCS.

## Transform

- Merge CDC in bronze -> silver -> gold using dbt-bigquery

## Train model

- Using data to train model
- Deploy that model

# Visulization

- Dashboard: ....

# Orchestration

- Airflow with dbt will run on VMs instance in GCP

- Airflow task: take snapshot -> push to GCS, 

[wait_for_gcs_bronze]
↓
[validate_external_table]
↓
[dbt_bronze_to_silver]
↓
[dbt_silver_to_gold]
↓
[data_quality_checks]
↓
[train_model]
↓
[deploy_model]

# CI/CD
