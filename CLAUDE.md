# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **GitOps template for Okta Identity Governance** designed for solutions engineers and sales teams to:
- Learn GitOps principles with Okta tenant management
- Create and maintain demo environments for prospective customers
- Manage multiple Okta tenants using Infrastructure as Code
- Demonstrate OIG (Okta Identity Governance) features

The repository is meant to be **forked and customized** for managing your Okta organizations.

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

**Each environment is completely self-contained:**
- Independent Terraform state
- Separate GitHub Environment secrets
- No cross-environment dependencies
- Easy to add/remove tenants

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
- Resource Owners (not in Terraform provider yet)
- Governance Labels (not in Terraform provider yet)
- Risk Rules / SOD Policies (not in Terraform provider yet)
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

### Initial Setup

#### AWS Backend Infrastructure (One-Time Setup)

```bash
# Deploy S3 bucket, DynamoDB table, and IAM roles for GitHub Actions
cd aws-backend
terraform init
terraform apply

# Save outputs - you'll need the AWS_ROLE_ARN for GitHub secrets
terraform output github_actions_role_arn
```

#### GitHub Secrets Configuration

Add this secret to your GitHub repository:
- **Secret Name:** `AWS_ROLE_ARN`
- **Secret Value:** From `terraform output github_actions_role_arn`

Example: `arn:aws:iam::123456789012:role/GitHubActions-OktaTerraform`

#### New Environment Setup

```bash
# Create environment directory structure
mkdir -p environments/mycompany/{terraform,imports,config}

# Backend is pre-configured in provider.tf
# State will be stored at: s3://okta-terraform-demo/Okta-GitOps/mycompany/terraform.tfstate
```

### Working with Terraform (per environment)

```bash
# Navigate to specific environment
cd environments/mycompany/terraform

# Initialize Terraform (connects to S3 backend)
terraform init

# Migrate existing local state to S3 (if upgrading)
terraform init -migrate-state

# Format code
terraform fmt

# Validate configuration
terraform validate

# Plan changes (acquires DynamoDB lock)
terraform plan

# Apply changes (with state locking)
terraform apply

# Destroy resources
terraform destroy

# Force unlock if previous run was interrupted
terraform force-unlock <LOCK_ID>
```

### GitHub Workflows

```bash
# Import all resources from Okta to code
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyCompany \
  -f update_terraform=true \
  -f commit_changes=true

# Manually trigger Terraform apply with approval
gh workflow run tf-apply.yml \
  -f environment=mycompany

# Sync and apply resource owners
gh workflow run oig-owners.yml \
  -f environment=mycompany \
  -f dry_run=false

# Import risk rules from Okta
gh workflow run oig-risk-rules-import.yml \
  -f environment=mycompany \
  -f commit_changes=true

# Apply risk rules to Okta
gh workflow run oig-risk-rules-apply.yml \
  -f environment=mycompany \
  -f dry_run=false

# Apply labels (all or admin only)
gh workflow run labels-apply.yml \
  -f label_type=admin \
  -f environment=mycompany \
  -f dry_run=false

# Manage entitlements (manual mode: list, enable, disable)
gh workflow run oig-manage-entitlements.yml \
  -f mode=manual \
  -f environment=mycompany \
  -f action=list

# Manage entitlements (auto mode: detect and enable on apps)
gh workflow run oig-manage-entitlements.yml \
  -f mode=auto \
  -f environment=mycompany \
  -f dry_run=true

# Cross-org migration: Copy groups, memberships, or grants between orgs
gh workflow run migrate-cross-org.yml \
  -f resource_type=groups \
  -f source_environment=SourceEnv \
  -f target_environment=TargetEnv \
  -f dry_run=true

# Also supports: resource_type=memberships or resource_type=grants
```

### Python Scripts (API Management)

```bash
# Install dependencies
pip install -r requirements.txt

# Import OIG resources from Okta
python3 scripts/import_oig_resources.py \
  --output-dir environments/mycompany

# Sync resource owners from Okta
python3 scripts/sync_owner_mappings.py \
  --output environments/mycompany/config/owner_mappings.json

# Apply resource owners to Okta
python3 scripts/apply_resource_owners.py \
  --config environments/mycompany/config/owner_mappings.json \
  --dry-run  # Remove for actual apply

# Sync governance labels from Okta
python3 scripts/sync_label_mappings.py \
  --output environments/mycompany/config/label_mappings.json

# Validate label configuration (used by PR validation workflow)
python3 scripts/validate_label_config.py \
  environments/mycompany/config/label_mappings.json

# Import risk rules (SOD policies) from Okta
python3 scripts/import_risk_rules.py \
  --output environments/mycompany/config/risk_rules.json

# Apply risk rules to Okta
python3 scripts/apply_risk_rules.py \
  --config environments/mycompany/config/risk_rules.json \
  --dry-run  # Remove for actual apply

# Find admin entitlements
python3 scripts/find_admin_resources.py

# Label admin entitlements
python3 scripts/apply_admin_labels.py --dry-run

# Manage entitlement settings on apps (Beta API - December 2025)
# List all apps and their entitlement management status
python3 scripts/manage_entitlement_settings.py --action list

# Enable entitlement management on an app
python3 scripts/manage_entitlement_settings.py \
  --action enable \
  --app-id 0oaXXXXXXXX \
  --dry-run  # Remove for actual apply

# Cross-org migration: Export groups to Terraform
python3 scripts/export_groups_to_terraform.py \
  --output environments/target/terraform/groups_imported.tf \
  --exclude-system

# Cross-org migration: Export group memberships
python3 scripts/copy_group_memberships.py export \
  --output memberships.json

# Cross-org migration: Import group memberships
python3 scripts/copy_group_memberships.py import \
  --input memberships.json \
  --dry-run

# Cross-org migration: Export entitlement bundle grants
python3 scripts/copy_grants_between_orgs.py export \
  --output grants_export.json

# Cross-org migration: Import entitlement bundle grants
python3 scripts/copy_grants_between_orgs.py import \
  --input grants_export.json \
  --exclude-apps "App Name" \
  --dry-run
```

### AI-Assisted Code Generation

**Option 1: Manual (Tier 1) - Prompt Engineering**
```bash
# 1. Copy context files to AI assistant (Gemini, ChatGPT, Claude)
cat ai-assisted/context/repository_structure.md
cat ai-assisted/context/terraform_examples.md
cat ai-assisted/context/okta_resource_guide.md

# 2. Use prompt template
cat ai-assisted/prompts/create_demo_environment.md

# 3. Paste to AI, get generated code, save to .tf files
```

**Option 2: Automated (Tier 2) - CLI Tool**
```bash
cd ai-assisted

# Install provider (choose one)
pip install google-generativeai  # Gemini
pip install openai               # OpenAI
pip install anthropic            # Claude

# Set API key
export GEMINI_API_KEY="your-key"

# Interactive mode
python generate.py --interactive --provider gemini

# Command-line mode
python generate.py \
  --prompt "Create 5 marketing users and a Salesforce app" \
  --provider gemini \
  --output ../environments/mycompany/terraform/demo.tf \
  --validate
```

### Testing and Validation

```bash
# Run manual validation plan
cp testing/MANUAL_VALIDATION_PLAN.md testing/validation_run_$(date +%Y%m%d).md
# Follow checklist in the copied file

# Quick validation
cd environments/mycompany/terraform
terraform fmt -check
terraform validate
terraform plan

# Python tests (if available)
pytest tests/ -v
```

---

## High-Level Architecture

### GitOps Workflow

```
Developer → Feature Branch → PR (terraform plan runs) →
Code Review → Merge to Main → Manual Apply Trigger →
Approval Gate → Terraform Apply → Okta Resources Created
```

**Key Components:**
- **Pull Requests:** Automatically run `terraform plan`, post results as PR comment
- **Branch Protection:** Requires 1 approval, plan must pass
- **Approval Gates:** Production applies require manual approval via GitHub Environments
- **Drift Detection:** Weekly scheduled imports detect manual changes in Okta

### Import Workflow Architecture

The import workflow is the "sync from Okta" mechanism:

```
Okta Tenant (source of truth) →
  API calls (via Python) →
    Generate Terraform .tf files →
      Generate JSON exports (for audit) →
        Commit to repository →
          Apply via Terraform (reconcile state)
```

**What gets imported:**
- Entitlement bundles → `terraform/oig_entitlements.tf`
- Access reviews → `terraform/oig_reviews.tf`
- Resource owners → `config/owner_mappings.json`
- Governance labels → `config/label_mappings.json`

### State Management

**Each environment maintains independent state in S3:**
- **S3 Backend:** `s3://okta-terraform-demo/Okta-GitOps/{environment}/terraform.tfstate`
- **State Locking:** DynamoDB table `okta-terraform-state-lock`
- **Encryption:** AES256 server-side encryption
- **Versioning:** Enabled for state history and rollback
- **GitHub Actions:** Authenticates via AWS OIDC (no long-lived credentials)

**State Storage Structure:**
```
s3://okta-terraform-demo/
└── Okta-GitOps/
    ├── production/terraform.tfstate
    ├── staging/terraform.tfstate
    └── development/terraform.tfstate
```

**Never share state across environments!**

### GitHub Actions Workflows

Workflows are named with category prefixes for easy searchability:

**Terraform Workflows (`tf-*`):**
- `tf-plan.yml` - Run plan on PR and push to main (with AWS OIDC)
- `tf-apply.yml` - Apply with manual approval gate (with AWS OIDC)
- `tf-validate.yml` - Validate Terraform configuration

**OIG/Governance Workflows (`oig-*`):**
- `oig-owners.yml` - Sync resource owners (requires environment parameter)
- `oig-manage-entitlements.yml` - Enable/disable entitlement management on apps
- `oig-risk-rules-apply.yml` - Apply risk rules to Okta
- `oig-risk-rules-import.yml` - Import risk rules from Okta

**Labels Workflows (`labels-*`):**
- `labels-apply.yml` - Apply labels (all or admin only)
- `labels-apply-from-config.yml` - Deploy labels from JSON config
- `labels-sync.yml` - Sync labels from Okta
- `labels-validate.yml` - Validate label configuration (syntax-only)

**Migration Workflows (`migrate-*`):**
- `migrate-cross-org.yml` - Copy groups, memberships, or grants between orgs

**Other Workflows:**
- `import-all-resources.yml` - Import entire tenant to code
- `export-oig.yml` - Export OIG configs to JSON
- `opa-plan.yml` - Plan OPA resources
- `deploy-oag-app.yml` - Deploy OAG applications
- `deploy-scim-server.yml` - Deploy SCIM server
- `sync-template.yml` - Sync from upstream template
- `validate-pr.yml` - Validate pull requests
- `generate-oauth-keys.yml` - Generate OAuth key pairs
- `governance-setup.yml` - Initial governance setup

**Authentication:**
- **Okta:** GitHub Environments with `OKTA_API_TOKEN`, `OKTA_ORG_NAME`, `OKTA_BASE_URL`
- **AWS:** OIDC authentication via `AWS_ROLE_ARN` secret (no long-lived credentials)

---

## Critical Patterns and Gotchas

### 1. Template String Escaping

**Okta uses `${source.login}` as template variables, which conflicts with Terraform interpolation.**

```hcl
# ❌ WRONG - Terraform will try to interpolate
user_name_template = "${source.login}"

# ✅ CORRECT - Double $$ escapes for Terraform
user_name_template = "$${source.login}"
```

**Always use `$$` for Okta template strings.**

### 2. Entitlement Bundle Principal Assignments

**Critical Understanding:**

```hcl
# This creates the BUNDLE DEFINITION
resource "okta_entitlement_bundle" "example" {
  name   = "Admin Access"
  status = "ACTIVE"
  # ...
}
```

**This does NOT assign the bundle to any users or groups!**

Principal assignments (who has this bundle) must be managed in **Okta Admin UI** or via direct API calls. They are NOT managed by Terraform.

### 3. Terraformer Limitations

**Terraformer can import:**
- ✅ Standard Okta resources (users, groups, apps, policies)

**Terraformer CANNOT import:**
- ❌ OIG resources (too new for Terraformer support)
- ❌ Entitlement bundles
- ❌ Access reviews
- ❌ Approval sequences

**Solution:** Use the `import_oig_resources.py` script for OIG resources.

### 4. System Apps Exclusion

**Do NOT import these Okta system apps (they can't be managed in Terraform):**
- `okta-iga-reviewer` (Access Certification Reviews)
- `okta-flow-sso` (Workflows)
- `okta-access-requests-resource-catalog` (Identity Governance)
- `flow` (Workflows OAuth)
- `okta-atspoke-sso` (Access Requests)

These are managed by Okta and will cause errors if imported.

### 5. OAuth App Visibility Rules

**Okta enforces validation rules:**

```hcl
# ❌ INVALID - can't have hide_ios=false with login_mode=DISABLED
resource "okta_app_oauth" "invalid" {
  hide_ios   = false
  login_mode = "DISABLED"
}

# ✅ VALID - for API/service apps
resource "okta_app_oauth" "api_app" {
  hide_ios   = true
  hide_web   = true
  login_mode = "DISABLED"
}

# ✅ VALID - for user-facing apps
resource "okta_app_oauth" "web_app" {
  hide_ios   = false
  hide_web   = false
  login_mode = "SPEC"
  login_uri  = "https://app.example.com/login"
}
```

### 6. Resource Owners and Labels Are API-Only

**These resources don't exist in the Terraform provider:**

```bash
# Manage via Python scripts
python3 scripts/apply_resource_owners.py --config config/owner_mappings.json
python3 scripts/apply_admin_labels.py
```

**Why:** The Okta Terraform provider doesn't support these endpoints yet. Use the Python API scripts.

### 7. Environment Secrets Must Match Directory Names

**GitHub Environment naming convention:**
- Directory: `environments/mycompany/`
- GitHub Environment: `MyCompany` (case-insensitive match)

**Workflow must specify:**
```yaml
environment:
  name: MyCompany
```

This ensures correct secrets are used for the tenant.

### 8. Label Validation Uses Two-Phase GitOps Approach

**Critical Understanding:**

Labels are managed via a two-phase workflow that respects environment protection:

**Phase 1: PR Validation (No Secrets)**
```yaml
# labels-validate.yml
# NO environment specified
# NO Okta API calls
# Validates syntax and ORN formats only
```

**Phase 2: Deployment (With Secrets)**
```yaml
# labels-apply-from-config.yml
environment: MyCompany  # Specified via input parameter
# Uses Okta API secrets
# Auto dry-run on merge to main
# Manual apply via workflow dispatch
```

**Why Two Workflows?**
- GitHub Environment protection blocks PR triggers
- Syntax validation doesn't need Okta secrets
- API validation requires environment secrets
- Separation prevents secret exposure via PRs

**Flow:**
```
PR → Syntax validation (no secrets) →
Merge → Auto dry-run (with secrets) →
Manual trigger → Apply (with secrets)
```

**Never:**
- Don't add `pull_request` trigger to deployment workflow
- Don't add `environment` to validation workflow
- Don't skip the dry-run step

### 9. OAuth Authentication Limitation

**OAuth-authenticated service apps cannot create other OAuth applications**, even with proper scopes and admin roles.

```hcl
# ❌ OAuth service app trying to create OAuth app - WILL FAIL
provider "okta" {
  org_name       = var.okta_org_name
  base_url       = var.okta_base_url
  client_id      = var.okta_client_id
  private_key    = var.okta_private_key
  # ...
}

resource "okta_app_oauth" "my_app" {
  # This will fail with "permission denied" error
}
```

```hcl
# ✅ API token works without limitations
provider "okta" {
  org_name  = var.okta_org_name
  base_url  = var.okta_base_url
  api_token = var.okta_api_token
}

resource "okta_app_oauth" "my_app" {
  # This works fine
}
```

**Recommendation:** Use API token authentication for simplicity and to avoid permission limitations.

**See:** [`docs/OAUTH_AUTHENTICATION_NOTES.md`](docs/OAUTH_AUTHENTICATION_NOTES.md) for detailed OAuth setup and troubleshooting.

### 10. Dynamic Value Lookups for Entitlement Bundles

**Entitlement bundles require Okta-generated value IDs, not external_value strings.**

When creating entitlement bundles, you need to reference the Okta-generated `id` for each entitlement value, not the `external_value` string you defined. Use `dynamic` blocks with `for` expressions to look up value IDs:

```hcl
# Define account groupings in locals for reusability
locals {
  standard_accounts = ["DEMO38", "26DEMO26", "26DEMO14", "DEMO42"]
}

# Create entitlement with values
resource "okta_entitlement" "app_accounts" {
  app_id         = okta_app_oauth.my_app.id
  key            = "accounts"
  type           = "array<string>"
  display_name   = "Account Access"

  values {
    value          = "ANCHOR CHECKING II"
    external_value = "DEMO38"
  }
  values {
    value          = "CASH MANAGEMENT III"
    external_value = "26DEMO26"
  }
  # ... more values
}

# Bundle using dynamic lookup
resource "okta_entitlement_bundle" "standard_access" {
  name        = "Standard Access"
  description = "Standard 4-account access"
  status      = "ACTIVE"

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
      content {
        id = values.value
      }
    }
  }
}
```

**Key points:**
- `values` is a **block type**, not an argument - use `dynamic "values"` not `values = [...]`
- The `for` expression filters values by `external_value` and returns the Okta-generated `id`
- This creates proper resource dependencies so bundles can be created in the same apply as entitlements
- Use locals to define reusable account groupings (standard, limited, full, etc.)

### 11. Entitlement Values Must Be Alphabetically Ordered

**Okta API returns entitlement values sorted alphabetically by `external_value`.**

The Terraform provider compares values by index position, so if your configuration defines values in a different order than the API returns, you'll get "Provider produced inconsistent result after apply" errors.

**Always define values in alphabetical order by `external_value`:**

```hcl
resource "okta_entitlement" "example" {
  name           = "Access Level"
  external_value = "accessLevel"
  data_type      = "string"
  multi_value    = false

  parent {
    external_id = okta_app_oauth.my_app.id
    type        = "APPLICATION"
  }

  # Values MUST be in alphabetical order by external_value
  values {
    external_value = "no"    # "n" comes before "y"
    name           = "No"
    description    = "Access denied"
  }

  values {
    external_value = "yes"   # "y" comes after "n"
    name           = "Yes"
    description    = "Access granted"
  }
}
```

**For array entitlements with many values:**
```hcl
# Sort alphabetically: 149259, 26DEMO14, 26DEMO26, DEMO1, DEMO10, DEMO11, DEMO2...
values {
  external_value = "149259"
  name           = "149259"
  description    = "Banking Account"
}

values {
  external_value = "26DEMO14"
  name           = "26DEMO14"
  description    = "CASH MANAGEMENT II"
}
# ... continue in alphabetical order
```

**Key points:**
- This is undocumented Okta API behavior
- The provider should handle this (set comparison vs list), but currently doesn't
- If you see "inconsistent result after apply" errors on entitlements, check value ordering first

---

## Repository Structure Highlights

### Key Directories

```
.
├── environments/               # Multi-tenant configurations
│   ├── production/            # Production template
│   ├── staging/               # Staging template
│   └── development/           # Development template
├── scripts/                   # Python automation
│   ├── import_oig_resources.py
│   ├── sync_owner_mappings.py
│   ├── apply_resource_owners.py
│   └── apply_admin_labels.py
├── ai-assisted/               # AI code generation tools
│   ├── generate.py           # CLI tool (Tier 2)
│   ├── prompts/              # Prompt templates (Tier 1)
│   ├── context/              # Context for AI
│   └── providers/            # AI provider integrations
├── docs/                      # Comprehensive documentation
├── testing/                   # Validation guides
└── .github/workflows/         # GitHub Actions
```

### Important Documentation Files

**Read these first:**
- `README.md` - Template overview
- `TEMPLATE_SETUP.md` - Step-by-step setup guide
- `DIRECTORY_GUIDE.md` - Environment structure explained
- `OIG_PREREQUISITES.md` - OIG setup requirements
- `docs/GITOPS_WORKFLOW.md` - GitOps patterns
- `docs/API_MANAGEMENT.md` - Python scripts reference (1190+ lines)
- `docs/LESSONS_LEARNED.md` - Critical troubleshooting insights
- `docs/TERRAFORMER_OIG_FAQ.md` - Terraformer + OIG limitations

### Terraform Provider Versions

```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    # Core Okta Provider - Users, Groups, Apps, OIG
    okta = {
      source  = "okta/okta"
      version = ">= 6.4.0, < 7.0.0"  # OIG support requires 6.4.0+
    }

    # Okta Privileged Access Provider (Optional)
    # Uncomment to enable OPA resource management
    # oktapam = {
    #   source  = "okta/oktapam"
    #   version = ">= 0.6.0"  # Latest with security_policy_v2
    # }
  }
}
```

**Critical:** OIG resources require Okta Terraform Provider v6.4.0 or higher.

### Okta Privileged Access (OPA) Integration

This repository supports optional OPA integration via the `oktapam` provider:

**OPA Resources:**
- Server access projects and enrollment tokens
- Secret folders and secrets
- Security policies
- Gateway setup tokens
- Resource groups
- Kubernetes cluster access
- Active Directory integration

**Setup:** See `docs/OPA_SETUP.md` for configuration instructions.

**Example file:** `environments/myorg/terraform/opa_resources.tf.example`

---

## Working with Demos and Environments

### Creating a Demo Environment

**Quick method (AI-assisted):**
1. Use AI to generate Terraform code (see AI-Assisted Commands above)
2. Apply the generated code
3. Assign entitlements in Okta Admin UI
4. Set up resource owners via Python scripts

**Manual method:**
1. Navigate to environment: `cd environments/mycompany/terraform`
2. Create users in `users.tf`
3. Create groups in `groups.tf`
4. Create apps in `apps.tf`
5. Create entitlement bundles in `oig_entitlements.tf`
6. Apply: `terraform apply`
7. Assign bundles in Okta Admin Console

### Demo Scenarios

**Common demo patterns documented in:**
- `DEMO_GUIDE.md` - Demo building with templates, AI, or manual approaches
- `ai-assisted/prompts/create_demo_environment.md` - AI prompt template
- `ai-assisted/examples/example_session_gemini.md` - Real example session

### Recommended Demo Flow

1. **Setup Phase:** Import existing tenant or create from scratch
2. **User Management:** Create users and groups
3. **App Integration:** Set up OAuth apps with proper scopes
4. **OIG Features:** Create entitlement bundles and access reviews
5. **Governance:** Apply labels and assign resource owners
6. **Automation:** Show GitOps workflow with PR → Plan → Approve → Apply

---

## Development Workflow

### Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/add-marketing-team

# 2. Make changes to Terraform files
cd environments/mycompany/terraform
vim users.tf

# 3. Validate locally
terraform fmt
terraform validate
terraform plan

# 4. Commit and push
git add .
git commit -m "feat: Add marketing team users and Salesforce app"
git push -u origin feature/add-marketing-team

# 5. Create PR
gh pr create --title "Add marketing team demo"

# 6. Review automated plan in PR comments
# 7. Get approval and merge
# 8. Manually trigger apply workflow
gh workflow run tf-apply.yml -f environment=mycompany
```

### Syncing from Okta (Drift Detection)

```bash
# Import latest from Okta to detect drift
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyCompany \
  -f update_terraform=false \
  -f commit_changes=false

# Review differences
# Decide to update Terraform or revert manual Okta changes
```

### Troubleshooting

**Common issues and solutions:**

1. **Template interpolation errors**
   - Solution: Use `$$` instead of `$` in Okta template strings

2. **Import fails for OIG resources**
   - Solution: Use `import_oig_resources.py`, not Terraformer

3. **"Entitlement assignments not working"**
   - Solution: Assignments must be managed in Okta Admin UI, not Terraform

4. **OAuth app validation errors**
   - Solution: Check visibility and login_mode rules (see Gotchas #5)

5. **Resource owners not applying**
   - Solution: Ensure API token has governance scopes, check JSON format

6. **Labels API returns 405 errors**
   - Solution: Use `labelId` not `name` in URLs, see `scripts/archive/README.md`

7. **"Error reading campaign" during terraform plan**
   - **Root Cause:** Provider bug - entitlement bundles have stale campaign associations from deleted access review campaigns
   - **Solution:** Run fix workflow: `gh workflow run fix-bundle-campaign-errors.yml -f environment=mycompany -f dry_run=false -f bundles_to_fix=all`
   - **Prevention:** Use `terraform plan -refresh=false` or `-target` to skip affected bundles until fixed

**For detailed troubleshooting, see:**
- `docs/TROUBLESHOOTING_ENTITLEMENT_BUNDLES.md` - Campaign association errors and fixes
- `docs/LESSONS_LEARNED.md` - Known issues and solutions
- `docs/LABELS_API_VALIDATION.md` - Labels API investigation results

---

## Python Scripts Architecture

### Key Scripts

**Import and Sync:**
- `import_oig_resources.py` - Import OIG resources from Okta API
- `sync_owner_mappings.py` - Sync resource owners from Okta
- `sync_label_mappings.py` - Sync governance labels from Okta

**Apply:**
- `apply_resource_owners.py` - Apply owners to resources
- `apply_admin_labels.py` - Auto-label admin entitlements

**Investigation (archived):**
- `scripts/archive/test_*.py` - Labels API troubleshooting scripts

### Python Dependencies

```bash
# Core dependencies
requests>=2.31.0        # HTTP library
python-dotenv>=1.0.0    # Environment variables
pyyaml>=6.0             # YAML support
tabulate>=0.9.0         # Table formatting
colorama>=0.4.6         # Colored output
```

### API Manager Module

**Graceful degradation pattern:**

```python
# Returns status codes: success, not_available, error, skipped
# HTTP 400/404 treated as "not available" instead of errors
# Allows scripts to work in orgs without full OIG features
```

**This enables:**
- Scripts work in any Okta org (OIG or not)
- Partial feature availability handled gracefully
- Clear status reporting per operation

---

## Testing Approach

**Manual validation checklist:**
```bash
cp testing/MANUAL_VALIDATION_PLAN.md testing/validation_run_$(date +%Y%m%d).md
# Fill out checklist: ~2-3 hours for complete validation
```

**Automated checks (via GitHub Actions):**
- Terraform format validation
- Terraform validate
- Terraform plan (on PR)
- Python script dry-runs

**Demo validation:**
- Follow `DEMO_GUIDE.md`
- Verify OIG features in Okta Admin Console
- Test approval workflows
- Validate access reviews

---

## Customizing for Your Organization

### Steps After Forking

1. **Remove template environments (optional)**
   ```bash
   # Create your first real environment
   mkdir -p environments/mycompany/{terraform,imports,config}

   # Copy template files
   cp environments/myorg/terraform/* environments/mycompany/terraform/
   cp environments/myorg/config/* environments/mycompany/config/
   ```

2. **Set up GitHub Environments**
   - Go to Settings → Environments
   - Create environment matching your directory name
   - Add secrets: `OKTA_API_TOKEN`, `OKTA_ORG_NAME`, `OKTA_BASE_URL`

3. **Import your Okta tenant**
   ```bash
   gh workflow run import-all-resources.yml -f tenant_environment=MyCompany
   ```

4. **Update this CLAUDE.md**
   - Document your org-specific patterns
   - Add environment-specific notes
   - Customize examples for your use case

5. **Document your patterns**
   - Update `DEMO_GUIDE.md` with your demo scenarios
   - Create environment-specific READMEs

---

## AWS Backend Integration

### S3 State Backend

All Terraform state is stored in AWS S3 with DynamoDB locking:

**Benefits:**
- ✅ Team collaboration without state conflicts
- ✅ State history and versioning for rollback
- ✅ Encryption at rest and in transit
- ✅ State locking prevents concurrent modifications
- ✅ Automated backups via S3 versioning

**Setup:**
1. Deploy backend infrastructure: `cd aws-backend && terraform apply`
2. Add `AWS_ROLE_ARN` secret to GitHub
3. Migrate existing state: `terraform init -migrate-state`

**See:** `docs/AWS_BACKEND_SETUP.md` for complete setup and migration guide

### GitHub Actions with AWS OIDC

Workflows authenticate with AWS using OpenID Connect:

```yaml
permissions:
  id-token: write  # Required for OIDC
  contents: read

- name: Configure AWS Credentials via OIDC
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    role-session-name: GitHubActions-Terraform
    aws-region: us-east-1
```

**No AWS access keys stored in GitHub!** OIDC provides temporary credentials.

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

This repository is designed for **managing Okta with GitOps**, so focus on:
- Clear, understandable configurations
- GitOps best practices
- OIG feature management (including label management workflow)
- OPA integration for privileged access (optional)
- AWS backend for production-ready state management
- Easy-to-customize structure
- Two-phase validation for governance changes
