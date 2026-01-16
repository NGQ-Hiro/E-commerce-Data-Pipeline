# --- NEW: Debezium IAM & Key Generation ---

# 1. Create the Service Account for Debezium
resource "google_service_account" "debezium_sa" {
  account_id   = "debezium-connector-sa"
  display_name = "Debezium Server Service Account"
  description  = "Used by Debezium Docker container to publish CDC events to Pub/Sub"
}

resource "google_service_account" "postgres_sa" {
  account_id   = "postgres-sa"
  display_name = "Postgres VM Service Account"
  description = "Used by Postgres VM to access Secret .env"
}