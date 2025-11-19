# Data source to reference existing Cloud Run service
data "google_cloud_run_v2_service" "cloudrun" {
  name     = var.service_name
  location = var.region
  project  = var.project_id
}

# Data source for VPC network
data "google_compute_network" "vpc" {
  name    = var.vpc_name
  project = var.project_id
}

# Data source for subnet
data "google_compute_subnetwork" "subnet" {
  name    = var.subnet_name
  region  = var.region
  project = var.project_id
}

# Regional Serverless Network Endpoint Group for Cloud Run
resource "google_compute_region_network_endpoint_group" "cloudrun_neg" {
  name                  = "${var.lb_name}-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id

  cloud_run {
    service = data.google_cloud_run_v2_service.cloudrun.name
  }
}

# Regional Backend Service (HTTPS protocol)
resource "google_compute_region_backend_service" "default" {
  name                  = "${var.lb_name}-backend"
  region                = var.region
  protocol              = "HTTPS"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  timeout_sec           = 30

  backend {
    group           = google_compute_region_network_endpoint_group.cloudrun_neg.id
    balancing_mode  = "UTILIZATION"
    capacity_scaler = 1.0
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# SSL Certificate (Self-signed for external use)
# Note: For testing without domain, we'll deploy without SSL first
# Uncomment this resource and update the proxy when you have a valid domain
# resource "google_compute_region_ssl_certificate" "lb_cert" {
#   name        = "lb-cert"
#   region      = var.region
#   description = "Certificate for external load balancer"
#   
#   # For production, use Google-managed certificate:
#   # managed {
#   #   domains = ["your-domain.com"]
#   # }
# }

# Regional URL Map
resource "google_compute_region_url_map" "default" {
  name            = "${var.lb_name}-url-map"
  region          = var.region
  default_service = google_compute_region_backend_service.default.id
}

# Note: SSL Policy and HTTPS proxy commented out for HTTP testing
# Uncomment when using HTTPS with valid certificate
# resource "google_compute_ssl_policy" "default" {
#   name            = "${var.lb_name}-ssl-policy"
#   profile         = "MODERN"
#   min_tls_version = "TLS_1_2"
# }
# 
# resource "google_compute_region_target_https_proxy" "default" {
#   name             = "${var.lb_name}-https-proxy"
#   region           = var.region
#   url_map          = google_compute_region_url_map.default.id
#   ssl_certificates = [google_compute_region_ssl_certificate.lb_cert.id]
#   ssl_policy       = google_compute_ssl_policy.default.id
# }

# Regional HTTP Target Proxy (for testing without certificate)
resource "google_compute_region_target_http_proxy" "default" {
  name    = "${var.lb_name}-http-proxy"
  region  = var.region
  url_map = google_compute_region_url_map.default.id
}

# Reserve External IP Address
resource "google_compute_address" "lb_ip" {
  name         = "${var.lb_name}-ip"
  region       = var.region
  address_type = "EXTERNAL"
}

# Regional Forwarding Rule (External, HTTP for testing)
resource "google_compute_forwarding_rule" "http" {
  name                  = "${var.lb_name}-http-rule"
  region                = var.region
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  port_range            = "80"
  target                = google_compute_region_target_http_proxy.default.id
  ip_address            = google_compute_address.lb_ip.id
  network               = data.google_compute_network.vpc.id
}
