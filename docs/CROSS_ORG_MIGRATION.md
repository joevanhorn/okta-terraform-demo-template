# Cross-Org Migration Guide

This guide covers tools for migrating Okta resources between organizations. These workflows and scripts are particularly useful for:

- Setting up demo environments from production data
- Migrating configurations between development, staging, and production
- Copying group structures and memberships between tenants
- Replicating entitlement bundle grants across organizations

---

## Available Workflows

### 1. Copy Groups Between Orgs

**Workflow:** `copy-groups-between-orgs.yml`

Exports groups from a source org as Terraform configuration and applies them to a target org.

```bash
gh workflow run copy-groups-between-orgs.yml \
  -f source_environment=ProductionEnv \
  -f target_environment=DemoEnv \
  -f exclude_system=true \
  -f dry_run=true \
  -f commit_changes=true
```

**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `source_environment` | GitHub Environment for source Okta org | Required |
| `target_environment` | GitHub Environment for target Okta org | Required |
| `name_pattern` | Regex to filter groups by name | (all groups) |
| `exclude_system` | Exclude Everyone, Administrators groups | `true` |
| `dry_run` | Plan only, don't apply | `true` |
| `commit_changes` | Commit generated Terraform file | `true` |

**What it does:**
1. Connects to source org and fetches all OKTA_GROUP type groups
2. Generates Terraform configuration (`groups_imported.tf`)
3. Runs `terraform plan` in target environment
4. Optionally applies changes and commits the file

---

### 2. Copy Group Memberships Between Orgs

**Workflow:** `copy-group-memberships.yml`

Exports group memberships from source org and recreates them in target org by matching users by email address.

```bash
gh workflow run copy-group-memberships.yml \
  -f source_environment=ProductionEnv \
  -f target_environment=DemoEnv \
  -f dry_run=true
```

**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `source_environment` | GitHub Environment for source Okta org | Required |
| `target_environment` | GitHub Environment for target Okta org | Required |
| `dry_run` | Preview only, don't apply changes | `true` |

**How it works:**
1. Exports all group memberships from source (stores user emails)
2. For each group in target org with matching name:
   - Finds users by email address
   - Adds matching users to the group
3. Reports on missing groups and users

**Important:** Users must exist in both orgs with the same email address for matching to work.

---

### 3. Copy Entitlement Bundle Grants Between Orgs

**Workflow:** `copy-grants-between-orgs.yml`

Exports OIG entitlement bundle grants from source org and recreates them in target org.

```bash
gh workflow run copy-grants-between-orgs.yml \
  -f source_environment=ProductionEnv \
  -f target_environment=DemoEnv \
  -f exclude_apps="App1,App2" \
  -f dry_run=true
```

**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `source_environment` | GitHub Environment for source Okta org | Required |
| `target_environment` | GitHub Environment for target Okta org | Required |
| `exclude_apps` | Comma-separated app names to exclude | (none) |
| `dry_run` | Preview only, don't apply changes | `true` |

**What it copies:**
- Which groups/users have which entitlement bundles
- Maps bundles and principals by name between orgs

**Prerequisites:**
- Entitlement bundles must exist in target org with matching names
- Groups/users must exist in target org with matching names

---

## Python Scripts

These scripts can be run directly for more control or debugging.

### Export Groups to Terraform

```bash
# Set environment variables for source org
export OKTA_ORG_NAME=source-org
export OKTA_BASE_URL=oktapreview.com
export OKTA_API_TOKEN=xxxxx

# Export groups
python3 scripts/export_groups_to_terraform.py \
  --output environments/target/terraform/groups_imported.tf \
  --exclude-system \
  --name-pattern "Sales -"  # Optional: filter by pattern
```

### Copy Group Memberships

```bash
# Export from source org
export OKTA_ORG_NAME=source-org
export OKTA_API_TOKEN=xxxxx

python3 scripts/copy_group_memberships.py export \
  --output memberships.json \
  --exclude-system

# Import to target org
export OKTA_ORG_NAME=target-org
export OKTA_API_TOKEN=yyyyy

python3 scripts/copy_group_memberships.py import \
  --input memberships.json \
  --dry-run
```

### Copy Entitlement Bundle Grants

```bash
# Export from source org
export OKTA_ORG_NAME=source-org
export OKTA_API_TOKEN=xxxxx

python3 scripts/copy_grants_between_orgs.py export \
  --output grants_export.json \
  --verbose

# Import to target org
export OKTA_ORG_NAME=target-org
export OKTA_API_TOKEN=yyyyy

python3 scripts/copy_grants_between_orgs.py import \
  --input grants_export.json \
  --exclude-apps "App Name" \
  --dry-run
```

---

## Recommended Migration Order

When migrating a complete environment, follow this order:

1. **Groups First**
   - Run `copy-groups-between-orgs.yml` with `dry_run=false`
   - Groups must exist before memberships or grants

2. **Users** (if needed)
   - Create users in target org (via Terraform or Okta admin)
   - Ensure email addresses match source org

3. **Group Memberships**
   - Run `copy-group-memberships.yml` with `dry_run=false`
   - Verify memberships were created

4. **Entitlement Bundles** (if needed)
   - Create bundles in target org via Terraform
   - Bundle names must match source org

5. **Grants Last**
   - Run `copy-grants-between-orgs.yml` with `dry_run=false`
   - Verifies bundles and principals exist before creating grants

---

## Troubleshooting

### Groups not found in target
- Ensure you ran the groups copy workflow first
- Check group names match exactly (case-sensitive)

### Users not matched
- Users are matched by email address (case-insensitive)
- Verify users exist in target org with same email

### Bundles not found
- Entitlement bundles must be created via Terraform first
- Bundle names must match exactly between orgs

### Rate limiting
- Scripts include automatic rate limit handling
- Large migrations may take time due to API limits

### Permission errors
- Ensure API token has governance scopes for OIG resources
- Super Admin role required for grant management

---

## Best Practices

1. **Always start with dry-run** - Preview changes before applying
2. **Use exclusions wisely** - Exclude system groups and sensitive apps
3. **Validate after migration** - Check Okta Admin Console to verify
4. **Keep exports for reference** - JSON exports serve as audit trail
5. **Test in non-production first** - Validate workflow in dev/staging

---

**Last Updated:** 2025-12-22
