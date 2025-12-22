# Prompt Template: Cross-Org Migration

Use this template when you need to copy resources between Okta organizations.

---

## Context Files to Paste First

Before using this prompt, paste these context files into your AI assistant:
1. `context/repository_structure.md`
2. `context/terraform_examples.md`

---

## Migration Planning

### Step 1: Define Your Migration

**Fill in the details:**

```
SOURCE ENVIRONMENT:
[e.g., production, demo-source]

TARGET ENVIRONMENT:
[e.g., staging, demo-target]

RESOURCES TO MIGRATE:
[Check all that apply]
- [ ] Groups
- [ ] Group memberships (user assignments)
- [ ] Entitlement bundle grants

MIGRATION PURPOSE:
[Choose one]
- Clone production to staging for testing
- Set up new demo environment from existing
- Merge two tenants
- Other: [describe]
```

---

### Step 2: Choose Your Scenario

#### Scenario A: Migrate Groups Only

**Example prompt:**
```
I need to copy all groups from my production tenant to staging.

Source environment: Production
Target environment: Staging

Requirements:
- Exclude system groups (Everyone, Administrators)
- Preserve group names and descriptions
- Generate Terraform configuration

Give me the commands to:
1. Export groups from source
2. Review what will be created
3. Apply to target
```

#### Scenario B: Migrate Groups + Memberships

**Example prompt:**
```
I need to copy groups AND their memberships from SourceDemo to TargetDemo.

Source: SourceDemo
Target: TargetDemo

Users already exist in both orgs with matching email addresses.

Give me the commands to:
1. Export groups to Terraform
2. Apply groups to target
3. Export memberships
4. Import memberships to target (matching by email)

Include dry-run steps.
```

#### Scenario C: Migrate Entitlement Bundle Grants

**Example prompt:**
```
I need to copy OIG entitlement bundle grants from ProductionOIG to StagingOIG.

Source: ProductionOIG
Target: StagingOIG

Bundles already exist in both orgs with matching names.
Users/groups already exist with matching names.

Exclude grants for these apps:
- System App
- Legacy App

Give me the migration commands with dry-run.
```

#### Scenario D: Complete Migration (All Resources)

**Example prompt:**
```
I need to clone my entire demo tenant to a new environment.

Source: demo-healthcare
Target: demo-healthcare-copy

Migrate in order:
1. Groups first
2. Group memberships second
3. Entitlement grants third

Give me the complete migration plan with commands.
```

---

## Workflow Commands

### Using the Consolidated Workflow

**Migrate groups:**
```bash
gh workflow run migrate-cross-org.yml \
  -f resource_type=groups \
  -f source_environment=SourceEnv \
  -f target_environment=TargetEnv \
  -f dry_run=true
```

**Migrate memberships:**
```bash
gh workflow run migrate-cross-org.yml \
  -f resource_type=memberships \
  -f source_environment=SourceEnv \
  -f target_environment=TargetEnv \
  -f dry_run=true
```

**Migrate grants:**
```bash
gh workflow run migrate-cross-org.yml \
  -f resource_type=grants \
  -f source_environment=SourceEnv \
  -f target_environment=TargetEnv \
  -f dry_run=true
```

---

## CLI Commands

### Export Groups to Terraform

```bash
# Export from source org
OKTA_ORG_NAME=source-org \
OKTA_BASE_URL=okta.com \
OKTA_API_TOKEN=$SOURCE_TOKEN \
python scripts/export_groups_to_terraform.py \
  --output environments/target/terraform/groups_imported.tf \
  --exclude-system
```

### Export/Import Group Memberships

```bash
# Export from source
OKTA_ORG_NAME=source-org \
OKTA_BASE_URL=okta.com \
OKTA_API_TOKEN=$SOURCE_TOKEN \
python scripts/copy_group_memberships.py export \
  --output memberships.json

# Import to target
OKTA_ORG_NAME=target-org \
OKTA_BASE_URL=okta.com \
OKTA_API_TOKEN=$TARGET_TOKEN \
python scripts/copy_group_memberships.py import \
  --input memberships.json \
  --dry-run
```

### Export/Import Entitlement Grants

```bash
# Export from source
OKTA_ORG_NAME=source-org \
OKTA_BASE_URL=okta.com \
OKTA_API_TOKEN=$SOURCE_TOKEN \
python scripts/copy_grants_between_orgs.py export \
  --output grants_export.json

# Import to target
OKTA_ORG_NAME=target-org \
OKTA_BASE_URL=okta.com \
OKTA_API_TOKEN=$TARGET_TOKEN \
python scripts/copy_grants_between_orgs.py import \
  --input grants_export.json \
  --exclude-apps "System App" \
  --dry-run
```

---

## Migration Order

**Critical: Follow this order to avoid dependency issues!**

```
1. GROUPS FIRST
   └── Creates group definitions in target org

2. MEMBERSHIPS SECOND
   └── Assigns users to groups (users must exist, groups must exist)

3. GRANTS THIRD
   └── Assigns bundles to users/groups (bundles must exist, principals must exist)
```

---

## Pre-Migration Checklist

Before migrating:
- [ ] Source org has Okta API token with admin access
- [ ] Target org has Okta API token with admin access
- [ ] GitHub Environments configured for both orgs
- [ ] Users exist in target org (for memberships)
- [ ] Bundles exist in target org (for grants)
- [ ] Reviewed exclusion lists (system groups, apps to skip)

---

## Post-Migration Verification

After migration:
- [ ] Groups created with correct names
- [ ] Group memberships match source
- [ ] Entitlement grants assigned correctly
- [ ] No duplicate resources
- [ ] Terraform state updated

**Verification commands:**
```bash
# Compare group counts
# Source
OKTA_API_TOKEN=$SOURCE_TOKEN python -c "
import requests
r = requests.get('https://source-org.okta.com/api/v1/groups',
  headers={'Authorization': 'SSWS $SOURCE_TOKEN'})
print(f'Source groups: {len(r.json())}')
"

# Target
OKTA_API_TOKEN=$TARGET_TOKEN python -c "
import requests
r = requests.get('https://target-org.okta.com/api/v1/groups',
  headers={'Authorization': 'SSWS $TARGET_TOKEN'})
print(f'Target groups: {len(r.json())}')
"
```

---

## Troubleshooting

### "Group not found in target"

The group doesn't exist in target org. Migrate groups first:
```bash
gh workflow run migrate-cross-org.yml \
  -f resource_type=groups \
  -f source_environment=Source \
  -f target_environment=Target \
  -f dry_run=false
```

### "User not found by email"

The user doesn't exist in target org with the same email. Options:
1. Create user in target org first
2. Skip that membership during import

### "Bundle not found in target"

The entitlement bundle doesn't exist in target. Create bundle first via Terraform or import.

---

## Related Documentation

- Cross-Org Migration Guide: `docs/CROSS_ORG_MIGRATION.md`
- Export Groups Script: `scripts/export_groups_to_terraform.py`
- Copy Memberships Script: `scripts/copy_group_memberships.py`
- Copy Grants Script: `scripts/copy_grants_between_orgs.py`
