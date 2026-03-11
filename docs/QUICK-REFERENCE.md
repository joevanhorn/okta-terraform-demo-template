# Quick Reference

Single-page cheat sheet for the okta-terraform-demo-template repository.

---

## Key File Paths

| What | Where |
|------|-------|
| Your Okta resources | `environments/{env}/terraform/*.tf` |
| Config files (owners, labels, risk rules) | `environments/{env}/config/*.json` |
| Infrastructure (AD, DB, OPC, SCIM) | `environments/{env}/*-infrastructure/` |
| Reusable modules | `modules/` (ad-domain-controller, generic-db-connector, opc-agent, itp-demo, lifecycle-management, saml-federation) |
| Python scripts | `scripts/` |
| GitHub Actions workflows | `.github/workflows/` |
| Demo YAML examples | `demo-builder/examples/` |
| Provider config | `environments/{env}/terraform/provider.tf` |

---

## Common Commands

### Terraform

```bash
cd environments/myorg/terraform
terraform init            # Initialize (S3 backend)
terraform fmt             # Format code
terraform validate        # Validate syntax
terraform plan            # Preview changes
terraform apply           # Apply (with approval)
```

### Key Workflows

| I want to... | Workflow | Command |
|--------------|----------|---------|
| Import resources from Okta | `import-all-resources.yml` | `gh workflow run import-all-resources.yml -f tenant_environment=MyOrg -f commit_changes=true` |
| Apply Terraform changes | `tf-apply.yml` | `gh workflow run tf-apply.yml -f environment=myorg` |
| Assign resource owners | `oig-owners.yml` | `gh workflow run oig-owners.yml -f environment=myorg -f dry_run=false` |
| Apply governance labels | `labels-apply-from-config.yml` | `gh workflow run labels-apply-from-config.yml -f environment=myorg -f dry_run=false` |
| Auto-label admin entitlements | `labels-apply.yml` | `gh workflow run labels-apply.yml -f label_type=admin -f environment=myorg -f dry_run=false` |
| Sync labels from Okta | `labels-sync.yml` | `gh workflow run labels-sync.yml -f environment=myorg -f commit_changes=true` |
| Export OIG for backup | `export-oig.yml` | `gh workflow run export-oig.yml -f environment=myorg` |
| Fix bundle campaign errors | `fix-bundle-campaign-errors.yml` | `gh workflow run fix-bundle-campaign-errors.yml -f environment=myorg -f dry_run=false` |
| Deploy AD Domain Controller | `ad-deploy.yml` | `gh workflow run ad-deploy.yml -f environment=myorg -f action=plan` |
| Plan OPA resources | `opa-plan.yml` | `gh workflow run opa-plan.yml -f environment=myorg` |
| Deploy SCIM server | `deploy-scim-server.yml` | `gh workflow run deploy-scim-server.yml -f environment=myorg` |
| Run ITP demo | `itp-demo-trigger.yml` | `gh workflow run itp-demo-trigger.yml -f environment=myorg -f mode=quick -f user_email=user@example.com` |

### Key Python Scripts

| Script | Purpose |
|--------|---------|
| `scripts/import_oig_resources.py` | Import OIG resources from Okta |
| `scripts/apply_resource_owners.py` | Apply resource owners (not in Terraform) |
| `scripts/apply_admin_labels.py` | Apply governance labels (not in Terraform) |
| `scripts/apply_risk_rules.py` | Apply risk rules / SOD policies |
| `scripts/manage_entitlement_settings.py` | Enable/disable entitlement management on apps |
| `scripts/build_demo.py` | Generate Terraform from YAML config |
| `modules/itp-demo/scripts/trigger_itp_demo.py` | ITP demo trigger (quick/real/ssf modes) |

---

## Workflow Categories

Workflows use prefixes for easy identification:

| Prefix | Category | Auto-triggered? |
|--------|----------|-----------------|
| `tf-*` | Terraform plan/apply/validate | `tf-plan` on PR, `validate-pr` on PR |
| `oig-*` | OIG governance operations | No |
| `labels-*` | Label management | `labels-validate` on PR, `labels-apply-from-config` dry-run on merge |
| `ad-*` | Active Directory | No |
| `generic-db-*` | Generic DB Connector | No |
| `opc-*` | OPC Agent | No |
| `opa-*` | OPA Privileged Access | No |
| `scim-*` | SCIM Server | No |
| `itp-*` | Identity Threat Protection | No |
| `diagnose-*` | Diagnostics | No |

---

## Three-Layer Resource Model

| Layer | What | Where | Managed By |
|-------|------|-------|------------|
| 1 | Users, groups, apps, bundles, reviews, policies | `*.tf` files | Terraform |
| 2 | Resource owners, labels, risk rules, entitlement settings | `config/*.json` | Python scripts |
| 3 | Bundle assignments, review decisions | Okta Admin UI | Manual |

---

## Critical Gotchas

### 1. Template String Escaping
```hcl
# WRONG -- Terraform interprets ${...}
user_name_template = "${source.login}"

# RIGHT -- double $$ escapes for Okta templates
user_name_template = "$${source.login}"
```

### 2. Entitlement Assignments Are Manual
Terraform creates bundle **definitions** only. Assigning bundles to users/groups is done in Okta Admin UI -- not Terraform.

### 3. Entitlement Values Must Be Alphabetically Ordered
Okta API returns values sorted by `external_value`. Mismatched order causes "inconsistent result after apply" errors.

### 4. OAuth Apps Can't Create OAuth Apps
OAuth-authenticated service apps cannot create other OAuth apps. Use API tokens instead.

### 5. Labels Use Two-Phase Workflow
- **Phase 1 (PR):** Syntax validation only -- no Okta API calls, no secrets needed
- **Phase 2 (Deploy):** Auto dry-run on merge, manual apply via workflow dispatch

---

## Adding a New Environment

```bash
# 1. Create directory
mkdir -p environments/mycompany/{terraform,imports,config}

# 2. Copy provider template
cp environments/myorg/terraform/provider.tf environments/mycompany/terraform/

# 3. Set up GitHub Environment secrets:
#    OKTA_API_TOKEN, OKTA_ORG_NAME, OKTA_BASE_URL, AWS_ROLE_ARN

# 4. Import existing resources
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyCompany \
  -f update_terraform=true \
  -f commit_changes=true
```

---

## GitOps Flow

```
Branch → Edit .tf files → PR (auto: plan + validate) → Review → Merge → Manual: tf-apply.yml
```

Merging does NOT auto-apply. You must manually trigger `tf-apply.yml` after merge.

---

**Full documentation:** [docs/README.md](README.md) | **Troubleshooting:** [troubleshooting/general.md](troubleshooting/general.md)
