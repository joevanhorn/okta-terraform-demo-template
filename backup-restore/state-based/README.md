# State-Based Backup and Restore

**Purpose:** Fast backup and restore using Terraform state versioning in S3.

This approach captures the S3 version ID of your Terraform state, enabling instant rollback to any previous state version.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Backup Workflow](#backup-workflow)
5. [Restore Workflow](#restore-workflow)
6. [CLI Usage](#cli-usage)
7. [How It Works](#how-it-works)
8. [Restore Modes](#restore-modes)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Okta Tenant    │────▶│  Terraform       │────▶│  S3 State       │
│                 │     │  Apply           │     │  (Versioned)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  MANIFEST.json  │◀────│  Backup Script   │◀────│  Version ID     │
│  (Git Commit)   │     │                  │     │  + Metadata     │
└─────────────────┘     └──────────────────┘     └─────────────────┘

Restore:
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  MANIFEST.json  │────▶│  Restore Script  │────▶│  Copy Version   │
│                 │     │                  │     │  as Current     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Terraform       │────▶│  Okta Tenant    │
                        │  Apply           │     │  (Rolled Back)  │
                        └──────────────────┘     └─────────────────┘
```

### Key Benefits

- **Instant Rollback** - Restore state without re-importing resources
- **Small Footprint** - Only stores metadata (~1KB per backup)
- **Preserves IDs** - All Okta resource IDs remain unchanged
- **Fast Recovery** - Restore in seconds, not minutes

---

## Prerequisites

1. **S3 Bucket with Versioning Enabled**
   ```bash
   aws s3api put-bucket-versioning \
     --bucket your-bucket \
     --versioning-configuration Status=Enabled
   ```

2. **AWS Credentials**
   - `AWS_ROLE_ARN` secret in GitHub Environment
   - Or local AWS credentials for CLI usage

3. **Python 3.11+ with boto3**
   ```bash
   pip install boto3
   ```

---

## Quick Start

### Create a Backup

```bash
# Via GitHub Workflow
gh workflow run backup-tenant-state.yml \
  -f environment=myorg \
  -f commit_changes=true

# Via CLI
python backup-restore/state-based/scripts/backup_state.py \
  --environment myorg \
  --output-dir environments/myorg/backups/state-based/latest \
  --state-bucket okta-terraform-demo \
  --state-key Okta-GitOps/myorg/terraform.tfstate
```

### View Backup

```bash
# View manifest
cat environments/myorg/backups/state-based/latest/MANIFEST.json | jq

# List available state versions
python backup-restore/state-based/scripts/restore_state.py \
  --state-bucket okta-terraform-demo \
  --state-key Okta-GitOps/myorg/terraform.tfstate \
  --list-versions
```

### Restore (Dry Run First!)

```bash
# Via GitHub Workflow
gh workflow run restore-tenant-state.yml \
  -f environment=myorg \
  -f snapshot_id=latest \
  -f restore_mode=state-only \
  -f dry_run=true

# Via CLI
python backup-restore/state-based/scripts/restore_state.py \
  --manifest environments/myorg/backups/state-based/latest/MANIFEST.json \
  --restore-state \
  --dry-run
```

---

## Backup Workflow

### Triggering Backups

**Manual backup:**
```bash
gh workflow run backup-tenant-state.yml \
  -f environment=myorg
```

**Via GitHub UI:**
1. Go to **Actions** → **Backup Tenant (State-Based)**
2. Click **Run workflow**
3. Select environment and options
4. Click **Run workflow**

### Backup Workflow Options

| Input | Description | Default |
|-------|-------------|---------|
| `environment` | Environment to backup | myorg |
| `schedule_type` | Metadata tag (manual/daily/weekly) | manual |
| `download_state` | Also download state file | false |
| `retention_count` | Snapshots to keep (0 = unlimited) | 30 |
| `commit_changes` | Commit backup to git | true |

### What Gets Captured

| Item | Always | Optional |
|------|--------|----------|
| S3 Version ID | ✅ | - |
| S3 ETag | ✅ | - |
| Last Modified | ✅ | - |
| State File Copy | - | `download_state=true` |

### Backup Outputs

- **Manifest** - `MANIFEST.json` with version info
- **Git Commit** - Backup committed to repository
- **Git Tag** - `backup-state/{env}/{timestamp}`
- **Artifact** - Downloadable from GitHub Actions

---

## Restore Workflow

### Triggering Restore

**Dry run (preview):**
```bash
gh workflow run restore-tenant-state.yml \
  -f environment=myorg \
  -f snapshot_id=latest \
  -f restore_mode=state-only \
  -f dry_run=true
```

**Actual restore:**
```bash
gh workflow run restore-tenant-state.yml \
  -f environment=myorg \
  -f snapshot_id=2025-01-15T10-30-00 \
  -f restore_mode=full-restore \
  -f dry_run=false
```

### Restore Workflow Options

| Input | Description | Default |
|-------|-------------|---------|
| `environment` | Environment to restore | myorg |
| `snapshot_id` | Snapshot ID or "latest" | latest |
| `restore_mode` | state-only or full-restore | state-only |
| `dry_run` | Preview without applying | true |

---

## CLI Usage

### Backup Script

```bash
# Basic backup
python backup-restore/state-based/scripts/backup_state.py \
  --environment myorg \
  --output-dir backups/latest \
  --state-bucket okta-terraform-demo \
  --state-key Okta-GitOps/myorg/terraform.tfstate

# With state file download
python backup-restore/state-based/scripts/backup_state.py \
  --environment myorg \
  --output-dir backups/latest \
  --state-bucket okta-terraform-demo \
  --state-key Okta-GitOps/myorg/terraform.tfstate \
  --download-state

# For local state (no S3)
python backup-restore/state-based/scripts/backup_state.py \
  --environment myorg \
  --output-dir backups/latest \
  --local-state environments/myorg/terraform/terraform.tfstate
```

### Restore Script

```bash
# List available versions
python backup-restore/state-based/scripts/restore_state.py \
  --state-bucket okta-terraform-demo \
  --state-key Okta-GitOps/myorg/terraform.tfstate \
  --list-versions

# Restore state only (from manifest)
python backup-restore/state-based/scripts/restore_state.py \
  --manifest backups/2025-01-15/MANIFEST.json \
  --restore-state \
  --dry-run

# Restore state only (from version ID)
python backup-restore/state-based/scripts/restore_state.py \
  --state-bucket okta-terraform-demo \
  --state-key Okta-GitOps/myorg/terraform.tfstate \
  --version-id "abc123..." \
  --restore-state

# Full restore (state + terraform apply)
python backup-restore/state-based/scripts/restore_state.py \
  --manifest backups/2025-01-15/MANIFEST.json \
  --full-restore \
  --terraform-dir environments/myorg/terraform \
  --auto-approve
```

---

## How It Works

### S3 Versioning

When versioning is enabled, S3 keeps every version of every object:

```
s3://bucket/path/terraform.tfstate
  ├── Version: abc123 (current)  ← After latest apply
  ├── Version: def456            ← Previous state
  ├── Version: ghi789            ← Even older
  └── Version: jkl012            ← And so on...
```

### Backup Process

1. **Get Current Version** - Query S3 for current version metadata
2. **Store in Manifest** - Save version ID, ETag, timestamps
3. **Optional: Download** - Copy state file if requested
4. **Commit to Git** - Version the manifest itself

### Restore Process

1. **Load Manifest** - Get target version ID
2. **Download Old Version** - Get state from target version
3. **Upload as New Current** - Copy creates new "current" version
4. **Optional: Terraform Apply** - Sync resources with restored state

**Important:** Restoring doesn't delete history. The old current version becomes part of the version history.

---

## Restore Modes

### State-Only (`--restore-state`)

Restores the S3 state file only. Use this when:
- You just need to rollback Terraform's view of resources
- Resources in Okta are already correct
- You'll manually run `terraform apply` later

```bash
python restore_state.py --manifest MANIFEST.json --restore-state
```

**After state-only restore:**
```bash
cd environments/myorg/terraform
terraform plan  # Shows what would change
terraform apply # Syncs resources with state
```

### Full Restore (`--full-restore`)

Restores state AND runs `terraform apply`. Use this when:
- You want complete automated rollback
- Resources in Okta need to be reverted
- You trust the backup completely

```bash
python restore_state.py --manifest MANIFEST.json --full-restore --auto-approve
```

---

## Manifest Format

```json
{
  "version": "2.0",
  "backup_type": "state-based",
  "snapshot_id": "2025-01-15T10-30-00",
  "environment": "myorg",
  "org_name": "dev-12345678",
  "created_at": "2025-01-15T10:30:00Z",
  "created_by": "github-actions",
  "schedule": "manual",
  "terraform_state": {
    "source": "s3",
    "bucket": "okta-terraform-demo",
    "key": "Okta-GitOps/myorg/terraform.tfstate",
    "region": "us-east-1",
    "version_id": "abc123def456...",
    "etag": "d41d8cd98f00b204e9800998ecf8427e",
    "last_modified": "2025-01-15T10:29:45Z",
    "content_length": 12345
  },
  "restore_instructions": {
    "state_restore": "Use restore_state.py --restore-state",
    "full_restore": "Use restore_state.py --full-restore"
  }
}
```

---

## Troubleshooting

### "Version ID is null"

S3 versioning may not be enabled:
```bash
# Check versioning status
aws s3api get-bucket-versioning --bucket your-bucket

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket your-bucket \
  --versioning-configuration Status=Enabled
```

### "Access Denied"

IAM permissions issue. Required actions:
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:GetObjectVersion",
    "s3:PutObject",
    "s3:ListBucketVersions"
  ],
  "Resource": [
    "arn:aws:s3:::your-bucket",
    "arn:aws:s3:::your-bucket/*"
  ]
}
```

### "State file not found"

Check the state key path:
```bash
aws s3 ls s3://your-bucket/Okta-GitOps/myorg/
```

### "Target version is already current"

The state is already at the target version. No action needed.

### "Terraform apply failed after restore"

The restored state may not match current Okta resources. Options:
1. Run `terraform plan` to see differences
2. Use resource-based backup for affected resources
3. Manually import resources: `terraform import <resource> <id>`

---

## Best Practices

1. **Always dry-run first** - Preview before actual restore
2. **Regular backups** - Enable scheduled backups (daily recommended)
3. **Test restores** - Periodically test restore to staging
4. **Monitor versions** - S3 lifecycle policies can delete old versions
5. **Combine approaches** - Use with resource-based backups for full DR

---

## Related Documentation

- [Resource-Based Backup](../resource-based/README.md) - Alternative approach
- [Main Backup Guide](../README.md) - Comparison of approaches
- [AWS Backend Setup](../../docs/AWS_BACKEND_SETUP.md) - S3 configuration
