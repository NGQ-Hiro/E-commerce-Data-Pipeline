#!/bin/bash

# These variables will be filled by Terraform
PG_HOST="${VM_POSTGRES}"
PG_PORT="5432"

echo ">>> [Debezium Helper] Starting connectivity check..."
echo ">>> Target: $PG_HOST:$PG_PORT"

# ---------------------------------------------------------
# LOOP: WAIT FOR POSTGRES
# ---------------------------------------------------------
# logic: Try to open a TCP connection. If it fails, sleep 2s and repeat.
# timeout 1: Prevents hanging if packets are dropped.
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

# (Optional) You can add your curl command to register the connector here
# ./register_connector.sh