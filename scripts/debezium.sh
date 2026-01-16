#!/bin/bash

# These variables will be filled by Terraform
PG_HOST="vm-postgres"
PG_PORT="5432"

echo ">>> [Debezium Helper] Starting connectivity check..."
echo ">>> Target: $PG_HOST:$PG_PORT"

# ---------------------------------------------------------
# LOOP: WAIT FOR POSTGRES
# ---------------------------------------------------------

while ! timeout 1 bash -c "cat < /dev/null > /dev/tcp/$PG_HOST/$PG_PORT"; do
  echo "   [Wait] Postgres is not ready yet. Retrying in 2 seconds..."
  sleep 2
done

echo ">>> ------------------------------------------------"
echo ">>> SUCCESS: Connection to Postgres established!"
echo ">>> ------------------------------------------------"

echo ">>> Starting Debezium..."
docker compose up -d --no-deps debezium