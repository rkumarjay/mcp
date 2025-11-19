variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "lb_name" {
  description = "Load balancer name prefix"
  type        = string
  default     = "internal-lb-https"
}

variable "network_name" {
  description = "VPC network name"
  type        = string
  default     = "custom-vpc"
}

variable "subnet_name" {
  description = "Subnet name"
  type        = string
  default     = "custom-subnet"
}

variable "cloudrun_service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "test-cr-01"
}

variable "domain_name" {
  description = "Domain name for SSL certificate"
  type        = string
  default     = "ccs.rajesh.com"
}

variable "certificate_file" {
  description = "Path to SSL certificate file"
  type        = string
  default     = "certs/certificate.crt"
}

variable "private_key_file" {
  description = "Path to SSL private key file"
  type        = string
  default     = "certs/private.key"
}
