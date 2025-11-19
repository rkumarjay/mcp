# External HTTPS Load Balancer for Cloud Run

This Terraform configuration creates an **external** Application Load Balancer with HTTPS protocol for Cloud Run.

## Configuration

- **Type**: Application Load Balancer (Layer 7)
- **Access**: External (accessible from internet)
- **Protocol**: HTTPS
- **Backend Services**: 1 regional backend service
- **Network Endpoint Groups**: 1 serverless NEG (Cloud Run)
- **SSL Policy**: GCP Default (MODERN profile, TLS 1.2+)
- **Global Access**: Disabled
- **Certificate**: Self-signed certificate (lb-cert)

## Features

✅ External load balancer (internet-accessible)
✅ HTTPS protocol with SSL/TLS
✅ Regional backend service
✅ Serverless NEG pointing to Cloud Run `test-cr-01`
✅ Self-signed certificate for testing
✅ GCP default SSL policy
✅ Regional load balancer

## Architecture

```
VPC (custom-vpc)
  └─> Internal Load Balancer (HTTPS)
       ├─> SSL Certificate (lb-cert)
       ├─> SSL Policy (MODERN, TLS 1.2+)
       ├─> Regional Backend Service
       │    └─> Serverless NEG
       │         └─> Cloud Run: test-cr-01
       └─> Internal IP in custom-subnet
```

## Prerequisites

1. Cloud Run service `test-cr-01` already deployed
2. VPC network `custom-vpc` exists
3. Subnet `custom-subnet` in us-central1

## Setup

1. **Create terraform.tfvars:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Initialize and apply:**
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

## Accessing the Load Balancer

The load balancer is **externally accessible** from anywhere on the internet:

### From your laptop:
```bash
# Using the external IP
curl -k https://EXTERNAL_IP

# From browser (accept self-signed certificate warning)
https://EXTERNAL_IP
```

### From PowerShell:
```powershell
Invoke-WebRequest -Uri "https://EXTERNAL_IP" -SkipCertificateCheck
```

## Certificate

The configuration includes a self-signed certificate embedded in the Terraform code. For production:
1. Use a proper CA-signed certificate
2. Or use Google-managed certificates with Cloud DNS

## Cleanup

```bash
terraform destroy
```

## Important Notes

- Load balancer is **accessible from the internet**
- Certificate is self-signed (browser will show security warning)
- Use `-k` flag with curl to skip certificate validation
- Backend service uses HTTPS protocol
- Regional load balancer in us-central1
- Access from your laptop via the external IP address
