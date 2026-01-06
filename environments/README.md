# ⚠️ Okta Tenants (NOT Application Environments)

> **CRITICAL:** Each folder in this directory represents a **separate Okta organization/tenant**, NOT dev/staging/prod environments of your application.

## Quick Reference

| Folder | Okta Organization | Purpose |
|--------|------------------|---------|
| `myorg/` | myorg.oktapreview.com | Example template environment (replace with your org) |

**One Folder = One Complete Okta Tenant**

Each folder manages ALL resources for that specific Okta organization, including users, groups, applications, policies, and OIG resources.

---

## Overview

Each directory under `environments/` represents a **separate Okta organization** with its own complete set of terraform-managed resources. This ensures complete isolation between different Okta tenants.

## Environment Structure

```
environments/
└── myorg/          # Example template environment
    ├── terraform/          # Okta Terraform configurations
    │   ├── oig_entitlements.tf
    │   ├── provider.tf
    │   └── variables.tf
    ├── infrastructure/     # AWS infrastructure (optional)
    │   ├── provider.tf
    │   ├── vpc.tf
    │   ├── security-groups.tf
    │   └── ad-domain-controller.tf
    ├── config/             # API-managed resources (owners, labels, risk rules)
    │   ├── owner_mappings.json
    │   ├── label_mappings.json
    │   └── risk_rules.json
    └── imports/            # Raw API import data (JSON snapshots)
```

## Critical Rules for Environment Isolation

### 1. One Directory = One Okta Org

Each environment directory manages resources for **exactly one** Okta organization:
- `myorg/` → Example template (replace with your org name)
- Add additional directories as needed for your organizations

**❌ NEVER** mix resources from different Okta orgs in the same directory.

### 2. Environment-Specific Secrets

Each environment MUST use GitHub Environment secrets, NOT repository secrets.

#### Configuring GitHub Environments

Go to: **Settings > Environments**

**Example: MyOrg Environment**
- **Environment Name:** `MyOrg` (matches directory name, case-insensitive)
- **Secrets:**
  - `OKTA_API_TOKEN` = myorg API token
  - `OKTA_BASE_URL` = `oktapreview.com`
  - `OKTA_ORG_NAME` = `myorg`

**Example: Production Environment**
- **Environment Name:** `Production`
- **Secrets:**
  - `OKTA_API_TOKEN` = production API token
  - `OKTA_BASE_URL` = `okta.com`
  - `OKTA_ORG_NAME` = `your-org`

### 3. Workflow Environment Specification

All workflows MUST specify the environment to ensure correct secrets:

```yaml
jobs:
  terraform-plan:
    environment:
      name: ${{ inputs.environment }}
```

This guarantees:
- ✅ Correct Okta API credentials
- ✅ Resources created in correct org
- ✅ No cross-environment pollution

### 4. Independent Terraform State

Each environment has its own S3 state file:

```
s3://okta-terraform-demo/Okta-GitOps/
└── myorg/terraform.tfstate
    # Add more as needed:
    # demo/terraform.tfstate
    # customer1/terraform.tfstate
    # etc.
```

**Never share state across environments!**

## Adding a New Environment

To add a new Okta tenant (e.g., `demo`):

### 1. Create Directory Structure
```bash
mkdir -p environments/demo/{terraform,config,imports}
```

### 2. Copy Base Configuration
```bash
# Copy provider configuration
cp environments/myorg/terraform/provider.tf environments/demo/terraform/
cp environments/myorg/terraform/variables.tf environments/demo/terraform/

# Update backend key in provider.tf
sed -i 's|production|demo|g' environments/demo/terraform/provider.tf
```

### 3. Create Configuration Files
```bash
# Create empty config files
echo '{"assignments": {"apps": [], "groups": [], "entitlement_bundles": []}}' > \
  environments/demo/config/owner_mappings.json

echo '{"labels": [], "assignments": {}}' > \
  environments/demo/config/label_mappings.json

echo '{"description": "Risk rules (SOD policies)", "version": "1.0", "rules": []}' > \
  environments/demo/config/risk_rules.json
```

### 4. Configure GitHub Environment
1. Go to **Settings > Environments**
2. Click **New environment**
3. Name: `Demo` (matches directory name)
4. Add secrets:
   - `OKTA_API_TOKEN`
   - `OKTA_ORG_NAME`
   - `OKTA_BASE_URL`

### 5. Import Initial Resources
```bash
gh workflow run import-all-resources.yml \
  -f tenant_environment=Demo \
  -f update_terraform=true \
  -f commit_changes=true
```

## Common Misconceptions

### ❌ WRONG: "These are dev/staging/prod of my app"
These folders do NOT represent different deployment stages of your application.

### ✅ CORRECT: "These are completely separate Okta organizations"
Each folder manages a different Okta tenant, which might serve different purposes:
- Demo tenant for showcasing features
- Customer-specific tenant
- Geographic region-specific tenant
- Compliance-separated tenant

### Example Use Cases

**Multi-Customer SaaS:**
```
environments/
├── customer-acme/      # Acme Corp's dedicated Okta tenant
├── customer-globex/    # Globex Inc's dedicated Okta tenant
└── internal/           # Your company's internal Okta tenant
```

**Geographic Regions:**
```
environments/
├── us-east/            # US East region Okta tenant
├── eu-west/            # EU West region Okta tenant
└── apac/               # APAC region Okta tenant
```

**Compliance Separation:**
```
environments/
├── production-pci/     # PCI-compliant production tenant
├── production-hipaa/   # HIPAA-compliant production tenant
└── development/        # Non-production testing tenant
```

## Workflow Usage

All environment-agnostic workflows require an `environment` parameter:

```bash
# Apply resource owners to myorg
gh workflow run apply-owners.yml \
  -f environment=myorg \
  -f dry_run=false

# Apply resource owners to production
gh workflow run apply-owners.yml \
  -f environment=production \
  -f dry_run=false
```

The workflow automatically:
1. Uses the GitHub Environment secrets for that tenant
2. Operates on the correct Okta organization
3. Updates the correct Terraform state file

## Related Documentation

- [Workflows Guide](../docs/03-WORKFLOWS-GUIDE.md)
- [Directory Guide](../DIRECTORY_GUIDE.md)
- [GitOps Value](../docs/GITOPS_VALUE.md)
