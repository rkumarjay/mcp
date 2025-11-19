# Cloud Run Terraform Configuration

This Terraform configuration creates a Cloud Run service with VPC integration in Google Cloud Platform.

## Features

- **Service Name**: test-cr-01
- **Region**: us-central1 (default)
- **VPC Integration**: Routes all traffic through custom VPC
- **Authentication**: IAM authentication required (no public access)
- **Service Mesh**: None
- **Binary Authorization**: Disabled
- **VPC Access Connector**: Automatically created for VPC connectivity

## Prerequisites

1. Google Cloud SDK installed and configured
2. Terraform installed (version >= 1.0)
3. GCP project with billing enabled
4. Existing VPC network (`custom-vpc`) and subnet (`custom-subnet`)
5. Appropriate IAM permissions:
   - Cloud Run Admin
   - Compute Network Admin
   - VPC Access Admin
   - Service Usage Admin

## Setup

1. **Authenticate with GCP:**
   ```bash
   gcloud auth application-default login
   ```

2. **Set your project:**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Create terraform.tfvars:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
   
   Edit `terraform.tfvars` and set your project ID and other variables.

## Usage

1. **Initialize Terraform:**
   ```bash
   terraform init
   ```

2. **Review the plan:**
   ```bash
   terraform plan
   ```

3. **Apply the configuration:**
   ```bash
   terraform apply
   ```

4. **To destroy resources:**
   ```bash
   terraform destroy
   ```

## Resources Created

- **Cloud Run Service**: test-cr-01 with VPC connectivity
- **VPC Access Connector**: For routing Cloud Run traffic through VPC
- **API Enablement**: Cloud Run API and VPC Access API

## Configuration

### VPC Settings
- **VPC Connector IP Range**: 10.8.0.0/28 (automatically allocated)
- **Traffic Routing**: ALL_TRAFFIC routed through VPC
- **Egress**: All egress traffic goes through VPC

### Authentication
- **IAM Required**: Only authenticated users/service accounts with `roles/run.invoker` can access
- **No Public Access**: Service is not publicly accessible by default

### Scaling
- **Min Instances**: 0 (configurable)
- **Max Instances**: 10 (configurable)

### Resources
- **CPU**: 1 vCPU (configurable)
- **Memory**: 512Mi (configurable)

## Accessing the Service

Since IAM authentication is required, you need to authenticate your requests:

### Using gcloud
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  $(terraform output -raw service_url)
```

### Grant Access to Users
To allow specific users to invoke the service:
```bash
gcloud run services add-iam-policy-binding test-cr-01 \
  --region=us-central1 \
  --member="user:example@example.com" \
  --role="roles/run.invoker"
```

### Grant Access to Service Accounts
```bash
gcloud run services add-iam-policy-binding test-cr-01 \
  --region=us-central1 \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/run.invoker"
```

## Customization

Edit `variables.tf` or `terraform.tfvars` to customize:
- Container image
- CPU and memory allocation
- Scaling parameters
- VPC and subnet names
- Region

## Notes

- VPC Access Connector uses IP range 10.8.0.0/28 (must not conflict with existing subnets)
- Binary Authorization is disabled (can be enabled by uncommenting code in cloudrun.tf)
- Service Mesh is not configured
- All egress traffic from Cloud Run goes through the VPC
- The service requires authentication - no anonymous access allowed
