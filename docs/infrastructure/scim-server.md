# SCIM + Okta Automation Guide

Complete guide for automating SCIM application creation and configuration in Okta using Terraform and Python.

## Table of Contents

1. [Overview](#overview)
2. [Why Two-Step Automation?](#why-two-step-automation)
3. [Prerequisites](#prerequisites)
4. [Step-by-Step Guide](#step-by-step-guide)
5. [Terraform Provider Limitations](#terraform-provider-limitations)
6. [Python Script Reference](#python-script-reference)
7. [Troubleshooting](#troubleshooting)
8. [Alternative Approaches](#alternative-approaches)
9. [Examples](#examples)

---

## Overview

This guide explains how to automate the complete SCIM integration workflow:

```
SCIM Server (AWS)  →  Okta App (Terraform)  →  SCIM Config (Python API)  →  Full Automation
```

### What Gets Automated

✅ **Terraform Handles:**
- Creating Okta application
- Reading SCIM server infrastructure state
- Providing configuration commands
- Managing app lifecycle

✅ **Python Script Handles:**
- Enabling SCIM provisioning
- Configuring SCIM connection (base URL, auth)
- Testing SCIM connection
- Enabling provisioning features

❌ **Still Manual:**
- Assigning users/groups to the app
- Configuring custom attribute mappings (optional)
- Reviewing provisioning logs

---

## Why Two-Step Automation?

### Okta Terraform Provider Does NOT Support

The Okta Terraform provider (as of v6.4.0) **does not support** these SCIM-specific operations:

| Feature | Terraform Provider | Okta Admin API | Our Solution |
|---------|-------------------|----------------|--------------|
| Create app | ✅ Yes | ✅ Yes | **Terraform** |
| Enable SCIM provisioning | ❌ No | ✅ Yes | **Python** |
| Configure SCIM connection | ❌ No | ✅ Yes | **Python** |
| Test SCIM connection | ❌ No | ✅ Yes | **Python** |
| Enable provisioning features | ❌ No | ✅ Yes | **Python** |
| Configure attribute mappings | ⚠️ Limited | ✅ Yes | **Python** (optional) |
| Assign users/groups | ✅ Yes | ✅ Yes | **Terraform** (optional) |

### Architecture Decision

We use a **two-phase approach** for full automation:

**Phase 1: Terraform (App Creation)**
```hcl
resource "okta_app_auto_login" "scim_demo" {
  label = "Custom SCIM Demo App"
  # Creates app shell, but cannot configure SCIM connection
}
```

**Phase 2: Python (SCIM Configuration)**
```python
configurator.configure_app(
    app_id=app_id,
    scim_url=scim_url,
    scim_token=scim_token
)
# Configures SCIM connection via Admin API
```

This gives us:
- ✅ Infrastructure as Code (Terraform manages app lifecycle)
- ✅ Complete automation (Python handles what Terraform can't)
- ✅ Idempotent operations (can re-run safely)
- ✅ Clear separation of concerns

---

## Prerequisites

### 1. SCIM Server Deployed

The SCIM server infrastructure must be deployed first. You have two deployment options:

#### Option A: GitHub Actions Workflow (Recommended)

This is the recommended approach for production deployments, following GitOps best practices.

**1. Add GitHub Environment Secrets:**

Navigate to: **GitHub Repository → Settings → Environments → MyOrg**

Add these secrets:

| Secret Name | Description | How to Generate |
|-------------|-------------|-----------------|
| `SCIM_AUTH_TOKEN` | Bearer token for SCIM authentication | `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'` |
| `AWS_REGION` | AWS region | `us-east-1` (or your preferred region) |
| `AWS_ROLE_ARN` | AWS OIDC role ARN | Already configured (from AWS backend setup) |

**2. Deploy via GitHub Actions:**

```bash
# Plan deployment
gh workflow run deploy-scim-server.yml \
  -f environment=myorg \
  -f domain_name=scim.demo-myorg.example.com \
  -f route53_zone_id=Z1234567890ABC \
  -f instance_type=t3.micro \
  -f action=plan

# Review plan output in GitHub Actions → Workflow runs

# Apply deployment
gh workflow run deploy-scim-server.yml \
  -f environment=myorg \
  -f domain_name=scim.demo-myorg.example.com \
  -f route53_zone_id=Z1234567890ABC \
  -f instance_type=t3.micro \
  -f action=apply
```

**3. Verify deployment:**

Check the workflow summary in GitHub Actions for:
- Infrastructure outputs (URLs, IDs)
- Health check instructions
- Next-step commands

**Benefits:**
- Secrets stored securely in GitHub (not in local files)
- Audit trail of all deployments
- Environment protection with approval gates
- AWS OIDC authentication (no long-lived credentials)
- Automated next-step instructions

#### Option B: Manual Terraform Deployment (Alternative)

Use this for local development or testing:

```bash
cd environments/myorg/infrastructure/scim-server

# Create terraform.tfvars from example
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars

# Initialize and deploy
terraform init
terraform apply
```

Verify deployment:
```bash
terraform output scim_base_url
# Should show: https://scim.yourdomain.com/scim/v2

curl $(terraform output -raw scim_health_url)
# Should return: {"status":"healthy"}
```

### 2. Okta Environment Configured

Ensure GitHub Environment or local environment has:

```bash
export OKTA_ORG_NAME="your-org"
export OKTA_BASE_URL="okta.com"
export OKTA_API_TOKEN="your-api-token"
```

API token must have scopes:
- `okta.apps.manage` - Create/update applications
- `okta.apps.read` - Read application configuration

### 3. Python Dependencies

```bash
pip install requests python-dotenv
```

Or use the repository requirements:
```bash
pip install -r requirements.txt
```

### 4. Custom Entitlements (Optional)

The SCIM server supports custom entitlements/roles to demonstrate different application scenarios. By default, it uses 5 standard roles (Administrator, Standard User, Read Only, Support Agent, Billing Manager).

**Using Pre-Built Templates:**

The repository includes templates for common applications:
- `entitlements.json` - Default 5 roles
- `examples/entitlements-salesforce.json` - Salesforce-style roles
- `examples/entitlements-aws.json` - AWS IAM-style permissions
- `examples/entitlements-generic.json` - Generic application roles

**Deploying with Custom Entitlements:**

When deploying the SCIM server, specify the entitlements file:

```bash
# Via GitHub Actions
gh workflow run deploy-scim-server.yml \
  -f environment=myorg \
  -f domain_name=scim.demo-myorg.example.com \
  -f route53_zone_id=Z1234567890ABC \
  -f entitlements_file=examples/entitlements-salesforce.json \
  -f action=apply

# Via Terraform
cd environments/myorg/infrastructure/scim-server
terraform apply -var="entitlements_file=examples/entitlements-aws.json"
```

**Creating Custom Entitlements:**

Create a JSON file following this schema:

```json
{
  "entitlements": [
    {
      "id": "role_analyst",
      "name": "Data Analyst",
      "description": "Analytics and reporting access",
      "permissions": ["read", "analytics", "reports"]
    }
  ]
}
```

See `environments/myorg/infrastructure/scim-server/README.md` for complete documentation.

---

## Step-by-Step Guide

### Quick Reference

**GitHub Actions Workflow (Recommended):**
1. Add secrets to GitHub Environment (SCIM_AUTH_TOKEN, AWS_REGION, AWS_ROLE_ARN)
2. Deploy SCIM server: `gh workflow run deploy-scim-server.yml`
3. Create Okta app: `cd environments/myorg/terraform && terraform apply`
4. Configure SCIM connection: `python3 scripts/configure_scim_app.py`

**Manual Terraform (Alternative):**
1. Deploy SCIM server: `cd infrastructure/scim-server && terraform apply`
2. Create Okta app: `cd ../../terraform && terraform apply`
3. Configure SCIM connection: `python3 scripts/configure_scim_app.py`

---

### Phase 1: Terraform (App Creation)

**1. Navigate to Okta Terraform directory**

```bash
cd environments/myorg/terraform
```

**2. Review SCIM app configuration**

The `scim_app.tf` file contains:
- Data source to read SCIM server state
- Okta app resource
- Outputs for Python script

```hcl
data "terraform_remote_state" "scim_server" {
  backend = "s3"
  config = {
    bucket = "okta-terraform-demo"
    key    = "Okta-GitOps/myorg/scim-server/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "okta_app_auto_login" "scim_demo" {
  label = var.scim_app_label
  # ... configuration
}
```

**3. Customize variables (optional)**

Edit `terraform.tfvars` or use CLI variables:

```hcl
scim_app_label = "My Custom SCIM App"
scim_environment = "myorg"  # Must match infrastructure deployment
scim_aws_region = "us-east-1"
```

**4. Apply Terraform**

```bash
terraform init
terraform plan
terraform apply
```

**5. Capture outputs**

```bash
# App ID (needed for Python script)
APP_ID=$(terraform output -raw scim_app_id)

# SCIM server URL (from infrastructure state)
SCIM_URL=$(terraform output -raw scim_server_url)

# View complete setup command
terraform output scim_configuration_command
```

### Phase 2: Python (SCIM Configuration)

**1. Get SCIM credentials**

From the SCIM server infrastructure state:

```bash
cd ../infrastructure/scim-server

# Bearer token (recommended)
SCIM_TOKEN=$(terraform output -json okta_configuration | jq -r '.header_auth_token')

# OR Basic auth credentials
SCIM_USER=$(terraform output -json okta_configuration | jq -r '.basic_auth_username')
SCIM_PASS=$(terraform output -json okta_configuration | jq -r '.basic_auth_password')

cd ../../terraform
```

**2. Run configuration script**

**Using Bearer Token (Recommended):**

```bash
python3 ../../scripts/configure_scim_app.py \
  --app-id "$APP_ID" \
  --scim-url "$SCIM_URL" \
  --scim-token "$SCIM_TOKEN" \
  --test-connection
```

**Using Basic Auth:**

```bash
python3 ../../scripts/configure_scim_app.py \
  --app-id "$APP_ID" \
  --scim-url "$SCIM_URL" \
  --scim-user "$SCIM_USER" \
  --scim-pass "$SCIM_PASS" \
  --auth-mode basic \
  --test-connection
```

**3. Verify configuration**

The script will:
1. ✅ Get app details from Okta
2. ✅ Enable SCIM provisioning
3. ✅ Configure SCIM connection (URL + auth)
4. ✅ Test connection (if `--test-connection` flag used)
5. ✅ Enable provisioning features

**4. Check in Okta Admin Console**

1. Navigate to app: `https://your-org.okta.com/admin/apps`
2. Find your SCIM app
3. Go to **Provisioning** tab
4. Verify:
   - ✅ "API Integration" enabled
   - ✅ SCIM Base URL configured
   - ✅ Authentication configured
   - ✅ Connection test passed
   - ✅ Provisioning features enabled

---

## Terraform Provider Limitations

### What the Okta Provider Can Do

```hcl
# ✅ Create app resource
resource "okta_app_auto_login" "example" {
  label = "My App"
}

# ✅ Assign groups
resource "okta_app_group_assignments" "example" {
  app_id = okta_app_auto_login.example.id
  group {
    id = var.group_id
  }
}

# ✅ Manage basic settings
# - App visibility
# - Sign-on settings
# - Logo
```

### What the Provider CANNOT Do

```python
# ❌ Enable SCIM provisioning
# Must use: POST /api/v1/apps/{appId}/features/provisioning

# ❌ Configure SCIM connection
# Must use: PUT /api/v1/apps/{appId}
# With scimConnector settings

# ❌ Test SCIM connection
# Must use: POST /api/v1/apps/{appId}/connections/default/test

# ❌ Enable provisioning features programmatically
# Must use: PUT /api/v1/apps/{appId}/features/provisioning

# ⚠️ Attribute mappings (very limited support)
# Provider has some support via app profile mappings
# But not full SCIM attribute mapping configuration
```

### Provider Roadmap

Track Okta Terraform provider feature requests:
- [GitHub: okta/terraform-provider-okta](https://github.com/okta/terraform-provider-okta/issues)

---

## Python Script Reference

### Basic Usage

```bash
python3 scripts/configure_scim_app.py \
  --app-id <app_id> \
  --scim-url <scim_base_url> \
  --scim-token <bearer_token>
```

### All Options

```
--app-id APP_ID           Okta application ID (required)
--scim-url SCIM_URL       SCIM base URL (required)
--auth-mode {bearer|basic} Authentication mode (default: bearer)
--scim-token SCIM_TOKEN   Bearer token for auth
--scim-user SCIM_USER     Username for basic auth
--scim-pass SCIM_PASS     Password for basic auth
--test-connection         Test SCIM connection after config
--dry-run                 Preview changes without applying
```

### Examples

**Dry Run (Preview Only):**

```bash
python3 scripts/configure_scim_app.py \
  --app-id 0oa1b2c3d4e5f6g7h8i9 \
  --scim-url https://scim.example.com/scim/v2 \
  --scim-token "MySecretToken123" \
  --dry-run
```

**With Connection Test:**

```bash
python3 scripts/configure_scim_app.py \
  --app-id 0oa1b2c3d4e5f6g7h8i9 \
  --scim-url https://scim.example.com/scim/v2 \
  --scim-token "MySecretToken123" \
  --test-connection
```

**Basic Auth:**

```bash
python3 scripts/configure_scim_app.py \
  --app-id 0oa1b2c3d4e5f6g7h8i9 \
  --scim-url https://scim.example.com/scim/v2 \
  --scim-user okta_scim_user \
  --scim-pass "MySecretPassword" \
  --auth-mode basic
```

### Script Output

```
================================================================================
CONFIGURING SCIM APPLICATION
================================================================================

📋 Getting app details...
   App: Custom SCIM Demo App
   ID: 0oa1b2c3d4e5f6g7h8i9

🔧 Enabling SCIM provisioning...
✅ Enabled SCIM provisioning for app 0oa1b2c3d4e5f6g7h8i9

🔗 Configuring SCIM connection...
   Base URL: https://scim.example.com/scim/v2
   Auth Mode: bearer
✅ Configured SCIM connection for app 0oa1b2c3d4e5f6g7h8i9

🧪 Testing SCIM connection...
✅ SCIM connection test succeeded!

⚙️  Enabling provisioning features...
✅ Enabled provisioning features for app 0oa1b2c3d4e5f6g7h8i9

================================================================================
✅ SCIM CONFIGURATION COMPLETE
================================================================================

📍 Next steps:
   1. Assign users/groups to the app in Okta
   2. Verify provisioning in SCIM server dashboard: https://scim.example.com
   3. Check provisioning logs in Okta Admin Console
```

---

## Operational Workflows

### SCIM - Check Server Status (`scim-check-status.yml`)

Diagnose SCIM server health: process status, listening ports, service status, health endpoints, recent logs, disk usage, and OPA agent status.

```bash
gh workflow run scim-check-status.yml \
  -f environment=myorg \
  -f region=us-east-1
```

Discovers the SCIM instance automatically via:
1. Tag name patterns (`*scim*`, `*SCIM*`)
2. Role/Environment tags
3. Terraform state output

Checks performed:
- SCIM process running
- Ports 80/443/8080/8443 listening
- `scim-server` or `nginx` systemd service
- `http://localhost:8080/health` endpoint
- Recent journal/log entries
- Disk usage
- External health endpoint (if public IP available)

---

## Troubleshooting

### Python Script Fails

**Error: "App ID not found"**

```
❌ Error getting app details: 404 Client Error
   App ID not found: 0oa1b2c3d4e5f6g7h8i9
```

**Solution:**
1. Verify app was created: `terraform state list | grep okta_app`
2. Get correct app ID: `terraform output scim_app_id`
3. Check Okta Admin Console for app existence

---

**Error: "Could not enable via Features API"**

```
⚠️  Could not enable via Features API: 404 Client Error
   This may be normal for some app types. Continuing...
```

**Explanation:**
- Some app types don't support the Features API endpoint
- This is expected and the script continues

**Action:**
- Script will attempt alternative configuration methods
- If all fail, manual configuration required

---

**Error: "Error configuring SCIM connection"**

```
❌ Error configuring SCIM connection: Invalid SCIM URL
   You may need to configure this manually in the Okta Admin Console
```

**Solution:**
1. Verify SCIM server is accessible:
   ```bash
   curl https://scim.example.com/health
   ```
2. Check SCIM URL format: must end with `/scim/v2`
3. Fall back to manual configuration (see README.md)

---

**Error: "Connection test endpoint not available"**

```
⚠️  Connection test endpoint not available for this app type
   Please test connection manually in Okta Admin Console
```

**Explanation:**
- Some app types don't support automated connection testing
- Manual verification required

**Action:**
1. Open app in Okta Admin Console
2. Go to Provisioning → Integration
3. Click "Test API Credentials"
4. Verify connection succeeds

---

### Terraform Data Source Issues

**Error: "Error acquiring the state lock"**

```
Error: Error acquiring the state lock
  State lock not configured or state lock timeout exceeded
```

**Solution:**
```bash
# Check lock status
aws dynamodb get-item \
  --table-name okta-terraform-state-lock \
  --key '{"LockID":{"S":"okta-terraform-demo/Okta-GitOps/myorg/scim-server/terraform.tfstate"}}'

# If stuck, force unlock (use with caution!)
cd ../infrastructure/scim-server
terraform force-unlock <LOCK_ID>
```

---

**Error: "No state file was found"**

```
Error: No state file was found for the given configuration
  Ensure the SCIM server has been deployed
```

**Solution:**
1. Deploy SCIM server first:
   ```bash
   cd ../infrastructure/scim-server
   terraform init
   terraform apply
   ```
2. Verify state exists in S3:
   ```bash
   aws s3 ls s3://okta-terraform-demo/Okta-GitOps/myorg/scim-server/
   ```

---

### Authentication Issues

**Error: "401 Unauthorized"**

**Solution:**
1. Verify Okta API token is valid:
   ```bash
   curl -H "Authorization: SSWS $OKTA_API_TOKEN" \
     https://your-org.okta.com/api/v1/users/me
   ```
2. Check token has required scopes:
   - `okta.apps.manage`
   - `okta.apps.read`
3. Regenerate token if needed in Okta Admin Console

---

**Error: "403 Forbidden"**

**Solution:**
- API token may lack required permissions
- Ensure token has `okta.apps.manage` scope
- Check if MFA is required for API access

---

### SCIM Connection Test Failures

**Error: "SCIM connection test failed"**

**Diagnostics:**

1. **Test SCIM server health:**
   ```bash
   curl https://scim.example.com/health
   # Should return: {"status":"healthy"}
   ```

2. **Test SCIM ServiceProviderConfig:**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://scim.example.com/scim/v2/ServiceProviderConfig
   # Should return SCIM schema
   ```

3. **Test user creation:**
   ```bash
   curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"userName":"test@example.com","name":{"givenName":"Test","familyName":"User"}}' \
     https://scim.example.com/scim/v2/Users
   ```

4. **Check SCIM server logs:**
   ```bash
   cd ../infrastructure/scim-server
   aws ssm start-session --target $(terraform output -raw instance_id)
   # Once connected:
   scim-logs
   ```

---

## Alternative Approaches

### 1. Terraform-Only (Partial)

Create app with Terraform, accept manual SCIM configuration:

```hcl
# Creates app shell only
resource "okta_app_auto_login" "scim_demo" {
  label = "SCIM Demo"
  skip_users = true
  skip_groups = true
}

output "manual_config_url" {
  value = "https://${var.okta_org_name}.${var.okta_base_url}/admin/app/${okta_app_auto_login.scim_demo.name}/instance/${okta_app_auto_login.scim_demo.id}/"
}
```

**Pros:**
- ✅ Simple Terraform-only workflow
- ✅ No Python dependencies

**Cons:**
- ❌ Requires manual SCIM configuration
- ❌ Not fully automated
- ❌ Prone to configuration errors

---

### 2. API-Only (No Terraform)

Use Python to create AND configure app:

```python
# Create app via API
app = okta_client.create_app(app_config)

# Configure SCIM via API
okta_client.configure_scim(app['id'], scim_config)
```

**Pros:**
- ✅ Single-language solution
- ✅ Complete automation

**Cons:**
- ❌ Not Infrastructure as Code
- ❌ No state management
- ❌ Harder to maintain

---

### 3. Manual (Okta Admin Console)

Create and configure entirely via UI.

**Pros:**
- ✅ No code required
- ✅ Visual confirmation
- ✅ Immediate feedback

**Cons:**
- ❌ Not reproducible
- ❌ No version control
- ❌ Error-prone
- ❌ Not scalable

---

### Our Recommendation

**Use Terraform + Python (Hybrid Approach)**

This provides:
- ✅ Infrastructure as Code (Terraform)
- ✅ Complete automation (Python fills gaps)
- ✅ State management (Terraform)
- ✅ Reproducibility (both tools)
- ✅ Version control (both tools)
- ✅ Clear separation of concerns

---

## Examples

### Complete End-to-End Example

#### Using GitHub Actions Workflow (Recommended)

```bash
#!/bin/bash
# complete-scim-setup-workflow.sh
# Complete SCIM + Okta automation using GitHub Actions

set -e

echo "Step 1: Deploy SCIM Server via GitHub Actions"
gh workflow run deploy-scim-server.yml \
  -f environment=myorg \
  -f domain_name=scim.demo-myorg.example.com \
  -f route53_zone_id=Z1234567890ABC \
  -f instance_type=t3.micro \
  -f action=apply

echo "⏳ Waiting for workflow to complete (check GitHub Actions tab)..."
echo "Press Enter once deployment is complete..."
read

echo "Step 2: Create Okta App"
cd environments/myorg/terraform
terraform init
terraform apply -auto-approve

APP_ID=$(terraform output -raw scim_app_id)

echo "Step 3: Get SCIM credentials from GitHub secrets"
echo "SCIM_URL=https://scim.demo-myorg.example.com/scim/v2"
echo "SCIM_TOKEN is stored in GitHub Environment secret: SCIM_AUTH_TOKEN"
echo ""
echo "Enter SCIM_AUTH_TOKEN from GitHub secrets:"
read -s SCIM_TOKEN

echo "Step 4: Configure SCIM Connection"
python3 ../../scripts/configure_scim_app.py \
  --app-id "$APP_ID" \
  --scim-url "https://scim.demo-myorg.example.com/scim/v2" \
  --scim-token "$SCIM_TOKEN" \
  --test-connection

echo "✅ Complete! SCIM app configured and ready."
echo "📍 Next: Assign users to app in Okta Admin Console"
```

#### Using Manual Terraform (Alternative)

```bash
#!/bin/bash
# complete-scim-setup.sh
# Complete SCIM + Okta automation

set -e

echo "Step 1: Deploy SCIM Server"
cd environments/myorg/infrastructure/scim-server
terraform init
terraform apply -auto-approve

echo "Step 2: Get SCIM credentials"
SCIM_URL=$(terraform output -raw scim_base_url)
SCIM_TOKEN=$(terraform output -json okta_configuration | jq -r '.header_auth_token')

echo "Step 3: Create Okta App"
cd ../../terraform
terraform init
terraform apply -auto-approve

APP_ID=$(terraform output -raw scim_app_id)

echo "Step 4: Configure SCIM Connection"
python3 ../../scripts/configure_scim_app.py \
  --app-id "$APP_ID" \
  --scim-url "$SCIM_URL" \
  --scim-token "$SCIM_TOKEN" \
  --test-connection

echo "✅ Complete! SCIM app configured and ready."
echo "📍 Next: Assign users to app in Okta Admin Console"
```

### CI/CD Integration Example

```yaml
# .github/workflows/deploy-scim.yml
name: Deploy SCIM Integration

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        default: 'myorg'

jobs:
  deploy-scim-server:
    name: Deploy SCIM Server
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Deploy SCIM Server
        working-directory: environments/${{ github.event.inputs.environment }}/infrastructure/scim-server
        run: |
          terraform init
          terraform apply -auto-approve

      - name: Export SCIM Credentials
        id: scim_creds
        working-directory: environments/${{ github.event.inputs.environment }}/infrastructure/scim-server
        run: |
          echo "scim_url=$(terraform output -raw scim_base_url)" >> $GITHUB_OUTPUT
          echo "scim_token=$(terraform output -json okta_configuration | jq -r '.header_auth_token')" >> $GITHUB_OUTPUT

    outputs:
      scim_url: ${{ steps.scim_creds.outputs.scim_url }}
      scim_token: ${{ steps.scim_creds.outputs.scim_token }}

  configure-okta-app:
    name: Configure Okta SCIM App
    runs-on: ubuntu-latest
    needs: deploy-scim-server
    environment: ${{ github.event.inputs.environment }}
    steps:
      - uses: actions/checkout@v4

      - name: Create Okta App
        working-directory: environments/${{ github.event.inputs.environment }}/terraform
        env:
          OKTA_ORG_NAME: ${{ secrets.OKTA_ORG_NAME }}
          OKTA_BASE_URL: ${{ secrets.OKTA_BASE_URL }}
          OKTA_API_TOKEN: ${{ secrets.OKTA_API_TOKEN }}
        run: |
          terraform init
          terraform apply -auto-approve

      - name: Configure SCIM Connection
        env:
          OKTA_ORG_NAME: ${{ secrets.OKTA_ORG_NAME }}
          OKTA_BASE_URL: ${{ secrets.OKTA_BASE_URL }}
          OKTA_API_TOKEN: ${{ secrets.OKTA_API_TOKEN }}
        run: |
          APP_ID=$(cd environments/${{ github.event.inputs.environment }}/terraform && terraform output -raw scim_app_id)

          python3 scripts/configure_scim_app.py \
            --app-id "$APP_ID" \
            --scim-url "${{ needs.deploy-scim-server.outputs.scim_url }}" \
            --scim-token "${{ needs.deploy-scim-server.outputs.scim_token }}" \
            --test-connection
```

---

## Summary

**Two-Phase Automation:**

1. **Terraform** - Creates app, manages infrastructure
2. **Python** - Configures SCIM connection (API gaps)

**When to Use:**
- ✅ Production deployments requiring IaC
- ✅ Multi-environment setups
- ✅ CI/CD pipelines
- ✅ Repeatable configurations

**When NOT to Use:**
- ❌ One-off demos (manual may be faster)
- ❌ Environments without Python available
- ❌ Apps requiring complex custom attribute mappings

**Future:**
- Monitor Okta Terraform provider for SCIM support
- Migrate to pure Terraform when available
- Maintain Python script for edge cases

---

**Document Version:** 1.0
**Last Updated:** 2025-11-14
**Maintained By:** Template Maintainers
