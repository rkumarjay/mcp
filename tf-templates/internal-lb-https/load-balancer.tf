# Data sources to reference existing resources
data "google_compute_network" "vpc" {
  name = var.network_name
}

data "google_compute_subnetwork" "subnet" {
  name   = var.subnet_name
  region = var.region
}

data "google_cloud_run_v2_service" "cloudrun" {
  name     = var.cloudrun_service_name
  location = var.region
}

# Regional Network Endpoint Group for Cloud Run
resource "google_compute_region_network_endpoint_group" "cloudrun_neg" {
  name                  = "${var.lb_name}-neg"
  region                = var.region
  network_endpoint_type = "SERVERLESS"

  cloud_run {
    service = data.google_cloud_run_v2_service.cloudrun.name
  }
}

# Regional Backend Service (INTERNAL_MANAGED, HTTPS protocol)
resource "google_compute_region_backend_service" "default" {
  name                  = "${var.lb_name}-backend"
  region                = var.region
  load_balancing_scheme = "INTERNAL_MANAGED"
  protocol              = "HTTPS"

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

# SSL Certificate (using provided certificate files)
resource "google_compute_region_ssl_certificate" "default" {
  name_prefix = "${var.lb_name}-cert-"
  region      = var.region
  description = "SSL certificate for internal HTTPS load balancer - ${var.domain_name}"

  certificate = file("${path.module}/${var.certificate_file}")
  private_key = file("${path.module}/${var.private_key_file}")

  lifecycle {
    create_before_destroy = true
  }
}

# Regional URL Map
resource "google_compute_region_url_map" "default" {
  name                    = "${var.lb_name}-url-map"
  region                  = var.region
  default_service         = google_compute_region_backend_service.default.id
}

# SSL Policy (MODERN profile with TLS 1.2+)
resource "google_compute_ssl_policy" "default" {
  name            = "${var.lb_name}-ssl-policy"
  profile         = "MODERN"
  min_tls_version = "TLS_1_2"
}

# Regional HTTPS Target Proxy
resource "google_compute_region_target_https_proxy" "default" {
  name             = "${var.lb_name}-https-proxy"
  region           = var.region
  url_map          = google_compute_region_url_map.default.id
  ssl_certificates = [google_compute_region_ssl_certificate.default.id]
  ssl_policy       = google_compute_ssl_policy.default.id
}

# Reserve Internal IP Address
resource "google_compute_address" "lb_ip" {
  name         = "${var.lb_name}-ip"
  region       = var.region
  address_type = "INTERNAL"
  subnetwork   = data.google_compute_subnetwork.subnet.id
  purpose      = "GCE_ENDPOINT"
}

# Regional Forwarding Rule (Internal, HTTPS)
resource "google_compute_forwarding_rule" "https" {
  name                  = "${var.lb_name}-https-rule"
  region                = var.region
  ip_protocol           = "TCP"
  load_balancing_scheme = "INTERNAL_MANAGED"
  port_range            = "443"
  target                = google_compute_region_target_https_proxy.default.id
  ip_address            = google_compute_address.lb_ip.id
  network               = data.google_compute_network.vpc.id
  subnetwork            = data.google_compute_subnetwork.subnet.id
}

# Optional: Private DNS Zone for internal domain resolution
resource "google_dns_managed_zone" "private_zone" {
  name        = "${var.lb_name}-private-zone"
  dns_name    = "rajesh.com."
  description = "Private DNS zone for internal load balancer"
  
  visibility = "private"
  
  private_visibility_config {
    networks {
      network_url = data.google_compute_network.vpc.id
    }
  }
}

# DNS A Record pointing to internal LB IP
resource "google_dns_record_set" "lb_record" {
  name         = "${var.domain_name}."
  type         = "A"
  ttl          = 300
  managed_zone = google_dns_managed_zone.private_zone.name
  rrdatas      = [google_compute_address.lb_ip.address]
}
