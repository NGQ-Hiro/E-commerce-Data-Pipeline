terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.15.0"
    }
    # Added 'local' provider to save the key to a file automatically
    local = {
      source  = "hashicorp/local"
      version = "2.5.1"
    }
  }
}

provider "google" {
  project     = "e-commerce-484010"
  region      = var.region
  credentials = "gcp-terraform-key.json" # This is your Terraform Admin key
}

provider "google-beta" {
  project     = "e-commerce-484010"
  region      = var.region
  credentials = "gcp-terraform-key.json" # MUST match the key above
}

# --- Your Existing Bucket ---
resource "google_storage_bucket" "my_bucket" {
  name                        = var.bucket_name
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
}



# -- Create Pub/Sub Topic and Subscription for each table in db --

## Topic

resource "google_pubsub_topic" "cdc_topics" {
  for_each = var.tables
  name     = "${var.db_name}.${var.schema}.${each.key}"
}

## Subscription

resource "google_pubsub_subscription" "cdc_gcs_subscriptions" {
  for_each = var.tables

  # name of the subscription
  name = "gcs_sub_${var.db_name}.${var.schema}.${each.key}"

  # connect into topic above
  topic = google_pubsub_topic.cdc_topics[each.key].name

  cloud_storage_config {
    bucket = var.bucket_name

    # filename_prefix = "${each.key}/cdc/year=/month=/day=/"
    filename_prefix = "${each.key}/cdc/dt="
    filename_datetime_format = "YYYY-MM-DD/hh_mm_ss"
    filename_suffix = ".json"
    

    max_duration = "300s"
    max_bytes = 104857600 
    max_messages = 10000
  }

  ack_deadline_seconds = 300
  depends_on = [
    google_storage_bucket_iam_member.pubsub_sink_creator,
    google_storage_bucket_iam_member.pubsub_sink_reader
  ]
}

# Create dataset 
resource "google_bigquery_dataset" "e-commerce-dataset-bronze" {
  dataset_id = "e_commerce_dataset_bronze"
  location   = var.region
}

resource "google_bigquery_dataset" "e-commerce-dataset-silver" {
  dataset_id = "e_commerce_dataset_silver"
  location   = var.region
}

resource "google_bigquery_dataset" "e-commerce-dataset-gold" {
  dataset_id = "e_commerce_dataset_gold"
  location   = var.region
}