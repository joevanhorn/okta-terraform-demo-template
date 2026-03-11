# Okta Access Gateway Deployment Guide

Complete guide for deploying and managing Okta Access Gateway (OAG) with Infrastructure as Code.

## Overview

Okta Access Gateway is a reverse proxy that protects on-premises applications using header-based authentication, Kerberos tokens, and other legacy methods. This guide covers automated deployment and management using Terraform and Python scripts.

---

## Architecture

```
Internet → ALB (HTTPS) → OAG Appliance → Backend Apps
                ↓
        ACM Certificate
        (Let's Encrypt)
```

**Components:**
- **Application Load Balancer (ALB)**: Handles HTTPS termination and routing
- **ACM Certificate**: Free SSL/TLS certificate from AWS
- **OAG Virtual Appliance**: EC2 instance running OAG
- **Backend Applications**: Your protected on-premises apps

---

## Prerequisites

### Required

- [ ] AWS account with appropriate permissions
- [ ] Okta organization with OAG license
- [ ] Domain name for OAG (e.g., `oag.example.com`)
- [ ] Route53 hosted zone (or external DNS)

### Software

- Terraform >= 1.9.0
- Python >= 3.9
- AWS CLI configured
- OAG OVA image (download from Okta Admin Console)

---

## Deployment Steps

### Step 1: Import OAG OVA to AWS

Before deploying, import the OAG virtual appliance OVA to create an AMI:

```bash
# Download OAG OVA from Okta Admin Console
# Settings → Downloads → Access Gateway

# Create S3 bucket for import
aws s3 mb s3://oag-import-bucket

# Upload OVA
aws s3 cp oag-image.ova s3://oag-import-bucket/

# Create import task
aws ec2 import-image \
  --description "Okta Access Gateway" \
  --disk-containers file://import-containers.json

# Check import status
aws ec2 describe-import-image-tasks --import-task-ids import-ami-xxxxx
```

**import-containers.json:**
```json
[{
  "Description": "OAG Root Volume",
  "Format": "ova",
  "UserBucket": {
    "S3Bucket": "oag-import-bucket",
    "S3Key": "oag-image.ova"
  }
}]
```

Note the AMI ID when complete.

### Step 2: Configure Terraform Variables

Create `terraform.tfvars`:

```hcl
aws_region    = "us-east-1"
environment   = "production"
name_prefix   = "oag"

# OAG Instance
oag_ami_id       = "ami-xxxxxxxxx"  # From Step 1
oag_instance_type = "t3.medium"
key_pair_name    = "your-keypair"

# Domain Configuration
oag_domain       = "oag.example.com"
route53_zone_id  = "Z1234567890ABC"

# Security (restrict in production!)
admin_cidr_blocks = ["10.0.0.0/8"]  # Your corporate network
```

### Step 3: Deploy Infrastructure

```bash
cd environments/myorg/oag-infrastructure/terraform

terraform init
terraform plan
terraform apply
```

**What gets created:**
- VPC with public/private subnets
- NAT Gateway for outbound access
- Application Load Balancer with HTTPS
- ACM certificate (auto-validated via Route53)
- OAG EC2 instance
- Security groups

### Step 4: Initial OAG Configuration

After Terraform completes:

1. **Access Admin Console**:
   ```
   https://<oag-private-ip>:8443
   ```

2. **Complete Setup Wizard**:
   - Set admin password
   - Configure network settings
   - Connect to Okta IdP

3. **Enable API Access**:
   - Go to Settings → API
   - Enable API
   - Download client ID and private key

4. **Save Credentials**:
   ```bash
   mkdir -p ~/.oag
   # Save private key to ~/.oag/private_key.pem
   chmod 600 ~/.oag/private_key.pem
   ```

### Step 5: Configure GitHub Secrets

Add these secrets to your GitHub Environment:

| Secret | Description |
|--------|-------------|
| `OAG_HOSTNAME` | OAG public domain (e.g., `oag.example.com`) |
| `OAG_CLIENT_ID` | API client ID from OAG |
| `OAG_PRIVATE_KEY` | Private key PEM content |

---

## Managing Applications

### Using the CLI

```bash
# List applications
python scripts/manage_oag_apps.py \
  --config environments/myorg/config/oag_apps.json \
  --action list

# Deploy applications (dry run)
python scripts/manage_oag_apps.py \
  --config environments/myorg/config/oag_apps.json \
  --action deploy \
  --dry-run

# Deploy specific application
python scripts/manage_oag_apps.py \
  --config environments/myorg/config/oag_apps.json \
  --action deploy \
  --app "Legacy HR Portal"

# Show application details
python scripts/manage_oag_apps.py \
  --config environments/myorg/config/oag_apps.json \
  --action show \
  --app "Legacy HR Portal"
```

### Using GitHub Actions

```bash
# Deploy all applications
gh workflow run deploy-oag-app.yml \
  -f environment=MyOrg \
  -f dry_run=false

# Deploy specific application
gh workflow run deploy-oag-app.yml \
  -f environment=MyOrg \
  -f app_name="Legacy HR Portal" \
  -f dry_run=false
```

### Configuration File Format

```json
{
  "gateway": {
    "hostname": "oag.example.com",
    "client_id": "your_client_id",
    "private_key_path": "~/.oag/private_key.pem"
  },
  "applications": [
    {
      "label": "My App",
      "public_domain": "app.example.com",
      "protected_resources": [
        {
          "url": "https://backend:8443",
          "weight": 100
        }
      ],
      "attributes": [
        {
          "source": "IDP",
          "field": "login",
          "type": "Header",
          "name": "X-Remote-User"
        }
      ],
      "group": "App-Users",
      "policy": "Protected"
    }
  ]
}
```

---

## Header Attribute Mapping

### Common Patterns

| Okta Field | Header Name | Use Case |
|------------|-------------|----------|
| `login` | `X-Remote-User` | Username/UPN |
| `email` | `X-Remote-Email` | Email address |
| `firstName` | `X-Remote-FirstName` | First name |
| `lastName` | `X-Remote-LastName` | Last name |
| `department` | `X-User-Department` | Department |
| `title` | `X-User-Title` | Job title |

### Data Sources

- **IDP**: Attributes from Okta user profile
- **Static**: Fixed values
- **Expression**: Calculated values

---

## Load Balancing

Configure multiple backend servers with weighted load balancing:

```json
"protected_resources": [
  {
    "url": "https://server1.internal:8443",
    "weight": 70
  },
  {
    "url": "https://server2.internal:8443",
    "weight": 30
  }
]
```

### Health Checks

```json
"health_check": {
  "path": "/health",
  "method": "GET",
  "expected_status": 200,
  "interval": 10,
  "timeout": 3,
  "unhealthy_threshold": 3,
  "healthy_threshold": 2
}
```

---

## Security Considerations

### Production Recommendations

1. **Restrict Admin Access**: Limit `admin_cidr_blocks` to corporate networks
2. **Enable Deletion Protection**: Set `enable_deletion_protection = true`
3. **Use Private Subnets**: OAG should be in private subnet
4. **Rotate API Keys**: Regularly rotate OAG API credentials
5. **Monitor Logs**: Enable CloudWatch logging for ALB

### Certificate Management

ACM certificates auto-renew. For custom certificates:

```bash
# Upload certificate to ACM
aws acm import-certificate \
  --certificate file://cert.pem \
  --private-key file://key.pem \
  --certificate-chain file://chain.pem
```

---

## Troubleshooting

### Common Issues

**"401 Unauthorized" from OAG API**
- Verify client ID and private key
- Check token hasn't expired
- Ensure API is enabled in OAG Admin Console

**"502 Bad Gateway"**
- Check OAG instance is running
- Verify security group allows traffic from ALB
- Check OAG health in target group

**Headers not injected**
- Verify attributes are configured in application
- Check user is assigned to application in Okta
- Review OAG logs for errors

**Certificate validation failed**
- Verify DNS points to ALB
- Check Route53 zone ID is correct
- Wait for DNS propagation (up to 30 minutes)

### Viewing Logs

```bash
# Connect via SSM
aws ssm start-session --target <instance-id>

# View OAG logs
sudo tail -f /var/log/oag/access.log
sudo tail -f /var/log/oag/error.log
```

---

## Cost Estimation

| Resource | Monthly Cost (us-east-1) |
|----------|--------------------------|
| EC2 t3.medium | ~$30 |
| ALB | ~$20 |
| NAT Gateway | ~$45 |
| Data Transfer | Variable |
| **Total** | **~$100+** |

---

## Example: Demo Application

See `examples/oag-demo-app/` for a complete example including:
- Flask application displaying headers
- Docker configuration
- OAG application configuration
- Deployment instructions

---

## Related Documentation

- [OAG API Management](./OAG_API_MANAGEMENT.md)
- [OAG Demo App](../examples/oag-demo-app/README.md)
- [Okta Access Gateway Docs](https://help.okta.com/oag/en-us/content/topics/access-gateway/about-oag.htm)
- [AWS ACM](https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html)
