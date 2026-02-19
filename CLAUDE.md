# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **GitOps template for Okta Identity Governance** designed for solutions engineers and sales teams. It enables managing multiple Okta tenants using Infrastructure as Code, creating demo environments, and demonstrating OIG features. The repository is meant to be **forked and customized** for managing your Okta organizations.

---

## Critical Architecture Principles

### Environment-Based Multi-Tenant Structure

**Core Rule:** One Directory = One Okta Organization

```
environments/
├── production/         # Production Okta tenant (template)
├── staging/            # Staging Okta tenant (template)
└── development/        # Development Okta tenant (template)
```

Each environment is completely self-contained with independent Terraform state, separate GitHub Environment secrets, and no cross-environment dependencies.

**To add a new environment:**
1. Create directory: `mkdir -p environments/mycompany/{terraform,imports,config}`
2. Set up GitHub Environment with secrets: `OKTA_API_TOKEN`, `OKTA_ORG_NAME`, `OKTA_BASE_URL`
3. Run import workflow: `gh workflow run import-all-resources.yml -f tenant_environment=MyCompany`

### Three-Layer Resource Management Model

Understanding what goes where is critical:

**Layer 1: Terraform Provider (Full CRUD)**
- Standard Okta resources: users, groups, apps, policies
- OIG resources: entitlement bundles, access reviews, approval sequences, catalog entries
- Managed in `environments/{env}/terraform/*.tf` files

**Layer 2: Python API Scripts (Read/Write)**
- Resource Owners, Governance Labels, Risk Rules / SOD Policies (not in Terraform provider yet)
- Entitlement Settings - enable/disable on apps (Beta API - December 2025)
- Managed in `environments/{env}/config/*.json` files
- Applied via `scripts/*.py` or GitHub Actions

**Layer 3: Manual Management (Okta Admin UI)**
- **Entitlement assignments** (which users/groups have which bundles)
- Access review decisions and approvals
- Certain advanced OIG configurations

**Why this matters:** Terraform manages bundle DEFINITIONS, but NOT who has those bundles. Principal assignments must be managed in the Okta Admin UI.

---

## Common Commands

### Terraform (per environment)

```bash
cd environments/mycompany/terraform
terraform init          # Initialize (connects to S3 backend)
terraform fmt           # Format code
terraform validate      # Validate configuration
terraform plan          # Plan changes (acquires DynamoDB lock)
terraform apply         # Apply changes (with state locking)
```

### Key GitHub Workflows

```bash
# Import all resources from Okta to code
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyCompany \
  -f update_terraform=true \
  -f commit_changes=true

# Manually trigger Terraform apply with approval
gh workflow run tf-apply.yml -f environment=mycompany

# Apply labels (all or admin only)
gh workflow run labels-apply.yml \
  -f label_type=admin \
  -f environment=mycompany \
  -f dry_run=false

# Sync and apply resource owners
gh workflow run oig-owners.yml \
  -f environment=mycompany \
  -f dry_run=false

# Deploy AD Domain Controller
gh workflow run ad-deploy.yml \
  -f environment=myorg \
  -f regions='["us-east-1"]' \
  -f action=plan  # or apply, destroy

# Manage entitlements (auto mode: detect and enable on apps)
gh workflow run oig-manage-entitlements.yml \
  -f mode=auto \
  -f environment=mycompany \
  -f dry_run=true
```

See `docs/reference/workflow-reference.md` for the complete list of all workflows.

### Key Python Scripts

```bash
pip install -r requirements.txt

# Import OIG resources from Okta
python3 scripts/import_oig_resources.py --output-dir environments/mycompany

# Apply resource owners to Okta
python3 scripts/apply_resource_owners.py \
  --config environments/mycompany/config/owner_mappings.json --dry-run

# Apply labels
python3 scripts/apply_admin_labels.py --dry-run

# Sync governance labels from Okta
python3 scripts/sync_label_mappings.py \
  --output environments/mycompany/config/label_mappings.json

# Apply risk rules to Okta
python3 scripts/apply_risk_rules.py \
  --config environments/mycompany/config/risk_rules.json --dry-run

# Manage entitlement settings on apps (Beta API)
python3 scripts/manage_entitlement_settings.py --action list
```

See `docs/reference/api-management.md` for the complete Python scripts reference.

---

## Repository Structure

```
.
├── environments/               # Multi-tenant configurations (one dir per org)
├── scripts/                    # Python automation (import, sync, apply)
├── modules/                    # Reusable Terraform modules
├── demo-builder/               # Demo environment generator (see demo-builder/README.md)
├── ai-assisted/                # AI code generation tools (see ai-assisted/README.md)
├── backup-restore/             # Backup and disaster recovery
├── docs/                       # Comprehensive documentation
├── testing/                    # Validation guides
└── .github/workflows/          # GitHub Actions
```

**Terraform Provider:** Okta provider v6.4.0+ required for OIG resources. See `environments/myorg/terraform/provider.tf`.

---

## Critical Patterns and Gotchas

### 1. Template String Escaping

**Okta uses `${source.login}` as template variables, which conflicts with Terraform interpolation.**

```hcl
# WRONG - Terraform will try to interpolate
user_name_template = "${source.login}"

# CORRECT - Double $$ escapes for Terraform
user_name_template = "$${source.login}"
```

### 2. Entitlement Bundle Principal Assignments

```hcl
# This creates the BUNDLE DEFINITION only
resource "okta_entitlement_bundle" "example" {
  name   = "Admin Access"
  status = "ACTIVE"
}
```

**This does NOT assign the bundle to any users or groups!** Principal assignments must be managed in **Okta Admin UI** or via direct API calls. They are NOT managed by Terraform.

### 3. Terraformer Limitations

Terraformer can import standard Okta resources (users, groups, apps, policies) but **CANNOT import** OIG resources (entitlement bundles, access reviews, approval sequences). Use `import_oig_resources.py` for OIG resources.

### 4. System Apps Exclusion

**Do NOT import these Okta system apps (they can't be managed in Terraform):**
- `okta-iga-reviewer`, `okta-flow-sso`, `okta-access-requests-resource-catalog`, `flow`, `okta-atspoke-sso`

### 5. OAuth App Visibility Rules

**Okta enforces validation rules on app visibility:**

```hcl
# INVALID - can't have hide_ios=false with login_mode=DISABLED
resource "okta_app_oauth" "invalid" {
  hide_ios   = false
  login_mode = "DISABLED"
}

# VALID - for API/service apps: hide both, login DISABLED
# VALID - for user-facing apps: show both, login SPEC with login_uri set
```

### 6. Resource Owners and Labels Are API-Only

These resources don't exist in the Terraform provider. Manage via Python scripts:

```bash
python3 scripts/apply_resource_owners.py --config config/owner_mappings.json
python3 scripts/apply_admin_labels.py
```

### 7. Environment Secrets Must Match Directory Names

- Directory: `environments/mycompany/`
- GitHub Environment: `MyCompany` (case-insensitive match)

Workflow must specify `environment: name: MyCompany` to use correct secrets.

### 8. Label Validation Uses Two-Phase GitOps Approach

Labels use a two-phase workflow that respects environment protection:

- **Phase 1 (PR Validation):** `labels-validate.yml` -- no environment, no Okta API calls, validates syntax and ORN formats only.
- **Phase 2 (Deployment):** `labels-apply-from-config.yml` -- uses environment secrets, auto dry-run on merge, manual apply via workflow dispatch.

**Why:** GitHub Environment protection blocks PR triggers. Syntax validation doesn't need secrets; API validation does. Separation prevents secret exposure via PRs.

**Never:** add `pull_request` trigger to deployment workflow, add `environment` to validation workflow, or skip the dry-run step.

### 9. OAuth Authentication Limitation

**OAuth-authenticated service apps cannot create other OAuth applications**, even with proper scopes and admin roles.

```hcl
# OAuth service app trying to create OAuth app - WILL FAIL
# API token works without limitations - USE THIS
provider "okta" {
  api_token = var.okta_api_token
}
```

See `docs/reference/oauth-authentication.md` for details.

### 10. Dynamic Value Lookups for Entitlement Bundles

**Entitlement bundles require Okta-generated value IDs, not external_value strings.** Use `dynamic` blocks with `for` expressions:

```hcl
locals {
  standard_accounts = ["DEMO38", "26DEMO26", "26DEMO14", "DEMO42"]
}

resource "okta_entitlement_bundle" "standard_access" {
  name   = "Standard Access"
  status = "ACTIVE"
  target {
    external_id = okta_app_oauth.my_app.id
    type        = "APPLICATION"
  }
  entitlements {
    id = okta_entitlement.app_accounts.id
    dynamic "values" {
      for_each = [
        for v in okta_entitlement.app_accounts.values : v.id
        if contains(local.standard_accounts, v.external_value)
      ]
      content { id = values.value }
    }
  }
}
```

**Key:** `values` is a **block type** -- use `dynamic "values"` not `values = [...]`. The `for` expression filters by `external_value` and returns the Okta-generated `id`.

### 11. Entitlement Values Must Be Alphabetically Ordered

**Okta API returns entitlement values sorted alphabetically by `external_value`.** The Terraform provider compares by index position, so mismatched order causes "Provider produced inconsistent result after apply" errors.

```hcl
resource "okta_entitlement" "example" {
  # Values MUST be in alphabetical order by external_value
  values {
    external_value = "no"    # "n" comes before "y"
    name           = "No"
  }
  values {
    external_value = "yes"   # "y" comes after "n"
    name           = "Yes"
  }
}
```

This is undocumented Okta API behavior. If you see "inconsistent result after apply" errors on entitlements, check value ordering first.

### 12. CSV-Based User Management for Bulk Imports

**For managing 1000+ users, use CSV-based import with for_each:**

```hcl
locals {
  csv_users = csvdecode(file("${path.module}/users.csv"))
  users_map = { for user in local.csv_users : user.email => user }
}

resource "okta_user" "csv_users" {
  for_each   = local.users_map
  email      = each.value.email
  first_name = each.value.first_name
  last_name  = each.value.last_name
  login      = each.value.login
  lifecycle { ignore_changes = [manager_id] }
}
```

**CSV columns:** `email,first_name,last_name,login,status,department,title,manager_email,groups,custom_profile_attributes`

Manager relationships use `okta_link_value` resources. Use `terraform apply -parallelism=10` for faster execution. See `environments/myorg/terraform/users_from_csv.tf.example` for complete implementation.

---

## AWS Backend Integration

All Terraform state is stored in S3 with DynamoDB locking and OIDC authentication for GitHub Actions (no long-lived AWS credentials). State path: `s3://okta-terraform-demo/Okta-GitOps/{environment}/terraform.tfstate`.

Setup: Deploy `aws-backend/` infrastructure, add `AWS_ROLE_ARN` to GitHub secrets, then `terraform init -migrate-state`.

See `docs/getting-started/aws-backend.md` for the complete setup and migration guide.

## OPA Integration

This repository supports optional Okta Privileged Access (OPA) integration via the `oktapam` provider for server access projects, secret management, security policies, and AD integration.

See `docs/infrastructure/opa-privileged-access.md` for configuration instructions. Example: `environments/myorg/terraform/opa_resources.tf.example`.

## Demo Builder

Generate complete demo environments from YAML config files with pre-built industry examples (financial services, healthcare, technology).

See `demo-builder/README.md` for documentation and `demo-builder/DEMO_WORKSHEET.md` for the questionnaire. AI-assisted generation is available via `ai-assisted/README.md`.

## Backup and Restore

Two approaches available: resource-based (full DR/audit) and state-based (quick S3 rollback).

See `docs/guides/backup-restore.md` for complete backup and restore procedures.

## Development Workflow

1. Create feature branch
2. Edit Terraform/config files, validate locally (`terraform fmt && terraform validate && terraform plan`)
3. Commit and push, create PR (`gh pr create`)
4. Review automated plan in PR comments, get approval, merge
5. Trigger apply: `gh workflow run tf-apply.yml -f environment=mycompany`

## Syncing from Okta (Drift Detection)

Run the import workflow with `update_terraform=false` and `commit_changes=false` to detect drift, then decide whether to update Terraform or revert manual Okta changes.

## Customizing for Your Organization

After forking: create your environment directory, set up GitHub Environment secrets, run the import workflow, then update this CLAUDE.md with org-specific patterns. See `docs/getting-started/README.md`.

## Troubleshooting

**Most common issues:**

1. **Template interpolation errors** -- Use `$$` instead of `$` in Okta template strings.
2. **Import fails for OIG resources** -- Use `import_oig_resources.py`, not Terraformer.
3. **Entitlement assignments not working** -- Assignments must be managed in Okta Admin UI, not Terraform.
4. **Labels API returns 405 errors** -- Use `labelId` not `name` in URLs. See `scripts/archive/README.md`.
5. **"Error reading campaign" during terraform plan** -- Provider bug with stale campaign associations. Run: `gh workflow run fix-bundle-campaign-errors.yml -f environment=mycompany -f dry_run=false -f bundles_to_fix=all`

See `docs/troubleshooting/` for detailed troubleshooting guides including `docs/troubleshooting/lessons-learned.md` and `docs/troubleshooting/entitlement-bundles.md`.

---

## Key Takeaways for Claude Code

When working in this repository:

1. **Always respect environment isolation** - never mix tenants
2. **Remember the three-layer model** - know what goes where (Terraform vs API vs Manual)
3. **Use `$$` for Okta template strings** - avoid interpolation errors
4. **Entitlement assignments are manual** - Terraform manages definitions only
5. **GitHub Environments match directory names** - ensures correct Okta secrets
6. **AWS OIDC for state backend** - no long-lived AWS credentials needed
7. **State is in S3** - not local files, use DynamoDB locking
8. **Use AI-assisted generation for demos** - faster and more consistent
9. **Import from Okta regularly** - detect drift from manual changes
10. **Resource owners and labels need Python scripts** - not in Terraform provider
11. **Label workflows use two-phase validation** - PR syntax check (no secrets) + deployment (with secrets)
12. **Always create PRs for label changes** - automatic validation catches errors early
13. **Review dry-run before apply** - automatic on merge, manual apply required
14. **OPA is optional** - enable oktapam provider only when OPA features are needed
15. **OPA lessons learned** - see `docs/troubleshooting/lessons-learned.md` for known issues
16. **Entitlement values must be alphabetically ordered** - undocumented API behavior causes apply errors
