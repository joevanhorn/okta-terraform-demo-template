# Scripts Directory

This directory contains Python and shell scripts for Okta API operations that complement Terraform. These scripts handle resources not yet supported by the Okta Terraform provider or provide utilities for import, migration, and management tasks.

## Quick Reference

| Task | Script | Workflow |
|------|--------|----------|
| Import OIG resources | `import_oig_resources.py` | `import-all-resources.yml` |
| Sync resource owners | `sync_owner_mappings.py` | `oig-owners.yml` |
| Apply resource owners | `apply_resource_owners.py` | `oig-owners.yml` |
| Sync labels | `sync_label_mappings.py` | `labels-sync.yml` |
| Apply labels | `apply_labels_from_config.py` | `labels-apply-from-config.yml` |
| Import risk rules | `import_risk_rules.py` | `oig-risk-rules-import.yml` |
| Apply risk rules | `apply_risk_rules.py` | `oig-risk-rules-apply.yml` |
| Build demo environment | `build_demo.py` | `build-demo.yml` |
| Manage entitlements | `manage_entitlement_settings.py` | `oig-manage-entitlements.yml` |
| Cross-org migration | `copy_grants_between_orgs.py` | `migrate-cross-org.yml` |

## Script Categories

### Core API Module

**`okta_api_manager.py`** - Shared API client module used by all Python scripts
- Handles authentication, rate limiting, error handling
- Graceful degradation for missing OIG features
- Used as import: `from okta_api_manager import OktaAPIManager`

### OIG Import Scripts

Import OIG resources from Okta to code for GitOps management.

| Script | Purpose |
|--------|---------|
| `import_oig_resources.py` | Import entitlement bundles, access reviews, catalog entries |
| `import_risk_rules.py` | Import risk rules / SOD policies to JSON |
| `import_app_entitlements.py` | Import entitlement definitions from apps |

**Usage:**
```bash
# Import all OIG resources
python scripts/import_oig_resources.py --output-dir environments/myorg

# Import risk rules
python scripts/import_risk_rules.py --output environments/myorg/config/risk_rules.json
```

### Resource Owners (API-Only)

Resource owners are not in the Terraform provider - managed via these scripts.

| Script | Purpose |
|--------|---------|
| `sync_owner_mappings.py` | Export current owners from Okta to JSON |
| `apply_resource_owners.py` | Apply owner assignments from JSON config |

**Usage:**
```bash
# Sync from Okta
python scripts/sync_owner_mappings.py --output environments/myorg/config/owner_mappings.json

# Apply to Okta
python scripts/apply_resource_owners.py --config environments/myorg/config/owner_mappings.json --dry-run
```

### Governance Labels (API-Only)

Labels for governance categorization - not in Terraform provider.

| Script | Purpose |
|--------|---------|
| `sync_label_mappings.py` | Export labels from Okta to JSON |
| `apply_labels_from_config.py` | Apply labels from JSON config |
| `apply_admin_labels.py` | Auto-detect and label admin entitlements |
| `create_compliance_labels.py` | Create standard compliance labels |
| `validate_label_config.py` | Validate label JSON syntax (used by PRs) |

**Usage:**
```bash
# Sync labels from Okta
python scripts/sync_label_mappings.py --output environments/myorg/config/label_mappings.json

# Apply labels
python scripts/apply_labels_from_config.py --config environments/myorg/config/label_mappings.json --dry-run

# Auto-label admin entitlements
python scripts/apply_admin_labels.py --dry-run
```

### Risk Rules / SOD Policies (API-Only)

Separation of Duties policies - not in Terraform provider.

| Script | Purpose |
|--------|---------|
| `import_risk_rules.py` | Export risk rules to JSON |
| `apply_risk_rules.py` | Apply risk rules from JSON config |

**Usage:**
```bash
# Import from Okta
python scripts/import_risk_rules.py --output environments/myorg/config/risk_rules.json

# Apply to Okta
python scripts/apply_risk_rules.py --config environments/myorg/config/risk_rules.json --dry-run
```

### Entitlement Management

Manage entitlement settings on applications (Beta API).

| Script | Purpose |
|--------|---------|
| `manage_entitlement_settings.py` | Enable/disable entitlement management on apps |
| `detect_entitlement_apps.py` | Find apps with entitlements to manage |
| `analyze_entitlements.py` | Analyze entitlement structure |
| `find_entitlement_value.py` | Find specific entitlement values |
| `list_all_entitlement_values.py` | List all values across apps |

**Usage:**
```bash
# List apps and their entitlement status
python scripts/manage_entitlement_settings.py --action list

# Enable on specific app
python scripts/manage_entitlement_settings.py --action enable --app-id 0oaXXX --dry-run
```

### Cross-Org Migration

Copy resources between Okta organizations.

| Script | Purpose |
|--------|---------|
| `export_groups_to_terraform.py` | Export groups as Terraform code |
| `copy_group_memberships.py` | Export/import group memberships |
| `copy_grants_between_orgs.py` | Export/import entitlement bundle grants |

**Usage:**
```bash
# Export groups to Terraform
python scripts/export_groups_to_terraform.py --output environments/target/terraform/groups.tf

# Copy memberships
python scripts/copy_group_memberships.py export --output memberships.json
python scripts/copy_group_memberships.py import --input memberships.json --dry-run

# Copy grants
python scripts/copy_grants_between_orgs.py export --output grants.json
python scripts/copy_grants_between_orgs.py import --input grants.json --dry-run
```

### Demo Builder

Generate complete demo environments from YAML configuration.

| Script | Purpose |
|--------|---------|
| `build_demo.py` | Generate Terraform from demo-config.yaml |

**Usage:**
```bash
# Generate demo environment
python scripts/build_demo.py --config demo-builder/my-demo.yaml

# Validate only
python scripts/build_demo.py --config demo-builder/my-demo.yaml --schema-check

# Dry run (preview)
python scripts/build_demo.py --config demo-builder/my-demo.yaml --dry-run
```

### Investigation & Debugging

Scripts for troubleshooting API issues.

| Script | Purpose |
|--------|---------|
| `investigate_labels_api.py` | Debug labels API behavior |
| `investigate_405_errors.py` | Debug 405 errors |
| `validate_labels_api.py` | Validate labels API endpoints |
| `check_label_eligibility.py` | Check if resources can have labels |
| `get_app_orns.py` | Get Okta Resource Names for apps |

### Utility Scripts

| Script | Purpose |
|--------|---------|
| `find_admin_resources.py` | Find admin-level entitlements |
| `protect_admin_users.py` | Protect admin users from modification |
| `list_apps.py` | List all applications |
| `list_all_labels.py` | List all governance labels |
| `check_specific_app.py` | Check specific app details |
| `cleanup_terraform.py` | Clean up terraform state issues |

### Shell Scripts

| Script | Purpose |
|--------|---------|
| `import_okta_resources.sh` | Terraformer import wrapper |
| `build_test_org.sh` | Set up test organization |
| `cleanup_test_org.sh` | Clean up test organization |
| `setup-repository.sh` | Initial repository setup |
| `reimport_bundles_with_campaign_errors.sh` | Fix campaign association errors |
| `test_complete_workflow.sh` | End-to-end workflow test |

### OPA/OAG Integration

| Script | Purpose |
|--------|---------|
| `import_opa_resources.py` | Import OPA resources |
| `manage_oag_apps.py` | Manage OAG applications |
| `configure_scim_app.py` | Configure SCIM provisioning |

### Subdirectories

- **`archive/`** - Deprecated scripts kept for reference
- **`oag/`** - OAG-specific utilities

## Environment Variables

All scripts use these environment variables:

```bash
export OKTA_ORG_URL="https://myorg.okta.com"
export OKTA_API_TOKEN="your-api-token"

# Optional for some scripts
export OKTA_ORG_NAME="myorg"
export OKTA_BASE_URL="okta.com"
```

## Dependencies

```bash
pip install -r requirements.txt

# Core dependencies:
# - requests
# - python-dotenv
# - pyyaml
# - tabulate
# - colorama
```

## CLI vs. Workflow Usage

Most scripts can be run directly or via GitHub Actions workflows:

**Direct CLI:**
```bash
python scripts/sync_owner_mappings.py --output config/owners.json
```

**Via Workflow:**
```bash
gh workflow run oig-owners.yml -f environment=myorg -f dry_run=true
```

Workflows provide:
- Proper authentication via GitHub Environments
- AWS OIDC for state access
- Approval gates for production
- Audit trail in GitHub Actions

## See Also

- [`docs/API_MANAGEMENT.md`](../docs/API_MANAGEMENT.md) - Comprehensive API guide (1190+ lines)
- [`docs/LABEL_WORKFLOW_GUIDE.md`](../docs/LABEL_WORKFLOW_GUIDE.md) - Labels GitOps workflow
- [`archive/README.md`](archive/README.md) - Archived script documentation
