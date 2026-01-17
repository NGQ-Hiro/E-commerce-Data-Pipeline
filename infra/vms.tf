locals {
  ssh_user = "hieu"

  public_key_path = "/home/newuser/.ssh/gcloud.pub"
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
  target_tags   = ["my-cluster"]
}

# --- VM 1: Postgres ---
resource "google_compute_instance" "vm_postgres" {
  name         = "vm-postgres"
  machine_type = "e2-medium"
  zone = var.zone
  tags         = ["my-cluster"]

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

  metadata_startup_script = templatefile("${path.module}/../scripts/vm_setup.sh", {
    target_service = "postgres"
  })

  service_account {
    email = google_service_account.postgres_sa.email
    scopes = ["cloud-platform"]
  }
}

# --- VM 2: Debezium ---
resource "google_compute_instance" "vm_debezium" {
  name         = "vm-debezium"
  machine_type = "e2-medium"
  zone = var.zone
  tags         = ["my-cluster"]

  boot_disk {
    initialize_params {
      image = var.vm_image
      size  = 10
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

  metadata_startup_script = templatefile("${path.module}/../scripts/vm_setup.sh", {
    target_service = "debezium"
  })

  service_account {
    email = google_service_account.debezium_sa.email
    scopes = ["cloud-platform"]
  }
}

# --- VM 3: Airflow ---
resource "google_compute_instance" "vm_airflow" {
  name         = "vm-airflow"
  machine_type = "e2-standard-2"
  zone = var.zone
  tags         = ["my-cluster"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 30
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

  metadata_startup_script = templatefile("${path.module}/../scripts/vm_setup.sh", {
    target_service = "airflow"
  })

  service_account {
    email = google_service_account.airflow_sa.email
    scopes = ["cloud-platform"]
  }
}

# # --- Output: In ra lệnh SSH sẵn để copy ---
output "cmd_ssh_airflow" {
  value = "ssh -i ~/.ssh/gcloud ${local.ssh_user}@${google_compute_instance.vm_airflow.network_interface.0.access_config.0.nat_ip}"
}

output "cmd_ssh_postgres" {
  value = "ssh -i ~/.ssh/gcloud ${local.ssh_user}@${google_compute_instance.vm_postgres.network_interface.0.access_config.0.nat_ip}"
}

output "cmd_ssh_debezium" {
  value = "ssh -i ~/.ssh/gcloud ${local.ssh_user}@${google_compute_instance.vm_debezium.network_interface.0.access_config.0.nat_ip}"
}