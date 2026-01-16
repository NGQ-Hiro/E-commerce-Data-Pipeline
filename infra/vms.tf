locals {
  ssh_user = "hieu"

  public_key_path = "C:/Users/QUANG HIEU/.ssh/gcloud.pub"
}

# --- Firewall: Mở cổng SSH, Web UI và Database ---
resource "google_compute_firewall" "allow_custom_ports" {
  name    = "allow-debezium-airflow"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22", "8080", "8083", "5432"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["data-lab"]
}

# --- VM 1: Debezium & Postgres ---
resource "google_compute_instance" "vm_debezium" {
  name         = "vm-debezium-postgres"
  machine_type = "e2-medium"
  zone = var.zone
  tags         = ["data-lab"]

  boot_disk {
    initialize_params {
      image = var.vm_image
      size  = 20
    }
  }

  network_interface {
    network = "default"
    access_config {} # Cấp Public IP
  }

  # Inject SSH Key
  metadata = {
    ssh-keys = "${local.ssh_user}:${file(local.public_key_path)}"
  }

  metadata_startup_script = file("${path.module}/../scripts/vm_setup.sh")
}

# --- VM 2: Airflow & DBT ---
# resource "google_compute_instance" "vm_airflow" {
#   name         = "vm-airflow-dbt"
#   machine_type = "e2-standard-2"
#   tags         = ["data-lab"]

#   boot_disk {
#     initialize_params {
#       image = "debian-cloud/debian-11"
#       size  = 30
#     }
#   }

#   network_interface {
#     network = "default"
#     access_config {} # Cấp Public IP
#   }

#   # Inject SSH Key
#   metadata = {
#     ssh-keys = "${local.ssh_user}:${file(local.public_key_path)}"
#   }

#   metadata_startup_script = file("${path.module}/scripts/install_airflow_dbt.sh")
# }

# # --- Output: In ra lệnh SSH sẵn để copy ---
# output "cmd_ssh_debezium" {
#   value = "ssh -i C:\\.ssh\\gcloud ${local.ssh_user}@${google_compute_instance.vm_debezium.network_interface.0.access_config.0.nat_ip}"
# }

# output "cmd_ssh_airflow" {
#   value = "ssh -i C:\\.ssh\\gcloud ${local.ssh_user}@${google_compute_instance.vm_airflow.network_interface.0.access_config.0.nat_ip}"
# }