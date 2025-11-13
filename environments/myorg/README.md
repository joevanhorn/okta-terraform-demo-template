# Production Environment (Template)

This is a template directory for your production Okta tenant. Follow the setup guide below to configure it for your organization.

## ⚠️ Setup Required

This directory contains template files only. Before using:

1. Configure GitHub Environment with secrets
2. Update Terraform provider configuration
3. Import resources from your Okta tenant

## Quick Setup Guide

### 1. Configure GitHub Environment

Go to **Settings > Environments** and create:

**Environment Name:** `Production`

**Required Secrets:**
- `OKTA_API_TOKEN` - Production Okta API token with governance scopes
- `OKTA_ORG_NAME` - Your Okta org name (e.g., `your-company`)
- `OKTA_BASE_URL` - Base URL (e.g., `okta.com` or `oktapreview.com`)

**Recommended Protection Rules:**
- ✅ Required reviewers (2+ for production)
- ✅ Wait timer (5-10 minutes for production changes)
- ✅ Restrict to protected branches only

### 2. Update Terraform Configuration

Edit `terraform/provider.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "okta-terraform-demo"
    key            = "Okta-GitOps/production/terraform.tfstate"  # ✓ Already correct
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }
}
```

The backend configuration is already set for production. No changes needed unless using a different S3 bucket.

### 3. Initialize Terraform

```bash
cd environments/myorg/terraform
terraform init
```

This connects to the S3 backend and initializes the state.

### 4. Import Resources from Okta

```bash
# Import all OIG resources
gh workflow run import-all-resources.yml \
  -f tenant_environment=Production \
  -f update_terraform=true \
  -f commit_changes=false

# Review the imported files before committing
```

### 5. Review and Apply

```bash
cd environments/myorg/terraform
terraform plan
terraform apply
```

## Directory Structure

```
production/
├── terraform/              # Terraform configurations
│   ├── provider.tf        # Provider and backend config
│   └── variables.tf       # Variable definitions
├── config/                # API-managed resources
│   ├── owner_mappings.json   # Resource owners (empty template)
│   └── label_mappings.json   # Governance labels (empty template)
├── imports/               # Raw API import data
│   └── README.md         # Import data documentation
└── README.md             # This file
```

## Current Status

| Component | Status | Action Needed |
|-----------|--------|---------------|
| GitHub Environment | ❌ Not configured | Create with secrets |
| Terraform State | ❌ Not initialized | Run `terraform init` |
| Resources | ❌ Empty | Import from Okta |
| Config Files | ⚠️ Templates only | Populate after import |

## Workflows

Once configured, use these workflows:

### Import Resources
```bash
gh workflow run import-all-resources.yml \
  -f tenant_environment=Production \
  -f update_terraform=true
```

### Apply Changes
```bash
gh workflow run terraform-apply-with-approval.yml \
  -f environment=production
```

### Manage Resource Owners
```bash
# Sync from Okta
python3 scripts/sync_owner_mappings.py \
  --output environments/myorg/config/owner_mappings.json

# Apply to Okta
gh workflow run apply-owners.yml \
  -f environment=production \
  -f dry_run=false
```

### Manage Labels
```bash
# Sync from Okta
python3 scripts/sync_label_mappings.py \
  --output environments/myorg/config/label_mappings.json

# Apply to Okta
gh workflow run apply-labels-from-config.yml \
  -f environment=production \
  -f dry_run=false
```

## Production Best Practices

### Security
- ✅ Use GitHub Environment protection rules with required approvers
- ✅ Enable wait timer for production changes (5-10 minutes)
- ✅ Rotate API tokens regularly (every 90 days)
- ✅ Use least-privilege API scopes
- ✅ Enable MFA for all admin accounts

### Change Management
- ✅ Always run in dry-run mode first
- ✅ Require peer review for all PRs
- ✅ Test changes in staging before production
- ✅ Document all changes in PR descriptions
- ✅ Schedule changes during maintenance windows

### State Management
- ✅ State stored in S3 with encryption
- ✅ DynamoDB locking prevents concurrent modifications
- ✅ State versioning enabled for rollback
- ✅ Never commit state files to Git
- ✅ Backup state files regularly

### Monitoring
- ✅ Review workflow run history regularly
- ✅ Monitor Okta System Log for changes
- ✅ Set up alerts for failed workflows
- ✅ Audit access to GitHub Environment secrets
- ✅ Track drift with regular imports

## Related Documentation

- [Main Environments README](../README.md)
- [GitOps Workflow Guide](../../docs/GITOPS_WORKFLOW.md)
- [Production Security Best Practices](../../docs/SECURITY.md) (if exists)
- [Workflow Documentation](../../docs/WORKFLOWS.md)

## Support

If you encounter issues:
1. Check [Troubleshooting Guide](../../docs/TROUBLESHOOTING.md)
2. Review [Lessons Learned](../../docs/LESSONS_LEARNED.md)
3. Search [GitHub Issues](https://github.com/joevanhorn/okta-terraform-complete-demo/issues)
4. Create a new issue with detailed logs
