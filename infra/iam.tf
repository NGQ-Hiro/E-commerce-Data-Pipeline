# allow terraform to manage IAM for GCP

data "google_secret_manager_secret" "common_env" {
  secret_id = "env"  # Tên chính xác bạn thấy trong gcloud
}

# --- NEW: Debezium IAM ---
resource "google_secret_manager_secret_iam_member" "debezium_secret_access" {
  secret_id = data.google_secret_manager_secret.common_env.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.debezium_sa.email}"
}

resource "google_project_iam_member" "debezium_pubsub_permissions" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.debezium_sa.email}"
}

# --- NEW: Postgres IAM ---
resource "google_secret_manager_secret_iam_member" "postgres_secret_access" {
  secret_id = data.google_secret_manager_secret.common_env.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.postgres_sa.email}"
}

# --- NEW: Airflow IAM ---
resource "google_secret_manager_secret_iam_member" "debezium_secret_access" {
  secret_id = data.google_secret_manager_secret.common_env.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.debezium_sa.email}"
}

locals {
  airflow_roles = [
    # "roles/pubsub.editor",         # Quản lý Pub/Sub (Tạo topic, gửi tin)
    "roles/storage.objectAdmin",   # Đọc/Ghi GCS
    "roles/bigquery.dataEditor",   # Sửa dữ liệu BigQuery
    "roles/bigquery.jobUser",      # Chạy Job BigQuery
  ]
}

resource "google_project_iam_member" "airflow_permissions" {
  for_each = toset(local.airflow_roles)

  project = var.project_id 
  role    = each.value
  member  = "serviceAccount:${google_service_account.airflow_sa.email}"
}

# --- NEW: Pub/Sub to GCS Sink Permissions ---

# 1. Retrieve the Google-managed Pub/Sub Service Account email in this project
resource "google_project_service_identity" "pubsub_agent" {
  provider = google-beta
  service  = "pubsub.googleapis.com"
}

# 2. Grant "Storage Object Creator" (allows writing files) to that account
resource "google_storage_bucket_iam_member" "pubsub_sink_creator" {
  bucket = var.bucket_name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_project_service_identity.pubsub_agent.email}"
}

# 3. Grant "Storage Legacy Bucket Reader" (allows reading bucket metadata)
resource "google_storage_bucket_iam_member" "pubsub_sink_reader" {
  bucket = var.bucket_name
  role   = "roles/storage.legacyBucketReader"
  
  member = "serviceAccount:${google_project_service_identity.pubsub_agent.email}"
}