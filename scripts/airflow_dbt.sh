#!/bin/bash
# Load environment variables
gcloud secrets versions access latest --secret="env" > .env

# Start airflow services
docker compose up -d