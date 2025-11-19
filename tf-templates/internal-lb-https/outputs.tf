output "load_balancer_ip" {
  description = "Internal IP address of the load balancer"
  value       = google_compute_address.lb_ip.address
}

output "load_balancer_url" {
  description = "Internal HTTPS URL"
  value       = "https://${var.domain_name}"
}

output "load_balancer_ip_url" {
  description = "Internal HTTPS URL using IP"
  value       = "https://${google_compute_address.lb_ip.address}"
}

output "backend_service_name" {
  description = "Name of the regional backend service"
  value       = google_compute_region_backend_service.default.name
}

output "neg_name" {
  description = "Name of the serverless NEG"
  value       = google_compute_region_network_endpoint_group.cloudrun_neg.name
}

output "ssl_certificate_name" {
  description = "Name of the SSL certificate"
  value       = google_compute_region_ssl_certificate.default.name
}

output "ssl_policy_name" {
  description = "Name of the SSL policy"
  value       = google_compute_ssl_policy.default.name
}

output "dns_zone_name" {
  description = "Name of the private DNS zone"
  value       = google_dns_managed_zone.private_zone.name
}

output "dns_record" {
  description = "DNS record for the load balancer"
  value       = "${var.domain_name} -> ${google_compute_address.lb_ip.address}"
}

output "access_instruction" {
  description = "How to access the load balancer"
  value       = <<-EOT
    Access from within VPC:
    - URL: https://${var.domain_name}
    - IP: https://${google_compute_address.lb_ip.address}
    
    Access from outside VPC:
    - Requires VPN or Cloud Interconnect connection to VPC
    - DNS resolution works only within VPC
    
    Test command (from VM in VPC):
    curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" https://${var.domain_name}
  EOT
}
