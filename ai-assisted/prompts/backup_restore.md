# Backup and Restore Prompt Template

Use this template when the user wants to set up or execute backup/restore operations for their Okta tenant.

---

## Trigger Phrases

Respond to requests containing:
- "backup my Okta tenant"
- "restore from backup"
- "disaster recovery"
- "point-in-time recovery"
- "rollback changes"
- "snapshot my tenant"
- "export users for backup"
- "how do I backup"

---

## Context to Provide to AI

When the user asks about backup/restore, provide this context:

### Two Approaches Available

1. **Resource-Based Backup** (Full DR)
   - Exports all resources to CSV/JSON/Terraform files
   - Portable across different Okta orgs
   - Selective restore (choose what to restore)
   - Best for: Disaster recovery, audit/compliance, environment cloning

2. **State-Based Backup** (Quick Rollback)
   - Captures S3 state version ID
   - Instant rollback to previous state
   - Preserves resource IDs
   - Best for: Quick recovery from bad terraform apply

### Backup Storage Structure

```
environments/{env}/
├── terraform/              # Terraform-managed resources
├── config/                 # API-managed resources
└── backups/                # Backup snapshots
    ├── MANIFEST.json       # Snapshot metadata
    ├── latest/             # Most recent backup
    │   ├── users.csv
    │   ├── groups.json
    │   ├── memberships.json
    │   └── app_assignments.json
    └── snapshots/          # Historical snapshots
        └── 2025-12-22T10-30-00/
```

---

## Response Templates

### For "How do I backup my tenant?"

```markdown
There are two backup approaches available:

**1. Resource-Based Backup** (recommended for disaster recovery):
```bash
gh workflow run backup-tenant.yml \
  -f environment=<your-environment> \
  -f commit_changes=true
```

This exports:
- Users to CSV (compatible with users_from_csv.tf.example)
- Groups to JSON
- Group memberships
- App assignments
- OIG resources (bundles, reviews, owners, labels)

**2. State-Based Backup** (recommended for quick rollback):
```bash
gh workflow run backup-tenant-state.yml \
  -f environment=<your-environment> \
  -f commit_changes=true
```

This captures the S3 state version for instant rollback.

**Recommended Strategy:**
- Daily: State-based (quick protection)
- Weekly: Resource-based (full DR capability)
```

### For "How do I restore from backup?"

```markdown
**Resource-Based Restore** (selective, portable):
```bash
# Preview first (dry-run)
gh workflow run restore-tenant.yml \
  -f environment=<your-environment> \
  -f snapshot_id=latest \
  -f resources=all \
  -f dry_run=true

# Actual restore
gh workflow run restore-tenant.yml \
  -f environment=<your-environment> \
  -f snapshot_id=latest \
  -f resources=all \
  -f dry_run=false
```

**State-Based Restore** (quick rollback):
```bash
# State-only rollback (just reverts state)
gh workflow run restore-tenant-state.yml \
  -f environment=<your-environment> \
  -f snapshot_id=latest \
  -f restore_mode=state-only \
  -f dry_run=true

# Full restore (state + terraform apply)
gh workflow run restore-tenant-state.yml \
  -f environment=<your-environment> \
  -f snapshot_id=latest \
  -f restore_mode=full-restore \
  -f dry_run=false
```

**Important:** Always use dry_run=true first to preview changes!
```

### For "Rollback a bad terraform apply"

```markdown
If you need to quickly rollback a bad `terraform apply`:

**Quick Rollback (State-Based):**
```bash
# 1. List available snapshots
ls -la environments/<env>/backups/state/

# 2. Rollback to previous state
gh workflow run restore-tenant-state.yml \
  -f environment=<your-environment> \
  -f snapshot_id=<snapshot-id> \
  -f restore_mode=state-only \
  -f dry_run=true

# 3. If preview looks good, apply
gh workflow run restore-tenant-state.yml \
  -f environment=<your-environment> \
  -f snapshot_id=<snapshot-id> \
  -f restore_mode=state-only \
  -f dry_run=false

# 4. Run terraform plan to verify
cd environments/<env>/terraform
terraform plan
```

This restores the S3 state version, preserving all resource IDs.
```

### For "Export users for backup"

```markdown
To export users to CSV:

```bash
# Export all active users
python backup-restore/resource-based/scripts/export_users_to_csv.py \
  --output backups/users.csv \
  --include-groups \
  --include-manager

# Export with status filter
python backup-restore/resource-based/scripts/export_users_to_csv.py \
  --output backups/users.csv \
  --status ACTIVE \
  --include-groups
```

The CSV is compatible with `users_from_csv.tf.example` for restore.
```

---

## Common Scenarios

### Scenario 1: Set Up Scheduled Backups

```markdown
To enable scheduled backups:

1. **Daily State Backups** (quick rollback):
   Edit `backup-restore/state-based/backup-tenant.yml`:
   ```yaml
   on:
     schedule:
       - cron: '0 2 * * *'  # Daily at 2 AM UTC
   ```

2. **Weekly Resource Backups** (full DR):
   Edit `backup-restore/resource-based/backup-tenant.yml`:
   ```yaml
   on:
     schedule:
       - cron: '0 3 * * 0'  # Weekly on Sunday at 3 AM UTC
   ```

3. Commit and push changes to enable scheduled runs.
```

### Scenario 2: Clone Environment from Backup

```markdown
To clone an environment from a backup:

1. Create the new environment directory:
   ```bash
   mkdir -p environments/new-env/{terraform,imports,config}
   ```

2. Copy backup files:
   ```bash
   cp environments/source-env/backups/latest/users.csv \
      environments/new-env/terraform/users.csv
   ```

3. Update Terraform to use CSV:
   ```bash
   cp environments/myorg/terraform/users_from_csv.tf.example \
      environments/new-env/terraform/users_from_csv.tf
   ```

4. Set up GitHub Environment with new Okta tenant secrets

5. Apply:
   ```bash
   cd environments/new-env/terraform
   terraform init
   terraform apply
   ```
```

### Scenario 3: Verify Backup Integrity

```markdown
To verify a backup:

```bash
# Check manifest
cat environments/<env>/backups/latest/MANIFEST.json

# Verify checksums
python backup-restore/resource-based/scripts/verify_backup.py \
  --manifest environments/<env>/backups/latest/MANIFEST.json

# Count resources
wc -l environments/<env>/backups/latest/users.csv
jq '. | length' environments/<env>/backups/latest/groups.json
```
```

---

## What Gets Backed Up

| Resource Type | Resource-Based | State-Based |
|---------------|----------------|-------------|
| Users | CSV export | In state |
| Groups | JSON export | In state |
| Group Memberships | JSON export | In state |
| App Assignments | JSON export | In state |
| OAuth Apps | Terraform state | In state |
| Entitlement Bundles | Terraform state | In state |
| Access Reviews | Terraform state | In state |
| Resource Owners | JSON export | Not in state |
| Governance Labels | JSON export | Not in state |
| Risk Rules | JSON export | Not in state |

**Not Backed Up:**
- System apps (Okta-managed)
- Deprovisioned users (configurable)
- Access review decisions (ephemeral)
- Entitlement assignments/grants (managed in Okta UI)

---

## Troubleshooting

### Backup workflow fails

```markdown
1. **Check secrets**: Ensure OKTA_API_TOKEN, OKTA_ORG_NAME, OKTA_BASE_URL are set
2. **Check permissions**: Token needs read access to all resources
3. **Check S3 access**: For state-based, ensure AWS_ROLE_ARN is configured
```

### Restore gives "resource already exists"

```markdown
Resource-based restore creates NEW resources with new IDs.
If resources already exist, you'll get conflicts.

Options:
1. Use state-based restore (preserves IDs)
2. Delete existing resources first
3. Use terraform import to update state
```

### State restore fails with "version not found"

```markdown
S3 versioning must be enabled on the state bucket.
Check:
```bash
aws s3api get-bucket-versioning --bucket okta-terraform-demo
```

If not enabled, state-based restore won't work.
Use resource-based restore instead.
```
