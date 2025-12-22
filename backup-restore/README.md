# Okta Tenant Backup and Restore

This folder contains two backup/restore approaches for Okta tenants managed via Terraform.

## Choose Your Approach

| Approach | Best For | Backup Size | Restore Speed | Complexity |
|----------|----------|-------------|---------------|------------|
| [Resource-Based](resource-based/) | Complete DR, Audit | Larger | Slower | Lower |
| [State-Based](state-based/) | Quick rollback | Smaller | Faster | Higher |

---

## Resource-Based Backup

**Location:** [`resource-based/`](resource-based/)

Exports all Okta resources to portable files (CSV, JSON, Terraform), then re-applies them during restore.

### How It Works

```
Backup:
  Okta Tenant → Export Scripts → CSV/JSON/TF Files → Git Commit

Restore:
  Backup Files → Import Scripts/Terraform Apply → Okta Tenant
```

### What Gets Backed Up

- Users (CSV format, compatible with `users_from_csv.tf`)
- Groups and memberships (JSON)
- App assignments (JSON)
- OIG resources: Entitlement bundles, access reviews (Terraform)
- Config: Resource owners, labels, risk rules (JSON)

### Advantages

- **Portable** - Backup files work across different S3 buckets/backends
- **Readable** - Human-readable CSV and JSON exports
- **Selective restore** - Choose which resources to restore
- **Audit-friendly** - Each file shows exactly what was backed up

### Disadvantages

- **Larger backups** - Exports all resource data
- **Slower restore** - Re-creates resources via API/Terraform
- **May lose relationships** - Some Okta-generated IDs may change on restore

### Quick Start

```bash
# Create backup
gh workflow run backup-tenant.yml \
  -f environment=myorg \
  -f commit_changes=true

# Restore (dry run first)
gh workflow run restore-tenant.yml \
  -f environment=myorg \
  -f snapshot_id=latest \
  -f dry_run=true
```

---

## State-Based Backup

**Location:** [`state-based/`](state-based/)

Captures the Terraform state version in S3, enabling instant rollback to previous states.

### How It Works

```
Backup:
  S3 State → Capture Version ID → Store in Manifest → Git Commit

Restore:
  Manifest → Get Version ID → Copy Old State as Current → Terraform Apply
```

### What Gets Backed Up

- S3 state version ID and metadata
- Optional: Downloaded state file copy
- Manifest with restore instructions

### Advantages

- **Instant rollback** - Restore state without re-importing
- **Smaller backups** - Only stores metadata (unless downloading state)
- **Faster restore** - Just copies S3 object version
- **Preserves IDs** - All Okta resource IDs remain intact

### Disadvantages

- **S3 dependency** - Requires S3 versioning enabled
- **Not portable** - Tied to specific S3 bucket
- **State-only** - Doesn't capture resources not in Terraform

### Quick Start

```bash
# Create backup
gh workflow run backup-tenant-state.yml \
  -f environment=myorg \
  -f commit_changes=true

# Restore (dry run first)
gh workflow run restore-tenant-state.yml \
  -f environment=myorg \
  -f snapshot_id=latest \
  -f restore_mode=state-only \
  -f dry_run=true
```

---

## Comparison Matrix

| Feature | Resource-Based | State-Based |
|---------|----------------|-------------|
| **Backup Contents** | Full resource export | State version ID |
| **Backup Size** | 100KB - 10MB+ | ~1KB (metadata) |
| **Backup Speed** | 2-10 min | Seconds |
| **Restore Speed** | 5-30 min | 1-5 min |
| **S3 Required** | No | Yes (versioning) |
| **Cross-Bucket** | Yes | No |
| **Selective Restore** | Yes | No (all or nothing) |
| **Preserves IDs** | No (may change) | Yes |
| **API Resources** | Yes | Partial |
| **Human Readable** | Yes | No |

---

## Recommended Strategy

### For Most Users: Use Both

1. **Daily**: State-based backups for quick rollbacks
2. **Weekly**: Resource-based backups for full DR

```yaml
# Enable both in your workflows:

# state-based/backup-tenant.yml
schedule:
  - cron: '0 3 * * *'  # Daily at 3 AM UTC

# resource-based/backup-tenant.yml
schedule:
  - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM UTC
```

### Recovery Scenarios

| Scenario | Use This |
|----------|----------|
| "I just applied bad changes, need to undo" | State-based |
| "Someone deleted resources, need them back" | Resource-based |
| "Migrating to new S3 bucket" | Resource-based |
| "Quick rollback after failed deploy" | State-based |
| "Audit: what did we have on date X?" | Resource-based |
| "Full disaster recovery" | Resource-based |

---

## Storage Structure

```
environments/{env}/backups/
├── latest/                    # Resource-based latest
│   ├── MANIFEST.json
│   ├── users.csv
│   ├── memberships.json
│   └── ...
├── snapshots/                 # Resource-based history
│   └── 2025-01-15T10-30-00/
└── state-based/               # State-based backups
    ├── latest/
    │   └── MANIFEST.json
    └── snapshots/
        └── 2025-01-15T10-30-00/
            └── MANIFEST.json
```

---

## Prerequisites

### For Resource-Based

- Python 3.11+
- Okta API token with admin access
- GitHub Environment secrets configured

### For State-Based

- All of the above, plus:
- S3 bucket with versioning enabled
- AWS credentials (OIDC via `AWS_ROLE_ARN`)
- boto3 Python package

---

## Troubleshooting

### "State version not found"

S3 versioning may not be enabled:
```bash
aws s3api get-bucket-versioning --bucket your-bucket
# Should show: {"Status": "Enabled"}
```

### "API authentication failed"

Check environment secrets:
- `OKTA_ORG_NAME`
- `OKTA_BASE_URL`
- `OKTA_API_TOKEN`

### "Restore changes nothing"

State may already be current:
```bash
# Check current version
aws s3api head-object \
  --bucket your-bucket \
  --key path/to/terraform.tfstate \
  --query 'VersionId'
```

---

## Related Documentation

- [AWS Backend Setup](../docs/AWS_BACKEND_SETUP.md) - S3 state backend configuration
- [Rollback Guide](../docs/ROLLBACK_GUIDE.md) - Manual rollback procedures
- [GitOps Workflow](../docs/03-WORKFLOWS-GUIDE.md) - Workflow reference
