# SCIM 2.0 Server for API-Only Entitlements Demo

This directory contains Terraform infrastructure to deploy a custom SCIM 2.0 server that demonstrates **API-only entitlements** in Okta Identity Governance.

## What is This?

This SCIM server simulates a **cloud application with custom roles/entitlements** that:
- Are NOT mapped to application resources in Okta
- Exist purely as API-level permissions
- Can be managed through Okta's Identity Governance features
- Demonstrate real-world scenarios where entitlements don't map 1:1 with app resources

### Real-World Use Cases

1. **Custom SaaS Applications** - Your proprietary app with unique role structures
2. **API-Level Permissions** - Roles that control API access, not UI features
3. **Entitlement Bundles** - Composite permissions that combine multiple low-level roles
4. **Non-Standard Provisioning** - Applications that don't fit Okta's standard app templates

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Okta Tenant                           │
│                                                             │
│  ┌──────────────────┐        ┌───────────────────────┐    │
│  │ SCIM 2.0 App     │        │ Identity Governance   │    │
│  │ (OPP enabled)    │◄───────┤ - Entitlement Bundles │    │
│  │                  │        │ - Access Reviews      │    │
│  └────────┬─────────┘        └───────────────────────┘    │
│           │                                                 │
│           │ SCIM 2.0 Protocol (HTTPS)                     │
└───────────┼─────────────────────────────────────────────────┘
            │
            │ Internet
            │
┌───────────▼─────────────────────────────────────────────────┐
│                    AWS Infrastructure                       │
│                                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  EC2 Instance (Ubuntu 22.04)                       │    │
│  │                                                     │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │  Caddy (Reverse Proxy + Let's Encrypt SSL)  │  │    │
│  │  │            https://scim.yourdomain.com       │  │    │
│  │  └────────────────┬─────────────────────────────┘  │    │
│  │                   │                                 │    │
│  │                   ▼                                 │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │  Flask SCIM Server (Python)                  │  │    │
│  │  │  - SCIM 2.0 endpoints (/scim/v2/Users)      │  │    │
│  │  │  - Custom entitlements/roles                 │  │    │
│  │  │  - In-memory user database                   │  │    │
│  │  │  - Web dashboard (/)                         │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  Route53 DNS: scim.yourdomain.com → Elastic IP             │
│  Security Group: SSH (optional), HTTP, HTTPS               │
└─────────────────────────────────────────────────────────────┘
```

## What Gets Created

### AWS Resources

1. **EC2 Instance** (t3.micro by default)
   - Ubuntu 22.04 LTS
   - Automatic HTTPS via Caddy + Let's Encrypt
   - Systemd service for SCIM server
   - IMDSv2 enabled for security

2. **Elastic IP** - Stable public IP address

3. **Route53 DNS Record** - Points your domain to the server

4. **Security Group**
   - Port 22: SSH (optional, only if ssh_key_name provided)
   - Port 80: HTTP (redirects to HTTPS)
   - Port 443: HTTPS (SCIM API + dashboard)

5. **IAM Role + Instance Profile**
   - SSM access for management (no SSH keys required)
   - CloudWatch Logs (optional)

6. **CloudWatch Log Group** (optional)

### Application Components

1. **Flask SCIM Server** (`demo_scim_server.py`)
   - SCIM 2.0 compliant API
   - Bearer token OR HTTP Basic authentication
   - Enhanced logging for troubleshooting
   - Web dashboard at `https://scim.yourdomain.com/`

2. **Custom Entitlements/Roles** (5 default roles)
   - Administrator - Full system access
   - Standard User - Basic access
   - Read Only - View only access
   - Support Agent - Customer support access
   - Billing Manager - Billing and payment access

## Prerequisites

### Required

- ✅ **AWS Account** with credentials configured
- ✅ **Route53 Hosted Zone** for your domain
- ✅ **Domain Name** for the SCIM server (e.g., `scim.demo-myorg.com`)
- ✅ **Terraform** >= 1.6.0
- ✅ **Okta Org** with OIG features enabled

### Optional

- SSH key pair in AWS (for direct server access)
- CloudWatch enabled for log aggregation

## Network Configuration

The SCIM server supports flexible network deployment options:

### Default Configuration (Simplest)

By default, the server deploys to the **default VPC** with an **auto-created security group**:
- ✅ No VPC/subnet configuration needed
- ✅ Security group created automatically
- ✅ HTTPS open to all (0.0.0.0/0)
- ✅ SSH optional (controlled by `ssh_key_name`)

**Perfect for:** Demos, testing, proof-of-concepts

### Custom VPC/Subnet (Recommended for Production)

Deploy into your existing VPC and subnet:

```hcl
# terraform.tfvars
vpc_id    = "vpc-1234567890abcdef"
subnet_id = "subnet-public-1a"  # Can be public or private (with NAT)
```

**Benefits:**
- ✅ Network isolation
- ✅ Private subnet support (requires NAT gateway)
- ✅ Integration with existing infrastructure
- ✅ VPC flow logs and monitoring

### Use Existing Security Group (Maximum Control)

Use your own security group with custom rules:

```hcl
# terraform.tfvars
use_existing_security_group = true
security_group_id          = "sg-1234567890abcdef"
```

**Your security group must allow:**
- **Inbound 443 (HTTPS)** - From Okta IP ranges + your network
- **Inbound 80 (HTTP)** - For Let's Encrypt validation (can be temporary)
- **Outbound ALL** - For package downloads and Let's Encrypt

**Perfect for:** Compliance requirements, pre-approved security groups, shared infrastructure

### Restrict HTTPS Access (Security Best Practice)

Limit HTTPS access to specific CIDR blocks (only when creating security group):

```hcl
# terraform.tfvars
allowed_https_cidr = [
  # Okta IP ranges (get latest from Okta docs)
  "52.23.120.0/21",      # US East
  "52.88.128.0/21",      # US West
  "3.120.0.0/14",        # EMEA
  # Your corporate network for dashboard access
  "203.0.113.0/24"
]
```

**Get Okta IP ranges:** https://help.okta.com/oie/en-us/content/topics/security/ip-address-allowlisting.htm

### Network Configuration Examples

#### Example 1: Default (Quick Start)

```hcl
# No network configuration needed - uses defaults
domain_name     = "scim.demo-myorg.com"
route53_zone_id = "Z1234567890ABC"
scim_auth_token = "your-token"
```

#### Example 2: Custom VPC with Restricted HTTPS

```hcl
# Deploy in specific VPC with HTTPS restrictions
vpc_id    = "vpc-1234567890abcdef"
subnet_id = "subnet-public-1a"

allowed_https_cidr = [
  "52.23.120.0/21",    # Okta
  "10.0.0.0/8"         # Your private network
]
```

#### Example 3: Use Existing Security Group

```hcl
# Use pre-approved security group
use_existing_security_group = true
security_group_id          = "sg-approved-scim"
vpc_id                     = "vpc-1234567890abcdef"
subnet_id                  = "subnet-dmz-1a"
```

#### Example 4: Private Subnet with NAT

```hcl
# Deploy in private subnet (no public IP)
vpc_id    = "vpc-1234567890abcdef"
subnet_id = "subnet-private-1a"  # Must have NAT gateway route

# Still need Elastic IP for Route53, but instance has no public IP
# Instance routes outbound through NAT
```

**Note:** Elastic IP is still created for Route53 DNS, but the instance itself can be in a private subnet.

## Deployment Options

You have two options for deploying the SCIM server:

### Option A: GitHub Actions Workflow (Recommended)

**Best for:** GitOps workflow, team collaboration, environment protection

Uses GitHub Environment secrets instead of local terraform.tfvars files.

#### Setup GitHub Environment Secrets

1. Navigate to your repository **Settings → Environments**
2. Select your environment (e.g., `MyOrg`)
3. Add the following secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SCIM_AUTH_TOKEN` | Bearer token for SCIM auth | `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `AWS_ROLE_ARN` | AWS OIDC role ARN | `arn:aws:iam::123456789012:role/GitHubActions-OktaTerraform` |

#### Deploy via GitHub Actions

```bash
# Trigger deployment workflow
gh workflow run deploy-scim-server.yml \
  -f environment=myorg \
  -f domain_name=scim.demo-myorg.example.com \
  -f route53_zone_id=Z1234567890ABC \
  -f instance_type=t3.micro \
  -f action=plan

# Review plan in workflow summary
# Then apply
gh workflow run deploy-scim-server.yml \
  -f environment=myorg \
  -f domain_name=scim.demo-myorg.example.com \
  -f route53_zone_id=Z1234567890ABC \
  -f instance_type=t3.micro \
  -f action=apply
```

**Benefits:**
- ✅ Secrets managed in GitHub (not in local files)
- ✅ Environment protection with approval gates
- ✅ Audit trail of all deployments
- ✅ AWS OIDC authentication (no long-lived credentials)
- ✅ Automated next-step instructions in workflow summary

---

### Option B: Manual Terraform Deployment

**Best for:** Local development, testing, one-time demos

Uses local terraform.tfvars file with secrets.

#### 1. Configure Variables

Create `terraform.tfvars` in this directory:

```hcl
# Required
domain_name      = "scim.demo-myorg.com"
route53_zone_id  = "Z1234567890ABC"  # Your Route53 zone ID
scim_auth_token  = "your-secure-token-here"  # Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'

# Optional
aws_region       = "us-east-1"
environment      = "myorg"
instance_type    = "t3.micro"
ssh_key_name     = "my-ec2-key"  # Leave empty to disable SSH
scim_basic_pass  = "basic-auth-password"  # Leave empty for Bearer-only auth

# CloudWatch Logs
enable_cloudwatch_logs = true
log_retention_days     = 7
```

#### 2. Generate Secure Tokens

```bash
# Generate SCIM Bearer token
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'

# Generate Basic Auth password (optional)
python3 -c 'import secrets; print(secrets.token_urlsafe(24))'
```

#### 3. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review plan
terraform plan

# Deploy (takes 5-10 minutes)
terraform apply

# View outputs
terraform output
```

#### 4. Wait for Server Initialization

The server takes **5-10 minutes** to fully initialize:
1. EC2 instance boots
2. System packages update
3. Caddy installs and provisions SSL certificate (Let's Encrypt)
4. Python dependencies install
5. SCIM server starts

**Check status:**
```bash
# Health check
curl https://scim.yourdomain.com/health

# Or use SSM Session Manager
aws ssm start-session --target $(terraform output -raw instance_id) --region us-east-1

# Once connected:
scim-status    # Check services
scim-logs      # View live logs
```

#### 5. Configure Okta SCIM App

**You have two options for creating and configuring the Okta SCIM application:**

- **Option A: Automated (Terraform + Python)** - Recommended for GitOps workflow
- **Option B: Manual (Okta Admin Console)** - Direct configuration via UI

---

##### Option A: Automated Configuration (Terraform + Python)

**Step 1: Create Okta App with Terraform**

1. Navigate to Okta Terraform directory:
   ```bash
   cd ../../terraform
   ```

2. Ensure SCIM server is deployed and state is available:
   ```bash
   cd ../infrastructure/scim-server
   terraform output scim_base_url
   # Should show: https://scim.yourdomain.com/scim/v2
   cd ../../terraform
   ```

3. The `scim_app.tf` file will automatically:
   - Read SCIM server outputs via data source
   - Create Okta application
   - Output configuration command

4. Apply Terraform (if not already done):
   ```bash
   terraform init
   terraform apply
   # Review plan and approve
   ```

5. Note the app ID from outputs:
   ```bash
   terraform output scim_app_id
   # Example: 0oa1b2c3d4e5f6g7h8i9
   ```

**Step 2: Configure SCIM Connection with Python**

The Okta Terraform provider cannot configure SCIM connection settings (API limitation).
Complete the configuration using the Python script:

```bash
# Get SCIM credentials from infrastructure state
cd ../infrastructure/scim-server
SCIM_URL=$(terraform output -raw scim_base_url)
SCIM_TOKEN=$(terraform output -json okta_configuration | jq -r '.header_auth_token')

# Run configuration script
cd ../../terraform
python3 ../../scripts/configure_scim_app.py \
  --app-id $(terraform output -raw scim_app_id) \
  --scim-url "$SCIM_URL" \
  --scim-token "$SCIM_TOKEN" \
  --test-connection
```

The script will:
- ✅ Enable SCIM provisioning for the app
- ✅ Configure SCIM connection (base URL, authentication)
- ✅ Test the connection
- ✅ Enable provisioning features (create, update, deactivate users)

**Dry Run Mode** (preview changes without applying):
```bash
python3 ../../scripts/configure_scim_app.py \
  --app-id $(terraform output -raw scim_app_id) \
  --scim-url "$SCIM_URL" \
  --scim-token "$SCIM_TOKEN" \
  --dry-run
```

**Using Basic Auth Instead** (if configured in SCIM server):
```bash
SCIM_USER=$(terraform output -json okta_configuration | jq -r '.basic_auth_username')
SCIM_PASS=$(terraform output -json okta_configuration | jq -r '.basic_auth_password')

python3 ../../scripts/configure_scim_app.py \
  --app-id $(terraform output -raw scim_app_id) \
  --scim-url "$SCIM_URL" \
  --scim-user "$SCIM_USER" \
  --scim-pass "$SCIM_PASS" \
  --auth-mode basic \
  --test-connection
```

**Troubleshooting Automated Configuration:**

If the Python script fails (some API endpoints may not be available for all app types):
1. The script will provide manual configuration instructions
2. Fall back to Option B (Manual Configuration) below
3. See `docs/SCIM_OKTA_AUTOMATION.md` for detailed troubleshooting

---

##### Option B: Manual Configuration (Okta Admin Console)

**Using Bearer Token Authentication (Recommended)**

1. In Okta Admin Console: **Applications → Applications**
2. Click **Browse App Catalog**
3. Search for **"SCIM 2.0 Test App (Header Auth)"**
4. Click **Add integration**
5. Configure **General Settings**:
   - Application label: `SCIM Entitlements Demo`
6. Click **Done**
7. Go to **Provisioning** tab → **Configure API Integration**
8. Check **Enable API integration**
9. Configure:
   - **SCIM Base URL**: `https://scim.yourdomain.com/scim/v2`
   - **Unique identifier field**: `userName`
   - **Authentication**: HTTP Header
   - **Authorization**: `Bearer YOUR_TOKEN_HERE` (from terraform.tfvars)
10. Click **Test API Credentials**
11. Enable provisioning features:
    - ✅ Create Users
    - ✅ Update User Attributes
    - ✅ Deactivate Users
    - ✅ Sync Password (optional)

##### Option C: Basic Authentication

1. Search for **"SCIM 2.0 Test App (Basic Auth)"**
2. Follow same steps but use:
   - **Username**: Value from `scim_basic_user` variable
   - **Password**: Value from `scim_basic_pass` variable

#### 6. Test Provisioning

1. **Assign Users** to the SCIM app in Okta
2. **View Dashboard**: `https://scim.yourdomain.com/`
3. **Check Logs**:
   ```bash
   # Via SSM
   aws ssm start-session --target $(terraform output -raw instance_id)
   scim-logs

   # Via SSH (if configured)
   ssh ubuntu@$(terraform output -raw public_ip)
   journalctl -u scim-demo -f
   ```

## Terraform Outputs

After deployment, Terraform provides these outputs:

### Infrastructure
- `instance_id` - EC2 instance ID
- `public_ip` - Server public IP address
- `domain_name` - FQDN for SCIM server
- `aws_region` - AWS region
- `vpc_id` - VPC ID (or "default VPC")
- `subnet_id` - Subnet ID (or "default subnet")
- `security_group_id` - Security group ID (created or existing)
- `security_group_created` - Whether a new security group was created

### URLs
- `dashboard_url` - Web dashboard URL
- `scim_base_url` - SCIM Base URL for Okta config
- `scim_health_url` - Health check endpoint

### Access
- `ssh_command` - SSH connection command (if enabled)
- `ssm_command` - AWS Systems Manager connection command
- `cloudwatch_console_url` - CloudWatch logs URL (if enabled)

### Okta Configuration
- `okta_configuration` - **SENSITIVE** - Complete Okta setup values

View outputs:
```bash
# All outputs
terraform output

# Specific output
terraform output dashboard_url

# Sensitive output
terraform output okta_configuration
```

## Variables Reference

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `domain_name` | string | ✅ | - | FQDN for SCIM server |
| `route53_zone_id` | string | ✅ | - | Route53 hosted zone ID |
| `scim_auth_token` | string | ✅ | - | Bearer token (min 32 chars) |
| `aws_region` | string | | `us-east-1` | AWS region |
| `environment` | string | | `myorg` | Environment name |
| `instance_type` | string | | `t3.micro` | EC2 instance type |
| `ssh_key_name` | string | | `""` | SSH key pair name (empty = disabled) |
| `allowed_ssh_cidr` | list(string) | | `["0.0.0.0/0"]` | Allowed SSH CIDRs |
| `scim_basic_user` | string | | `okta_scim_user` | Basic auth username |
| `scim_basic_pass` | string | | `""` | Basic auth password (empty = disabled) |
| `enable_cloudwatch_logs` | bool | | `true` | Enable CloudWatch Logs |
| `log_retention_days` | number | | `7` | CloudWatch log retention |
| `root_volume_size` | number | | `8` | Root EBS volume size (GB) |
| `github_repo` | string | | `joevanhorn/okta-terraform-demo-template` | Source code repository |
| `scim_server_path` | string | | `main/environments/myorg/infrastructure/scim-server` | Path to SCIM server code |
| `entitlements_file` | string | | `"entitlements.json"` | Path to entitlements JSON file (e.g., "examples/entitlements-salesforce.json") |
| `custom_entitlements` | string | | `""` | **DEPRECATED:** Use `entitlements_file` instead |
| **Network Configuration** | | | | |
| `vpc_id` | string | | `""` | VPC ID (empty = default VPC) |
| `subnet_id` | string | | `""` | Subnet ID (empty = default subnet) |
| `use_existing_security_group` | bool | | `false` | Use existing security group |
| `security_group_id` | string | | `""` | Existing security group ID |
| `allowed_https_cidr` | list(string) | | `["0.0.0.0/0"]` | Allowed HTTPS CIDRs |
| **Additional** | | | | |
| `tags` | map(string) | | `{}` | Additional resource tags |

## Custom Entitlements

### Overview

The SCIM server loads entitlements/roles from a JSON configuration file, making it easy to customize the application's permission model without modifying code. This allows you to demonstrate different application scenarios for prospects.

### Default Entitlements

By default, the server loads `entitlements.json` which contains 5 standard roles:
- **Administrator** - Full system access
- **Standard User** - Basic access
- **Read Only** - View only access
- **Support Agent** - Customer support access
- **Billing Manager** - Billing and payment access

### Using Example Templates

The repository includes pre-built templates for common applications:

**Salesforce Roles** (`examples/entitlements-salesforce.json`):
- System Administrator, Sales Manager, Sales Representative, Marketing User, Service Agent, Read Only User

**AWS IAM Roles** (`examples/entitlements-aws.json`):
- AdministratorAccess, PowerUserAccess, DeveloperAccess, ReadOnlyAccess, BillingAccess, SecurityAudit, NetworkAdministrator

**Generic Application** (`examples/entitlements-generic.json`):
- Owner, Administrator, Manager, Editor, Contributor, Viewer, Guest

### Deployment with Custom Entitlements

**Option 1: GitHub Actions Workflow (Recommended)**

Use the `entitlements_file` input when deploying:

```bash
gh workflow run deploy-scim-server.yml \
  -f environment=myorg \
  -f domain_name=scim.demo-myorg.example.com \
  -f route53_zone_id=Z1234567890ABC \
  -f entitlements_file=examples/entitlements-salesforce.json \
  -f action=apply
```

**Option 2: Terraform Variables**

Set the variable in your deployment:

```hcl
# terraform.tfvars
entitlements_file = "examples/entitlements-aws.json"
```

Or via command line:

```bash
terraform apply -var="entitlements_file=examples/entitlements-generic.json"
```

### Creating Custom Entitlements

Create a new JSON file in the repository:

```json
{
  "entitlements": [
    {
      "id": "role_data_analyst",
      "name": "Data Analyst",
      "description": "Access to analytics dashboard",
      "permissions": ["read", "analytics", "reports", "export_data"]
    },
    {
      "id": "role_developer",
      "name": "Developer",
      "description": "Development environment access",
      "permissions": ["read", "write", "deploy", "logs", "debug"]
    }
  ]
}
```

Save to: `environments/myorg/infrastructure/scim-server/custom/my-app-entitlements.json`

Then deploy with:

```bash
gh workflow run deploy-scim-server.yml \
  -f entitlements_file=custom/my-app-entitlements.json \
  -f action=apply
```

### Entitlement JSON Schema

Each entitlement object requires:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (e.g., `role_admin`) |
| `name` | string | Yes | Display name shown in dashboard |
| `description` | string | Yes | Description of the role's purpose |
| `permissions` | array | Yes | List of permission strings |

**Important:** The `id` field is used as the SCIM role value that Okta will provision.

## Monitoring and Troubleshooting

### Health Checks

```bash
# API health
curl https://scim.yourdomain.com/health

# Should return:
# {
#   "status": "healthy",
#   "service": "SCIM Entitlements Demo",
#   "users": 0,
#   "active_users": 0,
#   "roles": 5,
#   "timestamp": "2025-01-13T12:00:00Z"
# }
```

### View Logs

**Via SSM Session Manager (recommended):**
```bash
# Connect to instance
aws ssm start-session --target $(terraform output -raw instance_id) --region us-east-1

# Check status
scim-status

# View live logs
scim-logs

# Check specific services
systemctl status scim-demo
systemctl status caddy
```

**Via SSH (if enabled):**
```bash
ssh ubuntu@$(terraform output -raw public_ip)

# Setup logs
tail -f /var/log/user-data.log

# SCIM server logs
journalctl -u scim-demo -f

# Caddy logs
tail -f /var/log/caddy/access.log
```

### Common Issues

#### 1. SSL Certificate Not Provisioning

**Symptom:** HTTPS not working, browser shows security warning

**Cause:** Let's Encrypt can't verify domain ownership

**Solution:**
1. Verify DNS: `dig scim.yourdomain.com` should return Elastic IP
2. Check Route53 record created: `terraform state show aws_route53_record.scim_server`
3. Wait 5-10 minutes for DNS propagation
4. Check Caddy logs: `journalctl -u caddy -n 100`

#### 2. SCIM Server Not Starting

**Symptom:** Health check fails, returns 502 Bad Gateway

**Cause:** Python dependencies failed to install or server crashed

**Solution:**
1. Check server logs: `journalctl -u scim-demo -n 100`
2. Verify Python installed: `python3 --version`
3. Check Flask installed: `pip3 list | grep Flask`
4. Review setup log: `tail -200 /var/log/user-data.log`

#### 3. Okta Test Connection Fails

**Symptom:** "Unable to connect to SCIM server" error in Okta

**Causes & Solutions:**
- **Wrong URL**: Must be `https://scim.yourdomain.com/scim/v2` (with `/scim/v2`)
- **Wrong token**: Check `terraform output okta_configuration` for correct token
- **SSL issue**: Verify certificate: `curl -v https://scim.yourdomain.com/health`
- **Firewall**: Security group allows 0.0.0.0/0 on port 443

#### 4. Users Not Provisioning

**Symptom:** Users assigned in Okta but not appearing in SCIM server

**Solution:**
1. Check Okta provisioning log: Admin Console → Applications → [Your App] → Provisioning → Integration
2. View SCIM server logs: `scim-logs`
3. Check authentication: Look for 401 errors
4. Verify user filter matching: SCIM server logs show username matching patterns

## Cost Estimate

### AWS Costs (Monthly)

- **EC2 t3.micro**: ~$7.50/month (730 hours)
- **Elastic IP**: $3.65/month (if not attached to running instance)
- **Route53**: $0.50/month (hosted zone) + $0.40 for queries
- **Data Transfer**: Minimal (<$1/month for demo usage)

**Total**: ~$12-15/month

### Cost Optimization

- Use **t3.micro** for demo (included in AWS Free Tier for 12 months)
- Enable **CloudWatch** only when debugging
- **Delete** when not in use: `terraform destroy`
- Use **SSM Session Manager** instead of SSH (no SSH key management)

## Security Considerations

### Implemented

✅ **HTTPS Only** - Automatic SSL via Let's Encrypt
✅ **IMDSv2 Required** - Prevents SSRF attacks
✅ **Encrypted EBS** - Root volume encrypted at rest
✅ **SSM Access** - No SSH keys required
✅ **Security Headers** - HSTS, X-Frame-Options, etc.
✅ **Secure Tokens** - 32+ character random tokens

### Recommendations for Production

⚠️ **Restrict SSH CIDR** - Change `allowed_ssh_cidr` to your IP only
⚠️ **Use Secrets Manager** - Store tokens in AWS Secrets Manager
⚠️ **Enable VPC** - Deploy in private subnet with Application Load Balancer
⚠️ **Add WAF** - AWS WAF for additional protection
⚠️ **Rotate Tokens** - Regularly rotate authentication tokens
⚠️ **Enable MFA** - For AWS account and Okta admin access
⚠️ **Monitoring** - Enable CloudWatch alarms for unusual activity

## Cleanup

To remove all resources:

```bash
# Destroy infrastructure
terraform destroy

# Confirm deletion
# Type 'yes' when prompted
```

**Note:** Route53 hosted zone is NOT destroyed (managed separately)

## File Structure

```
environments/myorg/infrastructure/scim-server/
├── provider.tf              # AWS provider and backend config
├── variables.tf             # Input variables with validation
├── main.tf                  # Infrastructure resources
├── outputs.tf               # Output values
├── user-data.sh             # EC2 initialization script
├── demo_scim_server.py      # Flask SCIM 2.0 server application
├── requirements.txt         # Python dependencies
├── .gitignore               # Ignore sensitive files
└── README.md                # This file
```

## Integration with Okta Identity Governance

Once the SCIM server is provisioned and configured in Okta:

### 1. Create Entitlement Bundles

In `environments/myorg/terraform/oig_entitlements.tf`:

```hcl
resource "okta_entitlement_bundle" "admin_bundle" {
  name        = "SCIM Demo - Administrator Access"
  description = "Full admin access to SCIM demo application"
  status      = "ACTIVE"
}

# Link bundle to SCIM app entitlements
resource "okta_entitlement" "scim_admin_role" {
  app_id          = okta_app_oauth.scim_demo.id
  entitlement_id  = "role_admin"  # Matches SCIM server role ID
  bundle_id       = okta_entitlement_bundle.admin_bundle.id
}
```

### 2. Create Access Review Campaigns

```hcl
resource "okta_access_review_campaign" "scim_quarterly_review" {
  name        = "SCIM Demo - Quarterly Access Review"
  description = "Review administrator access to SCIM demo app"
  status      = "ACTIVE"

  resources {
    bundle_id = okta_entitlement_bundle.admin_bundle.id
  }

  schedule {
    frequency = "QUARTERLY"
    # ... configuration
  }
}
```

### 3. Assign Resource Owners

Use Python scripts in `scripts/apply_resource_owners.py`

## Development and Testing

### Local Testing (Without AWS)

You can run the SCIM server locally for testing:

```bash
# Install dependencies
pip3 install -r requirements.txt

# Set environment variables
export SCIM_AUTH_TOKEN="test-token"
export SCIM_BASIC_USER="okta"
export SCIM_BASIC_PASS="password123"

# Run server
python3 demo_scim_server.py

# Access at http://localhost:5000
```

### Test SCIM Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Service Provider Config
curl http://localhost:5000/scim/v2/ServiceProviderConfig

# Create user
curl -X POST http://localhost:5000/scim/v2/Users \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "userName": "john.doe@example.com",
    "name": {"givenName": "John", "familyName": "Doe"},
    "emails": [{"value": "john.doe@example.com", "primary": true}],
    "active": true,
    "roles": [
      {"value": "role_admin", "display": "Administrator"}
    ]
  }'

# List users
curl http://localhost:5000/scim/v2/Users \
  -H "Authorization: Bearer test-token"
```

## Support and Documentation

- **Repository**: https://github.com/joevanhorn/okta-terraform-demo-template
- **SCIM 2.0 Spec**: https://datatracker.ietf.org/doc/html/rfc7644
- **Okta SCIM Docs**: https://developer.okta.com/docs/concepts/scim/
- **Okta OIG Docs**: https://help.okta.com/oie/en-us/content/topics/identity-governance/iga-main.htm

## License

MIT License - See repository LICENSE file

---

**Questions?** See the main repository README or create an issue on GitHub.
