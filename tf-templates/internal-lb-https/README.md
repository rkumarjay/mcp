# Internal HTTPS Load Balancer for Cloud Run

This Terraform configuration creates an **Internal HTTPS Application Load Balancer** for Cloud Run service with SSL/TLS certificate.

## Architecture

- **Load Balancer Type**: Regional Internal Application Load Balancer
- **Protocol**: HTTPS (port 443)
- **Backend**: Cloud Run service via Serverless NEG
- **SSL/TLS**: Custom certificate (provided)
- **DNS**: Private DNS zone for internal domain resolution
- **Network**: Internal (accessible only within VPC or via VPN)

## Components Created

1. **Serverless Network Endpoint Group (NEG)** - Connects to Cloud Run
2. **Regional Backend Service** - INTERNAL_MANAGED, HTTPS protocol
3. **SSL Certificate** - Uploaded from provided certificate files
4. **SSL Policy** - MODERN profile, TLS 1.2+
5. **Regional URL Map** - Routes traffic to backend
6. **Regional HTTPS Target Proxy** - Terminates SSL/TLS
7. **Internal IP Address** - Private IP in VPC subnet
8. **Forwarding Rule** - Listens on port 443
9. **Private DNS Zone** - For internal domain resolution
10. **DNS A Record** - Maps domain to internal IP

## Prerequisites

1. **VPC Network**: `custom-vpc` (already exists)
2. **Subnet**: `custom-subnet` in us-central1 (already exists)
3. **Cloud Run Service**: `test-cr-01` (already deployed)
4. **Certificate Files**: 
   - `certs/certificate.crt` - SSL certificate
   - `certs/private.key` - Private key

## Certificate Setup

Place your certificate files in the `certs/` directory:

```
internal-lb-https/
├── certs/
│   ├── certificate.crt    # Your SSL certificate
│   └── private.key        # Your private key
├── load-balancer.tf
├── provider.tf
├── variables.tf
├── outputs.tf
└── terraform.tfvars
```

## Configuration

1. Copy the example variables file:
   ```powershell
   Copy-Item terraform.tfvars.example terraform.tfvars
   ```

2. Update `terraform.tfvars` if needed (default values should work):
   ```hcl
   project_id            = "ai-10292025"
   region                = "us-central1"
   domain_name           = "ccs.rajesh.com"
   certificate_file      = "certs/certificate.crt"
   private_key_file      = "certs/private.key"
   ```

## Deployment

1. **Initialize Terraform**:
   ```powershell
   .\terraform.exe init
   ```

2. **Review the plan**:
   ```powershell
   .\terraform.exe plan
   ```

3. **Apply the configuration**:
   ```powershell
   .\terraform.exe apply
   ```

## Access

### From Within VPC

The load balancer is **internal only** - accessible from:
- VMs in the same VPC
- On-premises network via VPN or Cloud Interconnect
- Other VPCs via VPC peering

**Access via domain name**:
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" https://ccs.rajesh.com
```

**Access via IP address**:
```bash
# Get the internal IP from terraform output
INTERNAL_IP=$(terraform output -raw load_balancer_ip)

curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" https://$INTERNAL_IP
```

### From Outside VPC

To access from your laptop:
1. **Setup VPN**: Configure Cloud VPN to connect to the VPC
2. **DNS Configuration**: Add DNS entry to your local DNS or hosts file
3. **Access**: Use HTTPS with the domain name

## DNS Resolution

The private DNS zone (`rajesh.com`) is created automatically and only works within the VPC. The A record `ccs.rajesh.com` points to the internal load balancer IP.

## Key Differences from External Load Balancer

| Feature | Internal HTTPS LB | External HTTP LB |
|---------|------------------|------------------|
| Access | VPC-only | Internet-accessible |
| IP Type | INTERNAL | EXTERNAL |
| Protocol | HTTPS (443) | HTTP (80) |
| Certificate | Required | Optional |
| DNS | Private zone | Public DNS |
| Proxy Subnet | Not required | Required |
| Network/Subnet | Required in forwarding rule | Not required |

## Security

- SSL/TLS encryption for all traffic
- Certificate-based authentication
- Internal access only (no public exposure)
- Cloud Run IAM authentication still required
- Modern TLS policy (TLS 1.2+)

## Outputs

After deployment, you'll get:
- `load_balancer_ip` - Internal IP address
- `load_balancer_url` - HTTPS URL with domain name
- `dns_record` - DNS mapping information
- `access_instruction` - How to access the load balancer

## Notes

- The certificate files are referenced from the `certs/` directory
- Private DNS zone only works within the VPC
- For laptop access, you need VPN connectivity
- Cloud Run service still requires IAM authentication (Bearer token)
- Load balancer typically takes 5-10 minutes to become fully operational

## Cleanup

To destroy all resources:
```powershell
.\terraform.exe destroy
```
