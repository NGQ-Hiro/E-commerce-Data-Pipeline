variable "project_id" {
  type    = string
  default = "e-commerce-484010"
}

variable "region" {
  description = "Your project region"
  default     = "us-central1"
  type        = string
}

variable "zone" {
  description = "Your project zone"
  default     = "us-central1-a"
  type        = string
}

variable "vm_image" {
  description = "Image for you VM"
  default     = "ubuntu-os-cloud/ubuntu-2204-lts"
  type        = string
}

variable "bucket_name" {
  type    = string
  default = "olist-ecommerce-bucket"
}

variable "db_name" {
  type    = string
  default = "olist"
}

variable "schema" {
  type    = string
  default = "public"
}

variable "tables" {
  type = set(string)
  default = [
    "customers",
    "orders",
    "order_items",
    "sellers",
    "payments",
    "order_reviews"
  ]
}

