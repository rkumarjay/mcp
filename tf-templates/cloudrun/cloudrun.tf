# VPC Access Connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "${var.service_name}-connector"
  region        = var.region
  network       = var.vpc_name
  ip_cidr_range = "10.8.0.0/28"
  
  depends_on = [
    google_project_service.vpcaccess_api
  ]
}

# Enable required APIs
resource "google_project_service" "run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "vpcaccess_api" {
  service            = "vpcaccess.googleapis.com"
  disable_on_destroy = false
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "default" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    # VPC configuration - route all traffic through VPC
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }

    # Scaling configuration
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    # Container configuration
    containers {
      image = var.container_image
      
      ports {
        container_port = var.container_port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }
    }

    # Service account (can be customized)
    # service_account = google_service_account.cloudrun_sa.email
  }

  # Traffic configuration
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.run_api,
    google_vpc_access_connector.connector
  ]
}

# IAM policy - Require authentication
# By default, Cloud Run requires authentication unless you explicitly allow unauthenticated access
# To enforce IAM authentication, do NOT add the allUsers invoker role
# Only authenticated users with the appropriate IAM permissions can invoke the service

# Example: Allow specific users or service accounts to invoke
# resource "google_cloud_run_v2_service_iam_member" "invoker" {
#   name     = google_cloud_run_v2_service.default.name
#   location = google_cloud_run_v2_service.default.location
#   role     = "roles/run.invoker"
#   member   = "user:example@example.com"
# }

# Note: Binary Authorization is disabled by default
# To enable Binary Authorization, uncomment and configure:
# resource "google_binary_authorization_policy" "policy" {
#   admission_whitelist_patterns {
#     name_pattern = "gcr.io/${var.project_id}/*"
#   }
#   default_admission_rule {
#     evaluation_mode  = "REQUIRE_ATTESTATION"
#     enforcement_mode = "ENFORCED_BLOCK_AND_AUDIT_LOG"
#     require_attestations_by = [
#       google_binary_authorization_attestor.attestor.name,
#     ]
#   }
# }
