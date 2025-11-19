variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "test-cr-01"
}

variable "vpc_name" {
  description = "VPC network name"
  type        = string
  default     = "custom-vpc"
}

variable "subnet_name" {
  description = "Subnet name"
  type        = string
  default     = "custom-subnet"
}

variable "lb_name" {
  description = "Load balancer name"
  type        = string
  default     = "internal-lb"
}
