# E-Commerce Data Pipeline

A production-ready data pipeline for e-commerce analytics built on Google Cloud Platform, featuring real-time CDC ingestion, dimensional modeling with SCD Type 2 tracking, and incremental transformations.

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Prerequisites](#setup--prerequisites)
- [Data Model](#data-model)
- [Pipeline Layers](#pipeline-layers)
- [Running the Pipeline](#running-the-pipeline)
- [Key Features](#key-features)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## Architecture

```
PostgreSQL (Source)
    ↓
Debezium CDC
    ↓
Google Cloud Storage (Bronze Layer)
    ↓
BigQuery (Bronze → Silver → Gold)
    ↓
Analytics & BI Tools
```

### Data Flow

1. **Ingestion**: PostgreSQL data captured via Debezium CDC and snapshots exported to GCS
2. **Bronze Layer**: External tables in BigQuery pointing to CDC and snapshot data
3. **Silver Layer**: Incremental models with SCD Type 2 for slowly changing dimensions (customers, sellers)
4. **Gold Layer**: Fact and dimension tables optimized for analytics queries

---

## Tech Stack

- **Data Source**: PostgreSQL (Brazilian e-commerce dataset)
- **CDC Engine**: Debezium (Postgres connector → Kafka)
- **Cloud Platform**: Google Cloud (BigQuery, Cloud Storage, Cloud Run)
- **Orchestration**: Apache Airflow
- **Transformation**: dbt (data build tool)
- **Infrastructure as Code**: Terraform
- **Containerization**: Docker

---

## Project Structure

```
e-commerce/
├── postgres/                          # Source database & sample data
│   ├── docker-compose.yaml
│   ├── init/                         # SQL scripts for source tables
│   │   ├── 01_create_table.sql
│   │   └── 02_load_data.sql
│   ├── olist_csv/                    # Brazilian e-commerce dataset
│   └── simulate.py                   # Data generator for CDC simulation
│
├── debezium/                          # CDC configuration
│   └── docker-compose.yaml
│
├── infra/                             # GCP Infrastructure (Terraform)
│   ├── main.tf                        # BigQuery datasets & tables
│   ├── iam.tf                         # Service accounts & permissions
│   ├── service_accounts.tf
│   ├── vms.tf                         # Compute instances
│   └── terraform.tfstate
│
├── airflow_dbt/                       # Orchestration & Transformation
│   ├── airflow/
│   │   ├── airflow.cfg                # Airflow configuration
│   │   └── dags/
│   │       ├── daily_dbt.py           # Daily dbt run DAG
│   │       ├── test_dbt.py
│   │       └── utils/
│   │           └── schema.py
│   │
│   └── dbt/
│       ├── profiles.yml               # BigQuery connection config
│       └── e_commerce/
│           ├── dbt_project.yml
│           ├── models/
│           │   ├── bronze/            # External table references (not materialized)
│           │   ├── silver/            # Incremental transformations with SCD
│           │   │   ├── customers.sql  # SCD Type 2, incremental merge
│           │   │   ├── sellers.sql    # SCD Type 2, incremental merge
│           │   │   ├── orders.sql
│           │   │   ├── products.sql
│           │   │   ├── geolocations.sql
│           │   │   ├── order_items.sql
│           │   │   ├── order_reviews.sql
│           │   │   └── payments.sql
│           │   │
│           │   └── gold/              # Analytics-ready tables & views
│           │       ├── dim_customers.sql     # View (all SCD versions)
│           │       ├── dim_sellers.sql       # View (all SCD versions)
│           │       ├── dim_products.sql      # View
│           │       ├── dim_geolocations.sql  # View
│           │       ├── dim_date.sql          # Table (static)
│           │       ├── dim_reviews.sql       # View
│           │       ├── fact_orders.sql       # Table (main analytics table)
│           │       └── big_table.sql         # Incremental denormalized table
│           │
│           ├── macros/
│           │   └── generate_schema_name.sql
│           │
│           └── tests/                 # dbt tests (optional)
│
└── docs/                              # Documentation
    ├── data_model.md
    ├── gcp_free.md
    └── command.md
```

---

## Setup & Prerequisites

### Requirements

- Docker & Docker Compose
- Python 3.10+
- GCP project with BigQuery, Cloud Storage enabled
- Google Cloud credentials (`gcp-terraform-key.json`)
- dbt 1.11+

### 1. Initialize GCP Infrastructure

```bash
cd infra/
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply
```

### 2. Start PostgreSQL & Debezium

```bash
cd postgres/
docker-compose up -d
# Load sample data
docker-compose exec postgres psql -U postgres -d ecommerce -f /docker-entrypoint-initdb.d/01_create_table.sql
docker-compose exec postgres psql -U postgres -d ecommerce -f /docker-entrypoint-initdb.d/02_load_data.sql

cd ../debezium/
docker-compose up -d
# Configure Debezium connectors via REST API
curl -X POST http://localhost:8083/connectors ...
```

### 3. Setup Airflow & dbt

```bash
cd airflow_dbt/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize Airflow DB
airflow db init

# Start Airflow
airflow webserver -p 8080 &
airflow scheduler &
```

### 4. Configure dbt profiles

```bash
# Set GCP credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-terraform-key.json

# Test dbt connection
cd dbt/e_commerce
dbt debug --profiles-dir ..
```

---

## Data Model

### Source Tables (PostgreSQL)

- `customers` - Customer master data
- `sellers` - Seller master data
- `products` - Product catalog
- `orders` - Order transactions
- `order_items` - Items per order
- `order_payments` - Payment details
- `order_reviews` - Customer reviews
- `geolocations` - Geographic reference

### Bronze Layer (External Tables in BigQuery)

**CDC Tables** (incremental, from Debezium):
- `*_cdc_external` - Change data capture events (op, ts_ms, dt, after/before)

**Snapshot Tables** (full refreshes):
- `*_snapshot_external` - Point-in-time copies of source data

### Silver Layer (Incremental Transformations)

#### SCD Type 2 Models

**customers.sql** & **sellers.sql**:
- ✅ Incremental merge strategy
- ✅ SCD Type 2 tracking: `valid_from`, `valid_to`, `is_current`
- ✅ Unique key: `scd_id` (UUID generated per version)
- ✅ Optimized: Only fetches old records affected by new CDC events
- ✅ Window functions: `lead()` over time to compute validity periods

Example logic:
```sql
-- Build all events (old + new), then compute validity windows
processing_scd as (
    select 
        coalesce(scd_id, generate_uuid()) as scd_id,
        customer_id,
        ... 
        lead(event_timestamp) over (
            partition by customer_id order by event_timestamp asc
        ) as next_event_time
    from all_events
)
```

#### Regular Incremental Models

**orders.sql**, **payments.sql**, **order_items.sql**, **order_reviews.sql**:
- ✅ Incremental merge with deduplication
- ✅ CDC watermark filters

### Gold Layer (Analytics-Ready)

#### Dimensions (Views)
- `dim_customers` - All SCD versions with `valid_from`, `valid_to`, `is_current`
- `dim_sellers` - All SCD versions with temporal attributes
- `dim_products` - Static product attributes
- `dim_geolocations` - Geographic coordinates
- `dim_date` - Date spine (2016–2026) with holidays, weekends
- `dim_reviews` - Review details

#### Facts (Materialized Tables)
- `fact_orders` - Order-item grain with customer/seller SCD keys, geolocation details
- `big_table` - Incremental denormalized fact (order + items + payments + reviews in one row)

#### Key Patterns

**Temporal Joins in fact_orders**:
```sql
left join dim_customers c 
    on o.customer_id = c.customer_id 
    and o.order_purchase_timestamp between c.valid_from and c.valid_to
```
Ensures each order gets the correct version of customer/seller attributes at order time.

**Incremental Load in big_table**:
```sql
where cast(order_purchase_timestamp as date) >= (
    select date_sub(coalesce(max(order_date), date('1900-01-01')), interval 3 day)
    from {{ this }}
)
```
Look-back window (3 days) to handle late-arriving data updates.

---

## Pipeline Layers

### Layer 1: Bronze (External Tables)
- **Materialization**: External (no storage cost)
- **Refresh**: CDC continuous + snapshots (daily)
- **Purpose**: Raw ingestion layer, immutable source

### Layer 2: Silver (Incremental Transformations)
- **Materialization**: BigQuery tables
- **Strategy**: Merge (upsert) on unique keys
- **Update Frequency**: Incremental on CDC events
- **SCD Tracking**: Type 2 for customers & sellers (full history)
- **Purpose**: Clean, deduplicated, slowly-changing-dimension-tracked

### Layer 3: Gold (Analytics-Ready)
- **Materialization**:
  - Views for lightweight dimensions (no storage overhead)
  - Tables for fact tables (optimized for queries)
- **Update Frequency**: Incremental (fact tables), real-time (views)
- **Purpose**: Optimized for BI, dashboards, aggregations

---

## Running the Pipeline

### Manual dbt Runs

```bash
cd airflow_dbt/dbt/e_commerce

# Full refresh
dbt run --profiles-dir ..

# Incremental run (respects materialization strategy)
dbt run --profiles-dir ..

# Specific model
dbt run --select customers --profiles-dir ..

# Plus dependencies
dbt run --select +fact_orders --profiles-dir ..

# Generate docs
dbt docs generate --profiles-dir ..
dbt docs serve --profiles-dir ..
```

### Airflow DAG

**Daily dbt Run** (`daily_dbt.py`):
- Single task: `dbt_run`
- Command: `dbt run` (all models)
- Schedule: Daily (configurable)
- Docker executor with mounted dbt project

Trigger manually:
```bash
airflow dags test test_dbt_bigquery_run
```

### End-to-End Test

```bash
# 1. Simulate new CDC events
python postgres/simulate.py

# 2. Run dbt pipeline
dbt run --profiles-dir ..

# 3. Verify row counts
bq query --use_legacy_sql=false '
  SELECT 
    COUNT(*) as big_table_rows, 
    MAX(order_date) as latest_date
  FROM `e-commerce-484010.e_commerce_dataset_gold.big_table`
'
```

---

## Key Features

### ✅ Slowly Changing Dimensions (SCD Type 2)

Track all changes to customers & sellers over time:
- `valid_from` - Start of validity period
- `valid_to` - End of validity period (9999-12-31 if current)
- `is_current` - Boolean flag for current version
- `scd_id` - Unique version ID

Use case: "How many distinct addresses did customer X have in Q3 2025?"

### ✅ Incremental Transformations

All silver/gold models use `merge` strategy:
- Upserts on existing keys (no full table rebuilds)
- Partitioning & clustering for fast lookups
- 3-day look-back window for late-arriving updates

### ✅ Temporal Joins

Fact tables join dimensions using time-valid keys:
```sql
and order_purchase_timestamp between dim.valid_from and dim.valid_to
```

Ensures analytical integrity (correct version at order time).

### ✅ Incremental Fact Tables

`big_table` (denormalized fact):
- Partitioned by `order_date` (monthly)
- Clustered by `order_id`
- Merged daily with 3-day look-back
- Handles items, payments, reviews in single row

### ✅ View-Based Dimensions

Lightweight dimensions as views:
- No storage cost
- Always reflect latest silver data
- Fast query performance via BigQuery optimization

---

## Monitoring & Troubleshooting

### dbt Runs

**Check execution logs**:
```bash
dbt run --profiles-dir .. --debug
```

**View compiled SQL**:
```bash
cat target/compiled/e_commerce/models/silver/customers.sql
```

**Run tests** (if configured):
```bash
dbt test --profiles-dir ..
```

### BigQuery Queries

**Check model row counts**:
```bash
bq ls -m e_commerce_dataset_silver
bq show --schema e_commerce_dataset_silver.customers
```

**Verify incremental runs**:
```sql
SELECT 
  order_id, 
  COUNT(*) as version_count
FROM `e-commerce-484010.e_commerce_dataset_gold.big_table`
GROUP BY order_id
HAVING version_count > 1
ORDER BY version_count DESC;
```

### Common Issues

**Issue**: `Unrecognized name: scd_id`
- **Cause**: Missing `FROM processing_scd` clause in incremental branch
- **Fix**: Ensure `select` clause includes `from processing_scd`

**Issue**: `BETWEEN type mismatch (DATE vs TIMESTAMP)`
- **Cause**: Comparing `cast(timestamp as date)` with `timestamp` columns
- **Fix**: Use `timestamp between valid_from and valid_to` directly

**Issue**: `Name seller_id not found inside o`
- **Cause**: `seller_id` is in `order_items`, not `orders`
- **Fix**: Use `oi.seller_id` in select and joins

**Issue**: Quota exceeded warnings
- **Fix**: Set quota project:
  ```bash
  gcloud auth application-default set-quota-project e-commerce-484010
  ```

### Airflow Monitoring

- **WebUI**: http://localhost:8080
- **Task logs**: Click task → Log tab
- **Trigger manual runs**: Airflow UI or CLI

---

## Performance Tips

1. **Incremental Runs**: Always use `dbt run` (respects merge strategies)
2. **Partition Pruning**: Filter on `order_date` in queries
3. **Clustering**: Join on `order_id`, `customer_id`, `seller_id`
4. **CDC Optimization**: 3-day look-back prevents missed updates without full reacquits
5. **View Caching**: Gold layer views leverage BigQuery caching

---

## Next Steps

- [ ] Set up Looker/Tableau dashboards on gold tables
- [ ] Add dbt tests for data quality assertions
- [ ] Configure Slack alerts in Airflow
- [ ] Implement cost monitoring (GCP Budget Alerts)
- [ ] Document custom macros (if any)
- [ ] Set up CI/CD for dbt (dbt Cloud or GitHub Actions)

---

## Support & References

- [dbt Documentation](https://docs.getdbt.com)
- [BigQuery Docs](https://cloud.google.com/bigquery/docs)
- [Debezium Docs](https://debezium.io)
- [Apache Airflow Docs](https://airflow.apache.org)

---

**Last Updated**: March 2026  
**Maintainer**: Data Engineering Team  
**Project Repository**: `/home/newuser/Project/e-commerce`
