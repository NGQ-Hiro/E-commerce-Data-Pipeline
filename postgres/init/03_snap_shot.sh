#!/bin/bash
set -e

export PGPASSWORD=123

DB_PORT=5432
DB_NAME=olist
DB_USER=admin
SNAPSHOT_DIR=/snap_shot

echo "Create logical replication slot (for CDC later)..."

psql  -U $DB_USER -d $DB_NAME \
  -c "SELECT pg_create_logical_replication_slot('snap_shot', 'pgoutput');" \
  || echo "Slot already exists, skip"

echo "Start snapshot to CSV..."

mkdir -p ${SNAPSHOT_DIR}

TABLES=$(psql  -U $DB_USER -d $DB_NAME -Atc "
  SELECT tablename
  FROM pg_tables
  WHERE schemaname = 'public';
")

for TABLE in $TABLES; do
  echo "Snapshot table: $TABLE"

  psql  -U $DB_USER -d $DB_NAME \
    -c "\copy ${TABLE} TO '${SNAPSHOT_DIR}/${TABLE}.csv' CSV HEADER"
done

echo "Snapshot completed."
