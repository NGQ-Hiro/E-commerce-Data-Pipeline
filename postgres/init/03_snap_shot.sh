#!/bin/bash
set -e

export PGPASSWORD=123

DB_PORT=5432
DB_NAME=olist
DB_USER=admin

psql -U $DB_USER -d $DB_NAME -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'dbz_publication') THEN
        CREATE PUBLICATION dbz_publication FOR ALL TABLES;
    END IF;
END
\$\$;"

echo "Create logical replication slot (for CDC later)..."

psql -U $DB_USER -d $DB_NAME -c "
SELECT 'snap_shot' FROM pg_replication_slots WHERE slot_name = 'snap_shot'
UNION ALL
SELECT pg_create_logical_replication_slot('snap_shot', 'pgoutput')
WHERE NOT EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = 'snap_shot');" \
> /dev/null 2>&1