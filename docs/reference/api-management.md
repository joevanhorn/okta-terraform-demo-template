# Okta OIG API Management Guide

This guide explains how to manage **Resource Owners** and **Labels** using the Okta API, complementing the Terraform provider.

## 📋 Overview

While the Okta Terraform Provider v6.1.0 adds support for many OIG features, some capabilities are only available via REST API:

- **Resource Owners API** - Assign owners to apps, groups, and entitlements
- **Labels API** - Create and assign governance labels to resources

**Note:** Entitlements should be managed via Terraform using the `okta_principal_entitlements` resource, not via this API management script.

This implementation uses the `okta_api_manager.py` script with **modular export functionality** that gracefully handles partial OIG availability.

## 🆕 Modular OIG Export

### Overview

The modular export approach allows you to export API-only OIG resources independently with graceful error handling:

**Key Features:**
- **Independent exports**: Labels and resource owners export separately
- **Graceful degradation**: HTTP 400/404 treated as "not_available" instead of errors
- **Status tracking**: Each export type reports its own status (success/not_available/error/skipped)
- **API-only focus**: Only exports resources not manageable via Terraform

### Export Status Codes

| Status | Description | Example Scenario |
|--------|-------------|------------------|
| `success` | Export completed successfully | 15 labels exported successfully |
| `not_available` | Resource type not available (HTTP 400/404) | Labels endpoint not enabled |
| `error` | Export failed with an error | API authentication failed |
| `skipped` | Export was not requested | Resource owners without --resource-orns |

### Usage

**Via GitHub Actions (Recommended):**

The `export-oig.yml` workflow uses the modular export (requires environment parameter):

```yaml
# .github/workflows/export-oig.yml
# Run with: gh workflow run export-oig.yml -f environment=myorg
python3 scripts/okta_api_manager.py \
  --action export \
  --org-name $OKTA_ORG_NAME \
  --base-url $OKTA_BASE_URL \
  --api-token $OKTA_API_TOKEN \
  --output ${EXPORT_DIR}/oig_export.json \
  --export-labels \
  --export-owners \
  --resource-orns <orn1> <orn2>
```

**Via Command Line:**

```bash
# Export API-only OIG resources (Labels and Resource Owners)
python3 scripts/okta_api_manager.py \
  --action export \
  --org-name demo-myorg \
  --base-url oktapreview.com \
  --api-token $OKTA_API_TOKEN \
  --output oig_export.json \
  --export-labels \
  --export-owners \
  --resource-orns "orn:okta:idp:demo:apps:oauth2:0oa123"
```

**CLI Arguments:**
- `--export-labels` - Export governance labels (default: true)
- `--export-owners` - Export resource owners (default: false, requires --resource-orns)
- `--resource-orns` - List of resource ORNs to export owners for

### Export Output Example

```json
{
  "export_date": "2025-11-07T01:59:19Z",
  "okta_org": "demo-myorg",
  "okta_base_url": "oktapreview.com",
  "export_status": {
    "labels": "success",
    "resource_owners": "success"
  },
  "labels": [
    {
      "name": "production",
      "description": "Production environment resources",
      "resources": [...]
    }
  ],
  "resource_owners": [
    {
      "resource_orn": "orn:okta:idp:demo:apps:oauth2:0oa123",
      "owners": [
        {
          "principalOrn": "orn:okta:directory:demo:users:00u456",
          "principalName": "John Doe"
        }
      ]
    }
  ]
}
```

### Implementation Details

The modular export is implemented in `okta_api_manager.py` with these key functions:

```python
def export_labels_only(manager: OktaAPIManager) -> Dict:
    """Export only governance labels with graceful error handling"""
    try:
        labels_response = manager.list_labels()
        # ... process labels
        return {"labels": labels_data, "status": "success"}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [400, 404]:
            return {"labels": [], "status": "not_available", "reason": str(e)}
        return {"labels": [], "status": "error", "reason": str(e)}

def export_resource_owners_only(manager: OktaAPIManager, resource_orns: List[str]) -> Dict:
    """Export only resource owners for specified resources"""
    # Requires resource ORNs to be provided
    # Includes rate limiting with exponential backoff
```

---

## 🔐 GitOps Label Validation Workflow

### Overview

This repository implements a two-phase GitOps workflow for label management that separates syntax validation from API validation:

**Phase 1: PR Validation (Syntax Check)**
- Workflow: `.github/workflows/validate-label-mappings.yml`
- Triggers on: PRs that modify `label_mappings.json`
- No Okta API calls (no secrets required)
- Validates JSON syntax and ORN formats
- Posts validation results as PR comment

**Phase 2: Deployment (API Validation)**
- Workflow: `.github/workflows/myorg-apply-labels-from-config.yml`
- Triggers on: Push to main (auto dry-run) or manual dispatch
- Uses environment secrets for Okta API access
- Automatic dry-run on merge to main
- Manual apply with `dry_run=false` input

### GitOps Flow Diagram

```
Developer edits label_mappings.json
  ↓
Create Pull Request
  ↓
[Automatic] Syntax Validation Workflow
  - Validate JSON syntax
  - Check ORN formats
  - Post PR comment with results
  ↓
Code Review & Approval
  ↓
Merge to Main
  ↓
[Automatic] Deployment Workflow (dry-run mode)
  - Connect to Okta API
  - Validate labels exist
  - Show what would be created/assigned
  - Post workflow summary
  ↓
Review Dry-Run Results
  ↓
[Manual] Trigger Apply
  - Run workflow with dry_run=false
  - Apply labels to Okta
  - Complete audit trail in Git
```

### Validation Script Usage

The `validate_label_config.py` script can be run standalone or via GitHub Actions:

**Standalone Usage:**

```bash
# Validate a label configuration file
python3 scripts/validate_label_config.py \
  environments/myorg/config/label_mappings.json
```

**Expected Output:**
```
✅ Required structure present

**Configuration Summary:**
- Labels defined: 2
- Assignment categories: 2
- Total resource assignments: 15

**Labels:**
- Privileged
- Crown Jewel

**ORN Validation:**
✅ All ORNs have valid format
```

**Error Example:**
```bash
# Missing required keys
❌ Missing required keys: assignments

# Invalid ORN format
❌ Invalid ORN formats found:
  - apps/Privileged: badformat:okta:app:123
```

**Exit Codes:**
- `0` - Validation passed
- `1` - Validation failed (syntax or structure errors)

### GitHub Actions Integration

#### Workflow 1: PR Validation (Environment-Agnostic)

**File:** `.github/workflows/validate-label-mappings.yml`

**Triggers:**
```yaml
on:
  pull_request:
    paths:
      - 'environments/*/config/label_mappings.json'
    types: [opened, synchronize, reopened]
```

**Key Features:**
- No environment secrets required (syntax-only validation)
- Permissions: `contents: read`, `pull-requests: write`
- Posts results as PR comment with next steps
- Fails PR if validation errors found

**What It Validates:**
1. JSON syntax using `python3 -m json.tool`
2. Required structure (labels, assignments keys)
3. ORN format (all start with `orn:`)
4. Configuration summary (label count, assignment count)

**PR Comment Example:**
```markdown
## 🏷️ Label Mappings Validation

Configuration file validation has completed for this PR.

### GitOps Workflow
When this PR is merged:
1. ✅ Configuration will be merged to main branch
2. 🔍 Label application workflow will run automatically in **dry-run mode**
3. 📊 Dry-run results will be available in workflow summary
4. 🔐 Manual approval required to apply labels (run workflow with `dry_run=false`)

This ensures all label changes have:
- ✓ Code review (via PR)
- ✓ Automated validation (this workflow)
- ✓ Dry-run preview (automatic on merge)
- ✓ Manual approval (before applying)
```

#### Workflow 2: Label Deployment (Environment-Specific)

**File:** `.github/workflows/apply-labels-from-config.yml`

**Triggers:**
```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment (myorg, production, etc.)'
        required: true
        type: choice
      dry_run:
        description: 'Dry run mode'
        required: false
        default: 'true'
        type: choice
        options: ['true', 'false']
  push:
    branches:
      - main
    paths:
      - 'environments/*/config/label_mappings.json'
```

**Key Features:**
- Requires environment parameter (e.g., `myorg`)
- Uses corresponding GitHub Environment for secrets (e.g., `MyOrg`)
- Permissions: `contents: write`, `actions: read`
- Auto dry-run on push to main (detects environment from file path)
- Manual apply via workflow dispatch (requires environment selection)
- Uploads artifacts (logs and results JSON)

**Automatic Behavior:**
- **On push to main:** Runs in dry-run mode (shows what would be done)
- **On workflow dispatch:** Uses `dry_run` input parameter

**Dry-Run vs Apply:**

| Mode | Triggered By | Dry Run | Makes Changes |
|------|-------------|---------|---------------|
| Auto Dry-Run | Push to main | ✅ Yes | ❌ No |
| Manual Dry-Run | Workflow dispatch (dry_run=true) | ✅ Yes | ❌ No |
| Manual Apply | Workflow dispatch (dry_run=false) | ❌ No | ✅ Yes |

### Best Practices

1. **Always Create PRs for Label Changes**
   - Never commit directly to main
   - Let validation workflow catch errors early
   - Get code review for governance changes

2. **Review Dry-Run Results Before Applying**
   - Check labels to be created
   - Verify assignments look correct
   - Ensure no errors in dry-run

3. **Use Descriptive Commit Messages**
   ```bash
   git commit -m "feat: Label CRM app as Crown Jewel

   Adding Crown Jewel label to Salesforce CRM app for
   enhanced governance and access review filtering."
   ```

4. **Sync Configuration After Manual Changes**
   - If labels are created manually in Okta UI
   - Run sync script to update label_mappings.json
   - Commit the synced configuration

5. **Monitor Workflow Runs**
   ```bash
   # Watch PR validation
   gh run watch <RUN_ID>

   # Check deployment status
   gh run list --workflow=apply-labels-from-config.yml
   ```

### Troubleshooting

**Issue: PR validation fails with JSON syntax error**

**Solution:**
```bash
# Validate JSON locally before pushing
python3 -m json.tool \
  environments/myorg/config/label_mappings.json
```

**Issue: ORN format validation fails**

**Solution:**
- Ensure all ORNs start with `orn:`
- Format: `orn:okta:{resource-type}:{org}:{type}:{id}`
- Example: `orn:okta:idp:myorg:apps:oauth2:0oa123`

**Issue: Dry-run succeeds but apply fails**

**Solution:**
- Check Okta API token has governance permissions
- Verify environment secrets are correct
- Check for rate limiting in workflow logs
- Review error details in uploaded artifacts

**Issue: Workflow doesn't trigger on PR**

**Solution:**
- Verify file path matches: `environments/*/config/label_mappings.json`
- Check PR includes changes to label_mappings.json
- Ensure workflow file exists in `.github/workflows/`

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Terraform     │
│                 │
│  - Core OIG     │
│  - Resources    │
│  - Reviews      │
│  - Requests     │
└────────┬────────┘
         │
         │ generates
         ▼
┌─────────────────┐
│  api_config.json│
└────────┬────────┘
         │
         │ consumed by
         ▼
┌─────────────────┐
│  Python Script  │
│                 │
│  - Owners API   │
│  - Labels API   │
└────────┬────────┘
         │
         │ calls
         ▼
┌─────────────────┐
│   Okta OIG API  │
└─────────────────┘
```

## 📦 Components

### 1. Python API Manager (`okta_api_manager.py`)

A comprehensive Python script that:
- Creates and manages governance labels
- Assigns resource owners to apps, groups, and entitlements
- Queries existing configurations
- Handles rate limiting and retries
- Provides idempotent operations

### 2. Terraform Integration

Terraform resources that:
- Generate API configuration from Terraform state
- Execute Python script via `local-exec` provisioners
- Manage lifecycle (create/update/destroy)
- Pass credentials securely

### 3. Configuration File (`label_mappings.json`)

JSON configuration containing:
- Label definitions
- Resource owner assignments
- Label-to-resource mappings

### 4. Validation Script (`validate_label_config.py`)

Standalone Python script that validates label configuration files:
- Checks JSON syntax
- Validates required structure (labels, assignments keys)
- Validates ORN formats
- Provides configuration summary
- Used by GitOps PR validation workflow

## 🚀 Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install requests

# Ensure Python 3.8+ is available
python3 --version
```

### Basic Setup

1. **Add Python script to your repository:**

```bash
mkdir -p scripts
# Copy okta_api_manager.py to scripts/
chmod +x scripts/okta_api_manager.py
```

2. **Configure in Terraform:**

```hcl
# In your terraform/main.tf or separate file

variable "app_owner_configs" {
  type = list(object({
    app_name       = string
    app_id         = string
    app_type       = string
    owner_user_ids = list(string)
  }))
  default = [{
    app_name       = "My App"
    app_id         = "0oa1234567890abcdef"
    app_type       = "oauth2"
    owner_user_ids = ["00u10sfroCwbHQO4a0g4"]
  }]
}

module "api_management" {
  source = "./modules/api-management"
  
  okta_org_name       = var.okta_org_name
  okta_api_token      = var.okta_api_token
  app_owner_configs   = var.app_owner_configs
}
```

3. **Apply configuration:**

```bash
terraform init
terraform plan
terraform apply
```

## 🔧 Configuration Examples

### Resource Owners

#### Assign User Owners to an App

```json
{
  "resource_owners": [
    {
      "description": "App owners for production CRM",
      "principal_type": "user",
      "principal_ids": [
        "00u10sfroCwbHQO4a0g4",
        "00u6yl0Q065H4BCPR0g4"
      ],
      "resource_type": "app",
      "resource_ids": ["0oa1234567890abcdef"],
      "app_type": "saml2"
    }
  ]
}
```

#### Assign Group Owners

```json
{
  "resource_owners": [
    {
      "description": "Engineering team group owner",
      "principal_type": "user",
      "principal_ids": ["00u10sfroCwbHQO4a0g4"],
      "resource_type": "group",
      "resource_ids": ["00g1234567890abcdef"]
    }
  ]
}
```

#### Assign Group as Owner (Delegated Ownership)

```json
{
  "resource_owners": [
    {
      "description": "Admin group owns production apps",
      "principal_type": "group",
      "principal_ids": ["00g10ctakVI6XlTdk0g4"],
      "resource_type": "app",
      "resource_ids": [
        "0oa1111111111111111",
        "0oa2222222222222222"
      ],
      "app_type": "oauth2"
    }
  ]
}
```

### Labels

#### Create Governance Labels

```json
{
  "labels": [
    {
      "name": "high-risk",
      "description": "High-risk applications requiring strict governance"
    },
    {
      "name": "pci-compliant",
      "description": "Resources subject to PCI DSS compliance"
    },
    {
      "name": "production",
      "description": "Production environment resources"
    }
  ]
}
```

#### Apply Labels to Applications

```json
{
  "label_assignments": [
    {
      "label_name": "high-risk",
      "resource_type": "app",
      "resource_ids": [
        "0oa1234567890abcdef",
        "0oa9876543210fedcba"
      ],
      "app_type": "saml2"
    }
  ]
}
```

#### Apply Labels to Groups

```json
{
  "label_assignments": [
    {
      "label_name": "production",
      "resource_type": "group",
      "resource_ids": [
        "00g1234567890abcdef",
        "00g9876543210fedcba"
      ]
    }
  ]
}
```

#### Apply Multiple Labels

```json
{
  "label_assignments": [
    {
      "label_name": "production",
      "resource_type": "app",
      "resource_ids": ["0oa1234567890abcdef"],
      "app_type": "oauth2"
    },
    {
      "label_name": "pci-compliant",
      "resource_type": "app",
      "resource_ids": ["0oa1234567890abcdef"],
      "app_type": "oauth2"
    },
    {
      "label_name": "customer-data",
      "resource_type": "app",
      "resource_ids": ["0oa1234567890abcdef"],
      "app_type": "oauth2"
    }
  ]
}
```

## 🎯 Use Cases

### Use Case 1: Automated Owner Assignment for New Apps

When creating apps via Terraform, automatically assign owners:

```hcl
resource "okta_app_oauth" "new_app" {
  label = "New Application"
  type  = "web"
  # ... other config
}

locals {
  new_app_owners = [{
    app_name       = okta_app_oauth.new_app.label
    app_id         = okta_app_oauth.new_app.id
    app_type       = "oauth2"
    owner_user_ids = [
      var.app_owner_id,
      var.backup_owner_id
    ]
  }]
}
```

**Benefits:**
- Ensures all apps have designated owners
- Automatic reviewer assignment for access certifications
- Clear accountability for app management

### Use Case 2: Compliance Labeling

Automatically label apps based on compliance requirements:

```hcl
locals {
  pci_apps = [
    okta_app_oauth.payment_system.id,
    okta_app_saml.billing_system.id
  ]
  
  sox_apps = [
    okta_app_saml.financial_reporting.id,
    okta_app_oauth.accounting_system.id
  ]
  
  compliance_labels = [
    {
      label_name = "pci-compliant"
      app_ids    = local.pci_apps
      app_type   = "oauth2"
    },
    {
      label_name = "sox-compliant"
      app_ids    = local.sox_apps
      app_type   = "saml2"
    }
  ]
}
```

**Benefits:**
- Consistent compliance tracking
- Easy filtering in access reviews
- Audit trail for compliance resources

### Use Case 3: Environment-Based Labeling

Label resources by environment:

```hcl
locals {
  production_resources = {
    apps = [
      okta_app_oauth.prod_api.id,
      okta_app_saml.prod_portal.id
    ]
    groups = [
      okta_group.prod_users.id,
      okta_group.prod_admins.id
    ]
  }
  
  environment_labels = [
    {
      label_name = "production"
      app_ids    = local.production_resources.apps
      app_type   = "oauth2"
    },
    {
      label_name = "production"
      group_ids  = local.production_resources.groups
    }
  ]
}
```

### Use Case 4: Delegated Group Ownership

Assign group ownership to team leads:

```hcl
locals {
  team_group_owners = [
    {
      group_name     = "Engineering Team"
      group_id       = okta_group.engineering.id
      owner_user_ids = [var.engineering_lead_id]
    },
    {
      group_name     = "Sales Team"
      group_id       = okta_group.sales.id
      owner_user_ids = [var.sales_lead_id]
    },
    {
      group_name     = "HR Team"
      group_id       = okta_group.hr.id
      owner_user_ids = [var.hr_director_id]
    }
  ]
}
```

**Benefits:**
- Decentralized group management
- Owners automatically review group memberships
- Clear escalation path for access requests

## 🔍 Querying Resource Owners and Labels

### Query via Python Script

```bash
# Query all resource owners and labels
python3 scripts/okta_api_manager.py \
  --action query \
  --config api_config.json
```

### Query via API (curl examples)

```bash
# List all labels
curl -X GET "https://your-org.okta.com/governance/api/v1/labels?limit=200" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  -H "Accept: application/json"

# List resource owners for an app
APP_ORN="orn:okta:idp:your-org:apps:oauth2:0oa1234567890abcdef"
FILTER="parentResourceOrn%20eq%20%22${APP_ORN}%22"

curl -X GET "https://your-org.okta.com/governance/api/v1/resource-owners?filter=${FILTER}" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  -H "Accept: application/json"

# List resources with a specific label
curl -X GET "https://your-org.okta.com/governance/api/v1/labels/high-risk/resources?limit=200" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  -H "Accept: application/json"

# List resources without owners
curl -X GET "https://your-org.okta.com/governance/api/v1/resource-owners/catalog/resources?filter=${FILTER}" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  -H "Accept: application/json"
```

### Query via Terraform Data Source

```hcl
data "external" "app_owners" {
  program = [
    "python3",
    "${path.module}/scripts/okta_api_manager.py",
    "--action", "query",
    "--config", local_file.api_config.filename
  ]
}

output "current_owners" {
  value = data.external.app_owners.result
}
```

## 🔐 Security Best Practices

### 1. Credential Management

```hcl
# ✅ GOOD: Use variables and environment variables
variable "okta_api_token" {
  type      = string
  sensitive = true
}

# ❌ BAD: Never hardcode tokens
# okta_api_token = "00abcd1234..."
```

### 2. File Permissions

```bash
# Set restrictive permissions on config files
chmod 600 api_config.json
chmod 600 terraform.tfvars

# Add to .gitignore
echo "api_config.json" >> .gitignore
echo "*.tfvars" >> .gitignore
```

### 3. Least Privilege

Ensure API token has only required scopes:
- `okta.governance.accessRequests.manage`
- `okta.governance.accessReviews.manage`
- `okta.governance.catalogs.manage`
- `okta.governance.resources.manage`
- `okta.apps.read` (if querying apps)
- `okta.groups.read` (if querying groups)

### 4. Audit Logging

Monitor API calls in Okta System Log:
```
Target: governance/api/v1/resource-owners
Target: governance/api/v1/labels
```

## 🐛 Troubleshooting

### Issue: Rate Limiting

**Error:** `429 Too Many Requests`

**Solution:**
The Python script includes automatic retry with exponential backoff. For large deployments:

```python
# Adjust in okta_api_manager.py
max_retries = 5  # Increase retries
retry_delay = 5  # Increase base delay
```

### Issue: Invalid ORN Format

**Error:** `Invalid resource ORN`

**Solution:**
Verify ORN format matches Okta's specification:
- Apps: `orn:okta:idp:${org}:apps:${type}:${id}`
- Groups: `orn:okta:directory:${org}:groups:${id}`
- Users: `orn:okta:directory:${org}:users:${id}`

```bash
# Debug ORN generation
terraform console
> local.demo_app_owners[0].app_id
> "orn:okta:idp:${var.okta_org_name}:apps:oauth2:${okta_app_oauth.demo_app.id}"
```

### Issue: Owners Not Appearing in UI

**Symptom:** API calls succeed but owners don't show in Okta Admin Console

**Solution:**
- Clear browser cache
- Wait 1-2 minutes for UI sync
- Verify via API query
- Check that OIG is fully enabled in your org

### Issue: Label Already Exists

**Error:** `409 Conflict - Label already exists`

**Solution:**
Script handles this gracefully. To delete and recreate:

```bash
# Labels don't have a DELETE endpoint yet
# Must remove via Okta Admin Console
```

### Issue: Python Script Not Found

**Error:** `No such file or directory: scripts/okta_api_manager.py`

**Solution:**
```bash
# Verify file location
ls -la scripts/okta_api_manager.py

# Ensure execute permissions
chmod +x scripts/okta_api_manager.py

# Test the script
python3 scripts/okta_api_manager.py --help
```

## 📊 Monitoring and Reporting

### Create Compliance Report

```python
# compliance_report.py
import json
from okta_api_manager import OktaAPIManager

manager = OktaAPIManager(org_name, base_url, api_token)

# Get all labels
labels = manager.list_labels()

# For each compliance label, list resources
for label in labels['data']:
    if 'compliant' in label['name']:
        resources = manager.list_resources_by_label(label['name'])
        print(f"\n{label['name']}: {len(resources['data'])} resources")
        
# Find resources without owners
unassigned = manager.list_unassigned_resources(parent_orn)
print(f"\nResources without owners: {len(unassigned['data'])}")
```

### Automated Ownership Audit

```bash
#!/bin/bash
# audit_owners.sh

echo "=== Resource Owner Audit ==="
python3 scripts/okta_api_manager.py --action query --config api_config.json | \
  jq '.resource_owners[] | {resource: .resource.id, owners: [.principals[].email]}'
```

## 🚀 CI/CD Integration

The Python script integrates seamlessly with GitHub Actions (already included in the main workflow).

### Additional CI/CD Examples

#### GitLab CI

```yaml
apply_api_config:
  stage: apply
  script:
    - pip install requests
    - python3 scripts/okta_api_manager.py --action apply --config api_config.json
  only:
    - main
```

#### Jenkins

```groovy
stage('Apply OIG API Config') {
    steps {
        sh '''
            pip3 install requests
            python3 scripts/okta_api_manager.py \
              --action apply \
              --config api_config.json \
              --org-name ${OKTA_ORG_NAME} \
              --api-token ${OKTA_API_TOKEN}
        '''
    }
}
```

## 📚 API Reference

### Resource Owners API

- **Endpoint:** `/governance/api/v1/resource-owners`
- **Documentation:** [Okta Resource Owners API](https://developer.okta.com/docs/api/iga/openapi/governance.api/tag/Resource-Owners/)

### Labels API

- **Endpoint:** `/governance/api/v1/labels`
- **Documentation:** [Okta Labels API](https://developer.okta.com/docs/api/iga/openapi/governance.api/tag/Labels/)

## 🎓 Best Practices Summary

1. **Always assign owners** to resources for clear accountability
2. **Use labels consistently** across environments
3. **Automate ownership assignment** during resource creation
4. **Regular audits** of unassigned resources
5. **Leverage labels in reviews** for scoped certifications
6. **Document label taxonomy** for organization-wide consistency
7. **Version control** API configurations alongside Terraform
8. **Test in non-production** before applying to production
9. **Monitor API rate limits** in high-volume environments
10. **Keep Python script updated** with latest API changes

## 🔄 Migration Guide

### Migrating Existing Manual Configurations

If you have existing resource owners or labels configured manually:

#### Step 1: Audit Current State

```bash
# Export current labels
curl -X GET "https://your-org.okta.com/governance/api/v1/labels?limit=200" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  -H "Accept: application/json" > current_labels.json

# Export current resource owners for your apps
for app_id in $(terraform state list | grep okta_app); do
  app_id_value=$(terraform state show $app_id | grep "id " | head -1 | awk '{print $3}' | tr -d '"')
  curl -X GET "https://your-org.okta.com/governance/api/v1/resource-owners?filter=parentResourceOrn%20eq%20%22orn:okta:idp:your-org:apps:oauth2:${app_id_value}%22" \
    -H "Authorization: SSWS ${OKTA_API_TOKEN}" >> current_owners.json
done
```

#### Step 2: Create Configuration

```bash
# Convert exported data to config format
python3 scripts/convert_to_config.py \
  --labels current_labels.json \
  --owners current_owners.json \
  --output migration_config.json
```

#### Step 3: Import to Terraform

```hcl
# Reference existing configurations
locals {
  migrated_owners = jsondecode(file("${path.module}/migration_config.json")).resource_owners
  migrated_labels = jsondecode(file("${path.module}/migration_config.json")).labels
}

module "api_management" {
  source = "./modules/api-management"
  
  # Merge migrated with new configs
  app_owner_configs = concat(
    local.migrated_owners,
    local.new_owners
  )
}
```

#### Step 4: Validate No Changes

```bash
# Should show no changes if migration successful
terraform plan

# Verify via Python script
python3 scripts/okta_api_manager.py --action query --config api_config.json
```

## 📖 Advanced Examples

### Example 1: Dynamic Owner Assignment Based on App Name

```hcl
locals {
  # Parse app names to determine owners
  app_owner_mapping = {
    "prod-"  = var.production_team_leads
    "dev-"   = var.development_team_leads
    "test-"  = var.qa_team_leads
  }
  
  # Dynamically assign owners based on app naming convention
  dynamic_app_owners = [
    for app in [okta_app_oauth.apps] : {
      app_name       = app.label
      app_id         = app.id
      app_type       = "oauth2"
      owner_user_ids = lookup(
        local.app_owner_mapping,
        [for prefix, owners in local.app_owner_mapping : 
          prefix if startswith(lower(app.label), prefix)
        ][0],
        var.default_owners
      )
    }
  ]
}
```

### Example 2: Conditional Labeling with Terraform Conditionals

```hcl
locals {
  # Conditionally apply labels based on app properties
  compliance_labels = flatten([
    for app_id, app_config in var.apps : [
      # Always production if in prod environment
      var.environment == "production" ? {
        label_name = "production"
        app_ids    = [app_id]
        app_type   = app_config.type
      } : null,
      
      # PCI if handles payments
      app_config.handles_payments ? {
        label_name = "pci-compliant"
        app_ids    = [app_id]
        app_type   = app_config.type
      } : null,
      
      # High-risk if has admin privileges
      app_config.admin_access ? {
        label_name = "high-risk"
        app_ids    = [app_id]
        app_type   = app_config.type
      } : null,
    ] if app_config != null
  ])
  
  # Filter out null values
  filtered_labels = [for label in local.compliance_labels : label if label != null]
}
```

### Example 3: Multi-Owner Governance Structure

```hcl
locals {
  # Primary and backup owners for business continuity
  critical_app_owners = [
    {
      app_name       = "Production Database"
      app_id         = okta_app_saml.prod_db.id
      app_type       = "saml2"
      owner_user_ids = [
        var.primary_dba_id,
        var.backup_dba_id,
        var.security_lead_id,      # Security oversight
        var.compliance_officer_id  # Compliance oversight
      ]
    }
  ]
  
  # Group-based ownership with delegation
  delegated_ownership = [
    {
      app_name       = "Employee Portal"
      app_id         = okta_app_oauth.employee_portal.id
      app_type       = "oauth2"
      owner_user_ids = []  # Use group instead
    }
  ]
  
  # Actually use group ownership
  group_based_ownership = {
    principal_type = "group"
    principal_ids  = [okta_group.app_owners.id]
    resource_type  = "app"
    resource_ids   = [okta_app_oauth.employee_portal.id]
    app_type       = "oauth2"
  }
}
```

### Example 4: Label Hierarchy and Taxonomy

```hcl
locals {
  # Structured label taxonomy
  label_taxonomy = {
    # Environment labels
    environment = ["production", "staging", "development", "sandbox"]
    
    # Compliance labels
    compliance = ["pci-compliant", "sox-compliant", "hipaa-compliant", "gdpr-compliant"]
    
    # Risk classification
    risk = ["high-risk", "medium-risk", "low-risk"]
    
    # Data classification
    data = ["customer-data", "financial-data", "hr-data", "public-data"]
    
    # Department ownership
    department = ["engineering", "sales", "finance", "hr", "marketing"]
  }
  
  # Flatten for creation
  all_labels = flatten([
    for category, labels in local.label_taxonomy : [
      for label in labels : {
        name        = label
        description = "${title(category)} label: ${label}"
      }
    ]
  ])
  
  # Create smart label assignments
  production_financial_apps = {
    label_names = ["production", "financial-data", "sox-compliant", "high-risk"]
    app_ids     = [okta_app_saml.accounting.id, okta_app_oauth.billing.id]
    app_type    = "oauth2"
  }
}
```

### Example 5: Automated Cleanup of Unassigned Resources

```hcl
# Data source to find resources without owners
data "external" "unassigned_resources" {
  program = ["bash", "-c", <<-EOT
    python3 scripts/find_unassigned.py \
      --org-name ${var.okta_org_name} \
      --api-token ${var.okta_api_token}
  EOT
  ]
}

# Automatically assign default owner to unassigned resources
resource "null_resource" "auto_assign_owners" {
  count = length(jsondecode(data.external.unassigned_resources.result.resource_ids))
  
  provisioner "local-exec" {
    command = <<-EOT
      curl -X PUT "https://${var.okta_org_name}.okta.com/governance/api/v1/resource-owners" \
        -H "Authorization: SSWS ${var.okta_api_token}" \
        -H "Content-Type: application/json" \
        -d '{
          "principalOrns": ["orn:okta:directory:${var.okta_org_name}:users:${var.default_owner_id}"],
          "resourceOrns": ["${jsondecode(data.external.unassigned_resources.result.resource_ids)[count.index]}"]
        }'
    EOT
  }
}
```

## 🧪 Testing Guide

### Unit Testing the Python Script

```python
# test_okta_api_manager.py
import unittest
from unittest.mock import Mock, patch
from okta_api_manager import OktaAPIManager

class TestOktaAPIManager(unittest.TestCase):
    def setUp(self):
        self.manager = OktaAPIManager("test-org", "okta.com", "test-token")
    
    @patch('requests.Session.request')
    def test_assign_resource_owners(self, mock_request):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_request.return_value = mock_response
        
        result = self.manager.assign_resource_owners(
            ["orn:okta:directory:test-org:users:00u123"],
            ["orn:okta:idp:test-org:apps:oauth2:0oa456"]
        )
        
        self.assertEqual(result["success"], True)
    
    def test_build_user_orn(self):
        orn = self.manager.build_user_orn("00u123")
        self.assertEqual(orn, "orn:okta:directory:test-org:users:00u123")

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

```bash
#!/bin/bash
# integration_test.sh

set -e

echo "=== Integration Test: API Management ==="

# 1. Create test configuration
cat > test_config.json <<EOF
{
  "okta_org_name": "${OKTA_ORG_NAME}",
  "okta_api_token": "${OKTA_API_TOKEN}",
  "labels": [
    {"name": "test-label", "description": "Test label for integration testing"}
  ],
  "resource_owners": [
    {
      "principal_type": "user",
      "principal_ids": ["${TEST_USER_ID}"],
      "resource_type": "app",
      "resource_ids": ["${TEST_APP_ID}"],
      "app_type": "oauth2"
    }
  ],
  "label_assignments": [
    {
      "label_name": "test-label",
      "resource_type": "app",
      "resource_ids": ["${TEST_APP_ID}"],
      "app_type": "oauth2"
    }
  ]
}
EOF

# 2. Apply configuration
echo "Applying configuration..."
python3 scripts/okta_api_manager.py --action apply --config test_config.json

# 3. Query and verify
echo "Verifying configuration..."
python3 scripts/okta_api_manager.py --action query --config test_config.json

# 4. Cleanup
echo "Cleaning up..."
python3 scripts/okta_api_manager.py --action destroy --config test_config.json

# 5. Verify cleanup
echo "Verifying cleanup..."
python3 scripts/okta_api_manager.py --action query --config test_config.json

echo "✅ Integration test passed!"
```

## 📈 Performance Optimization

### Batch Operations

```python
# Optimize for bulk operations
def batch_assign_owners(manager, assignments, batch_size=10):
    """Assign owners in batches to respect rate limits"""
    for i in range(0, len(assignments), batch_size):
        batch = assignments[i:i + batch_size]
        
        for assignment in batch:
            manager.assign_resource_owners(
                assignment['principal_orns'],
                assignment['resource_orns']
            )
        
        # Small delay between batches
        time.sleep(1)
```

### Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def parallel_label_assignment(manager, assignments, max_workers=5):
    """Apply labels in parallel (with caution for rate limits)"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        
        for assignment in assignments:
            future = executor.submit(
                manager.apply_labels_to_resources,
                assignment['label_name'],
                assignment['resource_orns']
            )
            futures.append(future)
        
        for future in as_completed(futures):
            try:
                result = future.result()
                print(f"✓ Label applied: {result}")
            except Exception as e:
                print(f"✗ Error: {e}")
```

## 🎉 Summary

This API management solution provides:

✅ **Complete OIG Coverage** - Manage all aspects of Okta Identity Governance
✅ **Terraform Integration** - Native workflow with infrastructure as code
✅ **Automation Ready** - CI/CD compatible with error handling
✅ **Idempotent Operations** - Safe to re-run without side effects
✅ **Comprehensive Querying** - Audit and report on current state
✅ **Production Ready** - Rate limiting, retries, and error handling

## 🔗 Additional Resources

- [Okta Governance API Documentation](https://developer.okta.com/docs/api/iga/)
- [Terraform Okta Provider](https://registry.terraform.io/providers/okta/okta/latest/docs)
- [Python Requests Documentation](https://requests.readthedocs.io/)
- [Okta Identity Governance Guide](https://help.okta.com/oie/en-us/content/topics/identity-governance/governance-main.htm)

---

**Need Help?** Open an issue in the repository or consult the Okta Developer Forums.
