# Cross-Org Migration Prompt Template

Use this template when the user wants to migrate resources between Okta organizations.

---

## Trigger Phrases

Respond to requests containing:
- "copy groups between orgs"
- "migrate from one Okta to another"
- "clone tenant"
- "copy users to another org"
- "sync groups between tenants"
- "migrate memberships"
- "copy entitlement grants"
- "cross-org migration"
- "copy from production to staging"

---

## Context to Provide to AI

When the user asks about cross-org migration, provide this context:

### Migration Capabilities

| Resource Type | Script | Workflow Support |
|---------------|--------|------------------|
| Groups | `export_groups_to_terraform.py` | Yes |
| Group Memberships | `copy_group_memberships.py` | Yes |
| Entitlement Bundle Grants | `copy_grants_between_orgs.py` | Yes |
| Users | `export_users_to_csv.py` | Manual |

### Important: Migration Order

Resources must be migrated in dependency order:

```
1. Groups      → No dependencies
2. Memberships → Requires groups to exist in target
3. Grants      → Requires bundles and principals (users/groups) to exist
```

### How Matching Works

Resources are matched between orgs by **name**, not ID:
- Groups: Matched by group name
- Users: Matched by email address
- Bundles: Matched by bundle name
- Apps: Matched by app label

---

## Response Templates

### For "How do I copy groups between orgs?"

```markdown
To copy groups from source to target org:

**Using Workflow:**
```bash
# Preview first
gh workflow run migrate-cross-org.yml \
  -f resource_type=groups \
  -f source_environment=SourceEnv \
  -f target_environment=TargetEnv \
  -f dry_run=true

# Apply
gh workflow run migrate-cross-org.yml \
  -f resource_type=groups \
  -f source_environment=SourceEnv \
  -f target_environment=TargetEnv \
  -f dry_run=false
```

**Using CLI:**
```bash
# Export from source (set source Okta credentials)
export OKTA_ORG_NAME=source-org
export OKTA_API_TOKEN=source-token

python scripts/export_groups_to_terraform.py \
  --output environments/target/terraform/groups_imported.tf \
  --exclude-system

# Apply to target
cd environments/target/terraform
terraform init
terraform apply
```

**What gets copied:**
- Group name
- Group description
- Custom profile attributes

**What doesn't get copied:**
- Group ID (new ID assigned)
- Group memberships (separate step)
- App assignments
```

### For "How do I copy group memberships?"

```markdown
To copy group memberships between orgs:

**Prerequisites:**
- Groups must exist in target org (run groups migration first)
- Users must exist in target org (matched by email)

**Using Workflow:**
```bash
# Preview first
gh workflow run migrate-cross-org.yml \
  -f resource_type=memberships \
  -f source_environment=SourceEnv \
  -f target_environment=TargetEnv \
  -f dry_run=true

# Apply
gh workflow run migrate-cross-org.yml \
  -f resource_type=memberships \
  -f source_environment=SourceEnv \
  -f target_environment=TargetEnv \
  -f dry_run=false
```

**Using CLI:**
```bash
# Export from source
export OKTA_ORG_NAME=source-org
export OKTA_API_TOKEN=source-token

python scripts/copy_group_memberships.py export \
  --output memberships.json

# Import to target
export OKTA_ORG_NAME=target-org
export OKTA_API_TOKEN=target-token

python scripts/copy_group_memberships.py import \
  --input memberships.json \
  --dry-run

# If dry-run looks good, remove --dry-run flag
```

**How matching works:**
- Groups: Matched by group name (case-sensitive)
- Users: Matched by email address (case-insensitive)

**Output reports:**
- Groups not found in target
- Users not found in target (email mismatch)
- Successfully added memberships
```

### For "How do I copy entitlement grants?"

```markdown
To copy entitlement bundle grants between orgs:

**Prerequisites:**
- Entitlement bundles must exist in target org (same names)
- Principal users/groups must exist in target org

**Using Workflow:**
```bash
# Preview first
gh workflow run migrate-cross-org.yml \
  -f resource_type=grants \
  -f source_environment=SourceEnv \
  -f target_environment=TargetEnv \
  -f dry_run=true

# Apply
gh workflow run migrate-cross-org.yml \
  -f resource_type=grants \
  -f source_environment=SourceEnv \
  -f target_environment=TargetEnv \
  -f dry_run=false
```

**Using CLI:**
```bash
# Export from source
export OKTA_ORG_NAME=source-org
export OKTA_API_TOKEN=source-token

python scripts/copy_grants_between_orgs.py export \
  --output grants_export.json

# Import to target
export OKTA_ORG_NAME=target-org
export OKTA_API_TOKEN=target-token

python scripts/copy_grants_between_orgs.py import \
  --input grants_export.json \
  --exclude-apps "System App Name" \
  --dry-run

# If dry-run looks good, remove --dry-run flag
```

**How matching works:**
- Bundles: Matched by bundle name
- Users: Matched by email address
- Groups: Matched by group name
- Apps: Matched by app label

**Exclusions:**
Use `--exclude-apps` to skip grants for specific apps (e.g., system apps).
```

---

## Complete Migration Workflow

### Full Migration from Source to Target

```markdown
Follow these steps in order:

**Step 1: Prepare Target Environment**
```bash
mkdir -p environments/target/{terraform,imports,config}
# Set up GitHub Environment with target Okta secrets
```

**Step 2: Migrate Groups**
```bash
gh workflow run migrate-cross-org.yml \
  -f resource_type=groups \
  -f source_environment=Source \
  -f target_environment=Target \
  -f dry_run=false
```

**Step 3: Create Users in Target**
Option A: Export/import via CSV
```bash
# Export users from source
python scripts/export_users_to_csv.py \
  --output users.csv --include-groups

# Import to target via Terraform
# See users_from_csv.tf.example
```

Option B: Create users via SCIM/HR sync

**Step 4: Migrate Group Memberships**
```bash
gh workflow run migrate-cross-org.yml \
  -f resource_type=memberships \
  -f source_environment=Source \
  -f target_environment=Target \
  -f dry_run=false
```

**Step 5: Create Entitlement Bundles in Target**
```bash
cd environments/target/terraform
terraform apply -target=okta_entitlement_bundle
```

**Step 6: Migrate Entitlement Grants**
```bash
gh workflow run migrate-cross-org.yml \
  -f resource_type=grants \
  -f source_environment=Source \
  -f target_environment=Target \
  -f dry_run=false
```

**Step 7: Verify**
- Check group memberships in Okta Admin
- Verify entitlement assignments
- Test app access
```

---

## Common Scenarios

### Scenario 1: Clone Production to Staging

```markdown
To clone production Okta to staging for testing:

```bash
# 1. Export groups
gh workflow run migrate-cross-org.yml \
  -f resource_type=groups \
  -f source_environment=Production \
  -f target_environment=Staging \
  -f dry_run=false

# 2. Create test users (or sync from HR)
# Staging usually has different users than production

# 3. Copy memberships (only works for users that exist in both)
gh workflow run migrate-cross-org.yml \
  -f resource_type=memberships \
  -f source_environment=Production \
  -f target_environment=Staging \
  -f dry_run=false

# 4. Copy grants
gh workflow run migrate-cross-org.yml \
  -f resource_type=grants \
  -f source_environment=Production \
  -f target_environment=Staging \
  -f dry_run=false
```

**Note:** Users are typically different in staging, so focus on groups and config.
```

### Scenario 2: Partial Migration (Groups Only)

```markdown
To copy just specific groups:

```bash
# Export groups with pattern filter
python scripts/export_groups_to_terraform.py \
  --output groups_imported.tf \
  --name-pattern "Marketing*" \
  --exclude-system
```

This exports only groups matching the pattern.
```

### Scenario 3: Audit Migration Before Apply

```markdown
To see what would be migrated without making changes:

```bash
# Export and review groups
python scripts/export_groups_to_terraform.py \
  --output review_groups.tf \
  --exclude-system

cat review_groups.tf

# Export and review memberships
python scripts/copy_group_memberships.py export \
  --output review_memberships.json

jq '.' review_memberships.json | head -50

# Export and review grants
python scripts/copy_grants_between_orgs.py export \
  --output review_grants.json

jq '.' review_grants.json | head -50
```
```

---

## Troubleshooting

### "Group not found in target org"

```markdown
The script matches groups by name. If names don't match exactly:

1. Check spelling (case-sensitive)
2. Check for leading/trailing spaces
3. Manually create the group in target if needed

**Workaround:** Create missing groups first:
```bash
gh workflow run migrate-cross-org.yml \
  -f resource_type=groups \
  -f source_environment=Source \
  -f target_environment=Target \
  -f dry_run=false
```
```

### "User not found" warnings

```markdown
Memberships migration matches users by email address.
If email addresses differ between orgs, users won't match.

**Check:**
```bash
# See which emails couldn't be matched
jq '.missing_users' migration_report.json
```

**Solutions:**
1. Create users with matching emails in target
2. Map emails manually via user attribute
3. Skip those memberships
```

### Rate limiting errors

```markdown
For large migrations, you may hit Okta rate limits.

**Solutions:**
1. Add delays:
   ```bash
   python scripts/copy_group_memberships.py import \
     --input memberships.json \
     --rate-limit 10  # requests per second
   ```

2. Run during off-hours

3. Split into batches:
   ```bash
   # Export specific groups
   python scripts/copy_group_memberships.py export \
     --output batch1.json \
     --groups "Group1,Group2,Group3"
   ```
```

### Grants failing for specific bundles

```markdown
Entitlement grants require exact bundle name match.

**Debug:**
```bash
# List bundle names in source
curl -X GET "https://${SOURCE_ORG}.okta.com/api/v1/governance/bundles" \
  -H "Authorization: SSWS ${SOURCE_TOKEN}" | jq '.[].name'

# List bundle names in target
curl -X GET "https://${TARGET_ORG}.okta.com/api/v1/governance/bundles" \
  -H "Authorization: SSWS ${TARGET_TOKEN}" | jq '.[].name'

# Compare
```

**If names don't match:** Rename bundles or update the mapping.
```

---

## What Gets Migrated

| Resource | Migrated | How Matched |
|----------|----------|-------------|
| Group names | Yes | Created new |
| Group descriptions | Yes | Created new |
| Group profiles | Yes | Created new |
| Group IDs | No | New ID assigned |
| User emails | Matched | By email address |
| Bundle names | Matched | By bundle name |
| Bundle IDs | No | Looked up by name |
| Grant relationships | Yes | Created new |
| App assignments | No | Manual |

---

## Security Considerations

```markdown
1. **API Token Security**
   - Use separate tokens for source and target
   - Use read-only token for source (export)
   - Tokens need appropriate scopes

2. **Data Sensitivity**
   - Review exported data before storing
   - Don't commit tokens to git
   - Use GitHub Environment secrets

3. **Approval Gates**
   - Always use dry_run=true first
   - Review changes before applying
   - Consider requiring approval for production targets
```
