# Cross-Org Migration Guide

This guide covers tools for migrating Okta resources between organizations. These workflows and scripts are particularly useful for:

- Setting up demo environments from production data
- Migrating configurations between development, staging, and production
- Copying group structures and memberships between tenants
- Replicating entitlement bundle grants across organizations

---

## Consolidated Workflow

All cross-org migration operations are handled by a single unified workflow: `migrate-cross-org.yml`

### Basic Usage

```bash
# Copy groups between orgs
gh workflow run migrate-cross-org.yml \
  -f resource_type=groups \
  -f source_environment=ProductionEnv \
  -f target_environment=DemoEnv \
  -f dry_run=true

# Copy group memberships between orgs
gh workflow run migrate-cross-org.yml \
  -f resource_type=memberships \
  -f source_environment=ProductionEnv \
  -f target_environment=DemoEnv \
  -f dry_run=true

# Copy entitlement bundle grants between orgs
gh workflow run migrate-cross-org.yml \
  -f resource_type=grants \
  -f source_environment=ProductionEnv \
  -f target_environment=DemoEnv \
  -f dry_run=true
```

### Parameters

| Parameter | Description | Default | Applies To |
|-----------|-------------|---------|------------|
| `resource_type` | Type of resource to migrate | Required | All |
| `source_environment` | GitHub Environment for source Okta org | Required | All |
| `target_environment` | GitHub Environment for target Okta org | Required | All |
| `name_pattern` | Regex to filter groups by name | (all groups) | groups |
| `exclude_system` | Exclude Everyone, Administrators groups | `true` | groups |
| `exclude_apps` | Comma-separated app names to exclude | (none) | grants |
| `dry_run` | Preview only, don't apply | `true` | All |
| `commit_changes` | Commit generated Terraform file | `true` | groups |

### Resource Types

#### `groups`
Exports groups from source org as Terraform configuration and applies to target org.
- Generates `groups_imported.tf` in target environment
- Runs terraform plan/apply
- Optionally commits the file

#### `memberships`
Exports group memberships and recreates in target org by matching users by email.
- Users must exist in both orgs with same email address
- Reports missing groups and unmatched users

#### `grants`
Exports OIG entitlement bundle grants and recreates in target org.
- Bundles must exist in target org with matching names
- Groups/users must exist with matching names

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
   - Run `migrate-cross-org.yml` with `resource_type=groups` and `dry_run=false`
   - Groups must exist before memberships or grants

2. **Users** (if needed)
   - Create users in target org (via Terraform or Okta admin)
   - Ensure email addresses match source org

3. **Group Memberships**
   - Run `migrate-cross-org.yml` with `resource_type=memberships` and `dry_run=false`
   - Verify memberships were created

4. **Entitlement Bundles** (if needed)
   - Create bundles in target org via Terraform
   - Bundle names must match source org

5. **Grants Last**
   - Run `migrate-cross-org.yml` with `resource_type=grants` and `dry_run=false`
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
