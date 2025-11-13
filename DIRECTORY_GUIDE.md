# Environment-Based Directory Structure Guide

This repository uses an **environment-based structure** to organize Okta configurations by tenant.

---

## Overview

Instead of separating resources by type (basic vs. OIG), this repository organizes configurations by **environment** (tenant):

```
environments/
├── myorg/      # Primary demo tenant
│   ├── terraform/      # ALL Terraform configurations
│   ├── imports/        # Raw API import data
│   └── config/         # Resource owners and labels
├── production/         # Production tenant
├── staging/            # Staging tenant
└── development/        # Development tenant
```

---

## Structure Benefits

### 1. Multi-Tenant Management
- Each environment is completely self-contained
- Independent Terraform state per environment
- No cross-environment dependencies
- Easy to add new environments

### 2. Template-Friendly
- Fork and customize for your organization
- Remove unused environments
- Add your own tenant environments
- Clear separation of concerns

### 3. Simplified Workflows
- Single import workflow for all resources
- Consistent structure across environments
- Easy to compare configurations between environments
- No confusion about where files belong

---

## Directory Structure Explained

### `/terraform/`
Contains ALL Terraform configuration files for the environment:

**Auto-generated files (from import workflow):**
- `oig_entitlements.tf` - Entitlement bundle definitions
- `oig_reviews.tf` - Access review campaigns
- `oig_approval_sequences.tf` - Approval workflows

**User-created files (you create these):**
- `app_oauth.tf` - OAuth applications
- `user.tf` - User resources
- `group.tf` - Group resources
- `policies.tf` - Security policies
- etc.

**Required configuration:**
- `provider.tf` - Okta provider and S3 backend configuration
- `variables.tf` - Variable definitions

**Template files (for new organizations):**
- `QUICKSTART_DEMO.tf.example` - Ready-to-use demo (5 users, 3 groups, 1 app)
- `RESOURCE_EXAMPLES.tf` - Comprehensive reference with ALL Okta resource examples
- `README.md` - Guide explaining templates and best practices

**Everything is in one place** - no need to choose between directories.

**📝 New to Terraform?** See [terraform/README.md](./environments/myorg/terraform/README.md) for template usage guide.

### `/imports/`
Raw JSON data from API imports for reference:
- `entitlements.json` - Entitlement bundles API response
- `reviews.json` - Access reviews API response

These are kept for:
- Auditing and compliance
- Drift detection
- Historical reference
- Debugging import issues

### `/config/`
Configuration files for API-only resources:
- `owner_mappings.json` - Resource ownership assignments
- `label_mappings.json` - Governance label assignments
- `api_config.json` - API configuration (if needed)

These resources cannot be managed in Terraform and are applied via API scripts.

---

## Working with Environments

### Import Resources for an Environment

```bash
# Import all resources for MyOrg
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyOrg \
  -f update_terraform=true \
  -f commit_changes=true
```

This creates/updates:
- `environments/myorg/terraform/*.tf`
- `environments/myorg/imports/*.json`
- `environments/myorg/config/*.json`

### Apply Terraform for an Environment

```bash
# Navigate to environment
cd environments/myorg/terraform

# Initialize and apply
terraform init
terraform plan
terraform apply
```

### Add a New Environment

1. Create directory structure:
```bash
mkdir -p environments/mycompany/{terraform,imports,config}
```

2. Set up GitHub Environment:
- Go to Settings → Environments → New environment
- Name it "MyCompany" (matches directory name)
- Add environment secrets:
  - `OKTA_API_TOKEN`
  - `OKTA_ORG_NAME`
  - `OKTA_BASE_URL`

3. Run import workflow:
```bash
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyCompany \
  -f update_terraform=true \
  -f commit_changes=true
```

4. Review and apply:
```bash
cd environments/mycompany/terraform
terraform init
terraform plan
terraform apply
```

---

## Migration from Old Structure

If you forked this repo before the environment-based structure:

### Old Structure
```
production-ready/
├── oig_entitlements.tf
├── app_oauth.tf
└── ...

config/
├── owner_mappings.json
└── label_mappings.json
```

### New Structure
```
environments/
└── myorg/
    ├── terraform/
    │   ├── oig_entitlements.tf
    │   ├── app_oauth.tf
    │   └── ...
    └── config/
        ├── owner_mappings.json
        └── label_mappings.json
```

### Migration Steps

1. Create environment directory:
```bash
mkdir -p environments/myenv/{terraform,imports,config}
```

2. Move files:
```bash
# Move Terraform files
mv production-ready/*.tf environments/myenv/terraform/

# Move config files
mv config/*.json environments/myenv/config/
```

3. Update backend configuration:
```bash
cd environments/myenv/terraform
# Edit backend.tf to use environment-specific state
```

4. Reinitialize:
```bash
terraform init -migrate-state
```

---

## Common Scenarios

### Scenario 1: "I have one Okta tenant"

Use the `myorg/` environment as a template:
1. Rename it to match your tenant name
2. Update GitHub Environment secrets
3. Run import workflow
4. Manage with Terraform

### Scenario 2: "I have production and staging tenants"

Use both `production/` and `staging/` directories:
1. Set up GitHub Environments for each
2. Run import workflow for each tenant
3. Manage independently
4. Promote changes from staging → production

### Scenario 3: "I'm forking for my company"

1. Delete or rename example environments
2. Create your environment directories
3. Set up GitHub Environments
4. Import your Okta configurations
5. Customize as needed

---

## Best Practices

### 1. One Environment = One Tenant
Each environment directory should correspond to exactly one Okta tenant.

### 2. Independent State
Each environment should have its own Terraform state file. Never share state across environments.

### 3. Environment Secrets
Use GitHub Environments to manage per-tenant secrets securely.

### 4. Naming Convention
Environment directory names should match:
- GitHub Environment name (for secrets)
- Okta tenant name (for clarity)

Examples:
- `myorg` → MyOrg GitHub Environment (template example)
- `acme-prod` → AcmeProd GitHub Environment
- `customer-demo` → CustomerDemo GitHub Environment

### 5. Regular Imports
Run import workflows regularly to detect configuration drift:
```bash
# Weekly or after manual changes in Okta UI
gh workflow run import-all-resources.yml \
  -f tenant_environment=<YourEnvironment>
```

---

## Quick Reference

### What Goes Where

| Resource Type | Location | Import Method |
|--------------|----------|---------------|
| Terraform configs | `environments/<env>/terraform/` | Workflow |
| Raw API data | `environments/<env>/imports/` | Workflow |
| Resource owners | `environments/<env>/config/` | Workflow |
| Labels | `environments/<env>/config/` | Workflow |

### Workflow Commands

```bash
# Import all resources
gh workflow run import-all-resources.yml -f tenant_environment=<Env>

# Apply Terraform
cd environments/<env>/terraform && terraform apply

# Sync owners
python3 scripts/sync_owner_mappings.py \
  --output environments/<env>/config/owner_mappings.json

# Apply owners
python3 scripts/apply_resource_owners.py \
  --config environments/<env>/config/owner_mappings.json
```

---

## Summary

✅ **Do:**
- Organize by environment (tenant)
- Keep each environment self-contained
- Use GitHub Environments for secrets
- Run regular imports for drift detection

❌ **Don't:**
- Mix resources from different tenants
- Share Terraform state across environments
- Manually edit imported JSON files
- Commit sensitive data (use .gitignore)

---

Last updated: 2025-11-07
