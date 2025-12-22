# Backup and Restore Guide

**Purpose:** Comprehensive backup and disaster recovery for Okta tenants using Terraform.

This guide covers creating snapshots of your Okta configuration, scheduling automated backups, and restoring from backups when needed.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Backup Workflow](#backup-workflow)
4. [Restore Workflow](#restore-workflow)
5. [Scheduled Backups](#scheduled-backups)
6. [Backup Storage Structure](#backup-storage-structure)
7. [What Gets Backed Up](#what-gets-backed-up)
8. [What Doesn't Get Backed Up](#what-doesnt-get-backed-up)
9. [Disaster Recovery Scenarios](#disaster-recovery-scenarios)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### Use Cases

1. **Disaster Recovery** - Restore tenant after accidental deletion or misconfiguration
2. **Audit/Compliance** - Point-in-time snapshots for change tracking and compliance
3. **Environment Cloning** - Create copies of production config for dev/staging

### How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Okta Tenant   │────▶│  Backup Workflow │────▶│   Git + S3      │
│                 │     │  (Export Scripts)│     │   (Versioned)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Okta Tenant   │◀────│ Restore Workflow │◀────│  Select Snapshot│
│   (Restored)    │     │ (Apply Scripts)  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Key Features

- **Git-based versioning** - Every backup is a git commit with tag
- **Manifest file** - Single source of truth for snapshot contents
- **Selective restore** - Choose which resources to restore
- **Dry-run mode** - Preview changes before applying
- **Approval gates** - Restore requires manual approval

---

## Quick Start

### Create a Backup

```bash
# Manual backup (recommended for first backup)
gh workflow run backup-tenant.yml \
  -f environment=myorg \
  -f schedule_type=manual \
  -f commit_changes=true
```

### View Available Backups

```bash
# List backup snapshots
ls environments/myorg/backups/snapshots/

# View latest backup manifest
cat environments/myorg/backups/latest/MANIFEST.json | jq
```

### Restore from Backup

```bash
# Dry run first (preview changes)
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=latest \
  -f dry_run=true

# Actual restore (requires environment approval)
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=2025-01-15T10-30-00 \
  -f dry_run=false
```

---

## Backup Workflow

### Triggering Backups

**Manual backup:**
```bash
gh workflow run backup-tenant.yml \
  -f environment=myorg \
  -f schedule_type=manual \
  -f retention_count=30 \
  -f commit_changes=true
```

**Via GitHub UI:**
1. Go to **Actions** → **Backup Tenant**
2. Click **Run workflow**
3. Select environment and options
4. Click **Run workflow**

### Backup Workflow Options

| Input | Description | Default |
|-------|-------------|---------|
| `environment` | Environment to backup | myorg |
| `schedule_type` | Metadata tag (manual/daily/weekly) | manual |
| `retention_count` | Snapshots to keep (0 = unlimited) | 30 |
| `commit_changes` | Commit backup to git | true |

### What Happens During Backup

1. **Export Users** → `users.csv`
2. **Export Groups** → `memberships.json`
3. **Export App Assignments** → `app_assignments.json`
4. **Export OIG Resources** → `oig/*.tf` and `oig/*.json`
5. **Export Config** → `owner_mappings.json`, `label_mappings.json`, `risk_rules.json`
6. **Create Manifest** → `MANIFEST.json`
7. **Archive Snapshot** → `snapshots/{timestamp}/`
8. **Cleanup Old Snapshots** (based on retention)
9. **Commit and Tag** → `backup/{env}/{timestamp}`

### Backup Outputs

- **Artifacts** - Downloadable from GitHub Actions (90-day retention)
- **Git Commit** - Backup files committed to repository
- **Git Tag** - `backup/myorg/2025-01-15T10-30-00`
- **Summary** - Detailed report in GitHub Actions summary

---

## Restore Workflow

### Triggering Restore

**Dry run (preview):**
```bash
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=latest \
  -f resources=all \
  -f dry_run=true
```

**Actual restore:**
```bash
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=2025-01-15T10-30-00 \
  -f resources=all \
  -f dry_run=false
```

### Restore Workflow Options

| Input | Description | Default |
|-------|-------------|---------|
| `environment` | Environment to restore | myorg |
| `snapshot_id` | Snapshot ID or "latest" | latest |
| `resources` | Resources to restore (comma-separated) | all |
| `dry_run` | Preview without applying | true |

### Resource Selection

Restore specific resources by setting the `resources` input:

| Value | What's Restored |
|-------|-----------------|
| `all` | Everything |
| `users` | Users from CSV |
| `groups` | Group memberships |
| `apps` | App assignments |
| `oig` | Entitlement bundles, reviews, sequences |
| `config` | Owners, labels, risk rules |

**Examples:**
```bash
# Restore only users and groups
-f resources=users,groups

# Restore only OIG and config
-f resources=oig,config
```

### Restore Process

1. **Validate Snapshot** - Check snapshot exists, display manifest
2. **Approval Gate** - Wait for GitHub Environment approval
3. **Restore Users** - Apply users.csv via Terraform
4. **Restore Groups** - Import memberships via API
5. **Restore Config** - Apply owners, labels, risk rules
6. **Restore OIG** - Apply Terraform for bundles/reviews

### Important Notes

- **Dry run is default** - Always preview before actual restore
- **Approval required** - Restore uses GitHub Environment protection
- **Incremental** - Restore adds/updates, doesn't delete existing
- **State consistency** - Terraform state is updated during restore

---

## Scheduled Backups

### Enable Scheduled Backups

Edit `.github/workflows/backup-tenant.yml` and uncomment the schedule:

```yaml
on:
  schedule:
    # Daily at 2 AM UTC
    - cron: '0 2 * * *'
    # Weekly on Sunday at 2 AM UTC
    # - cron: '0 2 * * 0'
```

### Schedule Options

| Schedule | Cron Expression | Use Case |
|----------|-----------------|----------|
| Daily | `0 2 * * *` | Production tenants |
| Weekly | `0 2 * * 0` | Dev/staging tenants |
| Monthly | `0 2 1 * *` | Audit snapshots |

### Environment for Scheduled Runs

For scheduled backups, set a default environment in the workflow:

```yaml
environment:
  name: ${{ inputs.environment || 'production' }}
```

---

## Backup Storage Structure

```
environments/myorg/
├── terraform/           # Terraform configurations
├── config/              # API-managed resources
├── imports/             # Import data
└── backups/             # Backup snapshots
    ├── latest/          # Most recent backup
    │   ├── MANIFEST.json
    │   ├── users.csv
    │   ├── memberships.json
    │   ├── app_assignments.json
    │   ├── owner_mappings.json
    │   ├── label_mappings.json
    │   ├── risk_rules.json
    │   └── oig/
    │       ├── entitlements.tf
    │       ├── entitlements.json
    │       ├── reviews.tf
    │       └── reviews.json
    └── snapshots/       # Historical snapshots
        ├── 2025-01-15T10-30-00/
        ├── 2025-01-14T10-30-00/
        └── 2025-01-13T10-30-00/
```

### Manifest File

The `MANIFEST.json` file documents the snapshot:

```json
{
  "version": "1.0",
  "snapshot_id": "2025-01-15T10-30-00",
  "org_name": "dev-12345678",
  "created_at": "2025-01-15T10:30:00Z",
  "created_by": "github-actions",
  "schedule": "daily",
  "resources": {
    "users": { "count": 150, "file": "users.csv" },
    "memberships": { "count": 340, "file": "memberships.json" },
    "app_assignments": { "count": 89, "file": "app_assignments.json" }
  },
  "summary": {
    "total_files": 10,
    "total_resources": 650
  }
}
```

---

## What Gets Backed Up

### Terraform-Managed Resources

| Resource | Format | Restore Method |
|----------|--------|----------------|
| Users | CSV | `terraform apply` |
| Entitlement Bundles | .tf + .json | `terraform apply` |
| Access Reviews | .tf + .json | `terraform apply` |
| Approval Workflows | .tf + .json | `terraform apply` |
| Catalog Entries | .tf + .json | `terraform apply` |

### API-Managed Resources

| Resource | Format | Restore Method |
|----------|--------|----------------|
| Group Memberships | .json | `copy_group_memberships.py` |
| App Assignments | .json | Manual / API script |
| Resource Owners | .json | `apply_resource_owners.py` |
| Governance Labels | .json | `apply_admin_labels.py` |
| Risk Rules | .json | `apply_risk_rules.py` |

### Relationship Data

| Relationship | Backed Up | Notes |
|--------------|-----------|-------|
| User → Groups | ✅ | Via memberships.json |
| User → Manager | ✅ | Via users.csv manager_email |
| User → Apps | ✅ | Via app_assignments.json |
| Group → Apps | ✅ | Via app_assignments.json |

---

## What Doesn't Get Backed Up

### By Design (Not Backed Up)

| Resource | Reason |
|----------|--------|
| System Apps | Okta-managed, can't be modified |
| System Groups | Everyone, Administrators |
| Deprovisioned Users | Optional - configurable |
| Entitlement Grants | Managed in Okta UI |
| Access Review Decisions | Ephemeral workflow data |
| MFA Enrollments | User-specific, can't be restored |
| Credentials | Security - passwords, tokens |

### Recommendations

- **Entitlement Grants** - Document separately if needed for DR
- **MFA** - Users will need to re-enroll after restore
- **Credentials** - Use password reset workflows

---

## Disaster Recovery Scenarios

### Scenario 1: Accidental User Deletion

**Problem:** Accidentally deleted users via Terraform or Admin Console

**Recovery:**
```bash
# 1. Find backup with users
cat environments/myorg/backups/latest/MANIFEST.json | jq '.resources.users'

# 2. Dry run restore
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=latest \
  -f resources=users \
  -f dry_run=true

# 3. Review plan in Actions, then apply
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=latest \
  -f resources=users \
  -f dry_run=false
```

### Scenario 2: Bad Terraform Apply

**Problem:** Applied wrong configuration, need to rollback

**Recovery:**
```bash
# 1. Revert git commit
git log --oneline -5
git revert HEAD
git push

# 2. Restore from last good backup
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=2025-01-14T10-30-00 \
  -f dry_run=false
```

### Scenario 3: Complete Tenant Recovery

**Problem:** Need to restore entire tenant configuration

**Recovery:**
```bash
# 1. List available backups
ls environments/myorg/backups/snapshots/

# 2. View manifest for target backup
cat environments/myorg/backups/snapshots/2025-01-10T02-00-00/MANIFEST.json | jq

# 3. Dry run full restore
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=2025-01-10T02-00-00 \
  -f resources=all \
  -f dry_run=true

# 4. Review carefully, then apply
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=2025-01-10T02-00-00 \
  -f resources=all \
  -f dry_run=false

# 5. Verify in Okta Admin Console
```

### Scenario 4: Clone Environment

**Problem:** Create staging from production backup

**Steps:**
1. Run backup on production
2. Copy backup to staging environment directory
3. Update `MANIFEST.json` with staging org info
4. Run restore workflow on staging environment

---

## Troubleshooting

### Backup Issues

**"API authentication failed"**
- Check `OKTA_API_TOKEN` secret in GitHub Environment
- Verify token hasn't expired
- Ensure token has appropriate scopes

**"Environment not found"**
- Directory `environments/{name}` must exist
- GitHub Environment name must match directory

**"No changes to commit"**
- Backup completed but no new data
- Check if previous backup was recent

### Restore Issues

**"Snapshot not found"**
- Check snapshot ID format: `YYYY-MM-DDTHH-MM-SS`
- Use "latest" for most recent backup
- Verify snapshot directory exists

**"users_from_csv.tf not found"**
- Copy example: `cp users_from_csv.tf.example users_from_csv.tf`
- Ensure CSV-based user management is set up

**"Terraform state conflict"**
- Run `terraform state list` to check current state
- May need to import resources first
- Consider `terraform import` for specific resources

### Common Fixes

```bash
# Force unlock Terraform state
cd environments/myorg/terraform
terraform force-unlock <LOCK_ID>

# Refresh Terraform state
terraform refresh

# Import missing resource
terraform import okta_user.example "00uXXXXXXXX"
```

---

## CLI Commands Reference

### Backup Commands

```bash
# Manual backup
gh workflow run backup-tenant.yml \
  -f environment=myorg

# Backup with custom retention
gh workflow run backup-tenant.yml \
  -f environment=myorg \
  -f retention_count=90

# Export users locally
python scripts/export_users_to_csv.py \
  --output backups/users.csv

# Export app assignments locally
python scripts/export_app_assignments.py \
  --output backups/app_assignments.json
```

### Restore Commands

```bash
# Dry run restore
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=latest \
  -f dry_run=true

# Restore specific resources
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=latest \
  -f resources=users,groups \
  -f dry_run=false

# Restore from specific snapshot
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=2025-01-15T10-30-00 \
  -f dry_run=false
```

### View Backup Status

```bash
# List backups
ls -la environments/myorg/backups/snapshots/

# View manifest
jq . environments/myorg/backups/latest/MANIFEST.json

# Check backup workflow runs
gh run list --workflow=backup-tenant.yml

# View specific run
gh run view <run-id>
```

---

## Best Practices

1. **Regular Backups** - Enable daily scheduled backups for production
2. **Test Restores** - Periodically test restore to staging environment
3. **Monitor Backups** - Set up alerts for backup workflow failures
4. **Retention Policy** - Balance storage costs with recovery needs
5. **Document Exclusions** - Note what's not backed up for DR planning
6. **Pre-Change Backups** - Run manual backup before major changes
7. **Verify Manifests** - Check resource counts match expectations

---

## Related Documentation

- [ROLLBACK_GUIDE.md](./ROLLBACK_GUIDE.md) - Git and state rollback procedures
- [AWS_BACKEND_SETUP.md](./AWS_BACKEND_SETUP.md) - S3 state backend with versioning
- [GITOPS_WORKFLOW.md](./GITOPS_WORKFLOW.md) - Standard GitOps patterns
- [API_MANAGEMENT.md](./API_MANAGEMENT.md) - Python scripts reference
