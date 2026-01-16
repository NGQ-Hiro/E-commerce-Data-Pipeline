# allow terraform to manage IAM for GCP

# --- NEW: Debezium IAM & Key Generation ---
resource "google_project_iam_member" "debezium_pubsub_permissions" {
  project = "e-commerce-484010"
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.debezium_sa.email}"
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