output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.default.name
}

output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.default.uri
}

output "service_location" {
  description = "Location of the Cloud Run service"
  value       = google_cloud_run_v2_service.default.location
}

output "vpc_connector_name" {
  description = "Name of the VPC Access Connector"
  value       = google_vpc_access_connector.connector.name
}

output "vpc_connector_id" {
  description = "ID of the VPC Access Connector"
  value       = google_vpc_access_connector.connector.id
}

output "service_status" {
  description = "Status of the Cloud Run service"
  value       = google_cloud_run_v2_service.default.terminal_condition
}
