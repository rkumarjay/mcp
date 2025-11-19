output "load_balancer_ip" {
  description = "External IP address of the load balancer"
  value       = google_compute_address.lb_ip.address
}

output "load_balancer_url" {
  description = "External HTTP URL"
  value       = "http://${google_compute_address.lb_ip.address}"
}

output "backend_service_name" {
  description = "Name of the regional backend service"
  value       = google_compute_region_backend_service.default.name
}

output "neg_name" {
  description = "Name of the serverless NEG"
  value       = google_compute_region_network_endpoint_group.cloudrun_neg.name
}

# SSL certificate output (commented out for HTTP testing)
# output "ssl_certificate_name" {
#   description = "Name of the SSL certificate"
#   value       = google_compute_region_ssl_certificate.lb_cert.name
# }

# SSL policy output (commented out for HTTP testing)
# output "ssl_policy_name" {
#   description = "Name of the SSL policy"
#   value       = google_compute_ssl_policy.default.name
# }

output "access_instruction" {
  description = "How to access the load balancer"
  value       = "Access from anywhere: curl http://${google_compute_address.lb_ip.address}"
}
