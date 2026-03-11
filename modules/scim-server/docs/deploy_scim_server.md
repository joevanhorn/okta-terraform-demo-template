# Prompt: Deploy Custom SCIM Server with Okta Integration

Use this prompt template to have an AI assistant generate a complete SCIM 2.0 server infrastructure with Okta integration.

---

## What This Deploys

A complete, working SCIM 2.0 server demonstration featuring:
- **AWS Infrastructure**: EC2 instance with automatic HTTPS (Let's Encrypt)
- **SCIM 2.0 Server**: Flask-based server with custom entitlements/roles
- **Okta Integration**: Automated provisioning from Okta to your custom app
- **Web Dashboard**: Visual interface to see provisioned users and roles
- **API-Only Entitlements**: Demonstrate custom roles that don't map to Okta app resources

**Perfect for demonstrating:**
- Custom SaaS application provisioning
- API-level permissions and roles
- Entitlement bundles with composite permissions
- Non-standard provisioning scenarios

---

## Prerequisites

Before using this prompt:

1. **AWS Account** with:
   - S3 backend configured (see `aws-backend/` directory)
   - Route53 hosted zone for your domain
   - AWS credentials configured

2. **Domain Name**:
   - You control a domain (e.g., `example.com`)
   - Route53 hosted zone exists for that domain
   - Subdomain for SCIM server (e.g., `scim.demo-myorg.example.com`)

3. **Okta Org** with:
   - OIG (Okta Identity Governance) features enabled (optional but recommended)
   - API token with `okta.apps.manage` scope

4. **Environment Variables** (for Python script):
   ```bash
   export OKTA_ORG_NAME="your-org"
   export OKTA_BASE_URL="okta.com"
   export OKTA_API_TOKEN="your-token"
   ```

---

## Step 1: Provide Context

Copy and paste the following context files to your AI assistant:

**Repository Structure:**
```
[Paste contents of: ai-assisted/context/repository_structure.md]
```

**Terraform Examples:**
```
[Paste contents of: ai-assisted/context/terraform_examples.md]
```

**Resource Guide:**
```
[Paste contents of: ai-assisted/context/okta_resource_guide.md]
```

---

## Step 2: Use This Prompt Template

Copy this template and fill in your specific requirements:

```
I need to deploy a custom SCIM 2.0 server with Okta integration using Terraform.
This will demonstrate API-only entitlements and custom provisioning.

Please generate THREE sets of Terraform configuration following the repository structure:

════════════════════════════════════════════════════════════════════════════
PART 1: SCIM Server Infrastructure (AWS)
════════════════════════════════════════════════════════════════════════════

Location: environments/myorg/infrastructure/scim-server/

Requirements:
- EC2 instance running Flask SCIM 2.0 server
- Automatic HTTPS with Let's Encrypt (via Caddy)
- Route53 DNS record
- Security groups (HTTP, HTTPS, optional SSH)
- Elastic IP for stable addressing

Configuration:
- Domain name: scim.demo-myorg.example.com
- Route53 zone ID: [Your Zone ID - get with: aws route53 list-hosted-zones]
- AWS region: us-east-1
- Instance type: t3.micro
- Generate secure tokens:
  - Bearer token: [Run: python3 -c 'import secrets; print(secrets.token_urlsafe(32))']
  - Basic auth password (optional): [Run: python3 -c 'import secrets; print(secrets.token_urlsafe(24))']

Custom Entitlements/Roles (5 defaults or specify custom):
- Administrator - Full system access
- Standard User - Basic application access
- Read Only - View-only access
- Support Agent - Customer support access
- Billing Admin - Financial/billing access

Network Configuration:
[Choose one:]
- Default VPC (simplest)
- Custom VPC: vpc-xxxxx, subnet-xxxxx
- Existing security group: sg-xxxxx
- Restrict HTTPS to specific CIDRs: [e.g., Okta IP ranges]

════════════════════════════════════════════════════════════════════════════
PART 2: Okta SCIM Application (Okta Terraform)
════════════════════════════════════════════════════════════════════════════

Location: environments/myorg/terraform/scim_app.tf

Requirements:
- Data source to read SCIM server state from S3
- Okta application resource for SCIM provisioning
- Outputs for Python script configuration
- Variables for customization

Configuration:
- App label: "Custom SCIM Demo App"
- Environment: myorg (must match infrastructure deployment)
- Read server URL and credentials from infrastructure state

Note: The Terraform provider cannot configure SCIM connection settings.
This will be done via Python script in Part 3.

════════════════════════════════════════════════════════════════════════════
PART 3: Configuration Commands
════════════════════════════════════════════════════════════════════════════

Generate a complete deployment script that:

1. Deploys SCIM server infrastructure
2. Waits for server initialization (~5-10 minutes)
3. Verifies server health
4. Creates Okta SCIM app
5. Configures SCIM connection via Python script
6. Tests the connection
7. Outputs next steps (assign users, test provisioning)

Include:
- Health check commands
- Troubleshooting steps
- Dashboard URL
- Okta Admin Console link

════════════════════════════════════════════════════════════════════════════

ADDITIONAL REQUIREMENTS:
- Follow S3 backend pattern: key = "Okta-GitOps/myorg/scim-server/terraform.tfstate"
- Use proper variable validation (domain format, token length, etc.)
- Include comprehensive outputs with setup instructions
- Add comments explaining two-phase automation (Terraform + Python)
- Reference existing README.md and documentation

IMPORTANT NOTES:
- SCIM connection CANNOT be configured via Terraform (provider limitation)
- Python script (scripts/configure_scim_app.py) handles SCIM connection setup
- This is documented in docs/SCIM_OKTA_AUTOMATION.md
- Server initialization takes 5-10 minutes for SSL certificate provisioning

Please generate all necessary files with proper structure and documentation.
```

---

## Step 3: Customize the Generated Code

After the AI generates the code:

1. **Review the terraform.tfvars file**:
   ```bash
   cd environments/myorg/infrastructure/scim-server
   cp terraform.tfvars.example terraform.tfvars
   # Edit with your actual values:
   # - domain_name
   # - route53_zone_id
   # - scim_auth_token (generated)
   # - scim_basic_pass (generated, optional)
   ```

2. **Add terraform.tfvars to .gitignore** (should already be there):
   ```bash
   # In .gitignore:
   terraform.tfvars
   *.tfstate
   *.tfstate.*
   ```

3. **Review security settings**:
   - Restrict `allowed_https_cidr` to Okta IP ranges + your network
   - Review `allowed_ssh_cidr` or disable SSH entirely
   - Use strong authentication tokens (min 32 characters)

---

## Step 4: Deploy Infrastructure

```bash
# Navigate to SCIM server directory
cd environments/myorg/infrastructure/scim-server

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Deploy infrastructure
terraform apply

# Save the outputs
terraform output > outputs.txt
```

**Wait 5-10 minutes** for server initialization:
- Caddy installs and provisions Let's Encrypt SSL certificate
- Python dependencies install
- SCIM server starts

**Check status:**
```bash
# Health check
SCIM_URL=$(terraform output -raw scim_base_url | sed 's|/scim/v2||')
curl $SCIM_URL/health
# Should return: {"status":"healthy"}

# View dashboard
DASHBOARD_URL=$(terraform output -raw dashboard_url)
echo "Dashboard: $DASHBOARD_URL"
open $DASHBOARD_URL  # Or visit in browser
```

---

## Step 5: Create Okta SCIM App

```bash
# Navigate to Okta Terraform directory
cd ../../terraform

# Verify SCIM server state is readable
terraform init

# Review the plan (should show SCIM app creation)
terraform plan

# Create Okta app
terraform apply

# Capture app ID
APP_ID=$(terraform output -raw scim_app_id)
echo "App ID: $APP_ID"
```

---

## Step 6: Configure SCIM Connection

The Okta Terraform provider **cannot** configure SCIM connections. Use the Python script:

```bash
# Get SCIM credentials from infrastructure state
cd ../infrastructure/scim-server
SCIM_URL=$(terraform output -raw scim_base_url)
SCIM_TOKEN=$(terraform output -json okta_configuration | jq -r '.header_auth_token')

# Return to terraform directory
cd ../../terraform

# Run configuration script
python3 ../../scripts/configure_scim_app.py \
  --app-id "$APP_ID" \
  --scim-url "$SCIM_URL" \
  --scim-token "$SCIM_TOKEN" \
  --test-connection
```

**Expected output:**
```
================================================================================
CONFIGURING SCIM APPLICATION
================================================================================

📋 Getting app details...
   App: Custom SCIM Demo App
   ID: 0oa...

🔧 Enabling SCIM provisioning...
✅ Enabled SCIM provisioning

🔗 Configuring SCIM connection...
✅ Configured SCIM connection

🧪 Testing SCIM connection...
✅ SCIM connection test succeeded!

⚙️  Enabling provisioning features...
✅ Enabled provisioning features

================================================================================
✅ SCIM CONFIGURATION COMPLETE
================================================================================
```

---

## Step 7: Test Provisioning

1. **Assign users in Okta**:
   - Open Okta Admin Console
   - Navigate to Applications → Your SCIM App
   - Go to Assignments tab
   - Assign users or groups

2. **Verify provisioning**:
   ```bash
   # Check SCIM server dashboard
   open $(cd ../infrastructure/scim-server && terraform output -raw dashboard_url)
   ```

3. **Assign custom entitlements** (optional):
   - In Okta Admin Console → Applications → Your SCIM App
   - Go to provisioning tab → Attributes
   - Map Okta attributes to SCIM `customEntitlements` field
   - Users will receive assigned roles

4. **View logs**:
   ```bash
   # Via SSM Session Manager (no SSH key needed)
   cd ../infrastructure/scim-server
   aws ssm start-session --target $(terraform output -raw instance_id)

   # Once connected:
   scim-logs       # View SCIM server logs
   scim-status     # Check service status
   ```

---

## Customization Options

### Custom Entitlements/Roles

Edit the `custom_entitlements` variable in terraform.tfvars:

```hcl
custom_entitlements = jsonencode([
  {
    id = "healthcare-clinician"
    name = "Healthcare Clinician"
    description = "Access to patient records and clinical tools"
  },
  {
    id = "healthcare-billing"
    name = "Healthcare Billing Specialist"
    description = "Access to billing and insurance claims"
  },
  {
    id = "healthcare-admin"
    name = "Healthcare Administrator"
    description = "Full system access"
  }
])
```

### Network Configuration

**Restrict to Okta IP Ranges:**
```hcl
allowed_https_cidr = [
  "185.15.224.0/22",   # Okta US cell 1
  "185.82.176.0/22",   # Okta US cell 2
  "44.234.242.0/24",   # Okta US cell 3
  "54.188.171.0/24",   # Okta US cell 4
  "YOUR_OFFICE_IP/32"  # Your office for testing
]
```

**Use Custom VPC:**
```hcl
vpc_id    = "vpc-12345678"
subnet_id = "subnet-12345678"
```

**Use Existing Security Group:**
```hcl
use_existing_security_group = true
security_group_id = "sg-12345678"
```

---

## Troubleshooting

### Server Not Responding

```bash
# Check instance status
cd environments/myorg/infrastructure/scim-server
aws ec2 describe-instance-status --instance-id $(terraform output -raw instance_id)

# Check logs via SSM
aws ssm start-session --target $(terraform output -raw instance_id)
# Then:
tail -f /var/log/user-data.log
scim-logs
```

### SSL Certificate Issues

Let's Encrypt may take time or fail if:
- DNS not propagated yet (wait 5-10 minutes)
- Port 80 not accessible (check security groups)
- Domain doesn't resolve to server IP

```bash
# Check DNS
dig $(terraform output -raw domain_name)

# Check HTTP accessibility
curl -I http://$(terraform output -raw domain_name)
```

### Python Script Fails

If `configure_scim_app.py` fails:
1. Check error message for specific API issue
2. Verify environment variables are set (OKTA_ORG_NAME, OKTA_API_TOKEN, etc.)
3. Verify API token has `okta.apps.manage` scope
4. Fall back to manual configuration (see README.md Option B)

### Connection Test Fails

```bash
# Test SCIM server directly
SCIM_URL=$(cd ../infrastructure/scim-server && terraform output -raw scim_base_url)
SCIM_TOKEN=$(cd ../infrastructure/scim-server && terraform output -json okta_configuration | jq -r '.header_auth_token')

# Test ServiceProviderConfig
curl -H "Authorization: Bearer $SCIM_TOKEN" \
  "$SCIM_URL/ServiceProviderConfig"

# Should return SCIM schema JSON
```

---

## Cleanup

To destroy all resources:

```bash
# Destroy Okta app first
cd environments/myorg/terraform
terraform destroy -target=okta_app_auto_login.scim_demo

# Destroy SCIM server infrastructure
cd ../infrastructure/scim-server
terraform destroy
```

---

## Advanced Use Cases

### Integration with OIG Entitlement Bundles

Create entitlement bundles that grant SCIM app entitlements:

```hcl
# In environments/myorg/terraform/oig_entitlements.tf

resource "okta_entitlement_bundle" "healthcare_clinician_access" {
  name        = "Healthcare Clinician Access"
  description = "Full access to clinical systems"

  entitlement {
    app_id = okta_app_auto_login.scim_demo.id
    value  = "orn:okta:entitlement:healthcare-clinician"
  }
}
```

### Automated Testing

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test-scim.yml
- name: Test SCIM Server
  run: |
    SCIM_URL=$(terraform output -raw scim_base_url)
    HEALTH=$(curl -s $SCIM_URL/health | jq -r '.status')
    if [ "$HEALTH" != "healthy" ]; then
      echo "SCIM server unhealthy"
      exit 1
    fi
```

---

## Documentation References

- **SCIM Server README**: `environments/myorg/infrastructure/scim-server/README.md`
- **Automation Guide**: `docs/SCIM_OKTA_AUTOMATION.md`
- **Release Plan**: `upcoming-releases/SCIM_SERVER_INTEGRATION_PLAN.md`
- **Okta SCIM Docs**: https://developer.okta.com/docs/concepts/scim/

---

## Example AI Prompts

**Quick Demo:**
```
Deploy a simple SCIM demo server at scim.demo.example.com with default 5 roles.
Use domain: scim.demo.example.com
Route53 zone: Z1234567890ABC
Region: us-east-1
Environment: myorg
```

**Healthcare Demo:**
```
Deploy SCIM server for healthcare demo with custom roles:
- Clinician (patient records access)
- Billing Specialist (billing/claims)
- Administrator (full access)
- Nurse (clinical tools, limited records)
- Receptionist (scheduling only)

Domain: scim.healthcare-demo.example.com
Restrict HTTPS to Okta IP ranges only
Environment: healthcare
```

**Multi-Region:**
```
Deploy SCIM server in eu-west-1 for European demo.
Domain: scim.eu-demo.example.com
Use existing VPC: vpc-eu12345678
Existing subnet: subnet-eu12345678
Custom security group with pre-configured rules: sg-eu12345678
```

---

**Prompt Version:** 1.0
**Last Updated:** 2025-11-14
**Compatible With:** Release 2 (Okta Terraform Integration)
