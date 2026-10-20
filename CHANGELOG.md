# Changelog

All notable changes to this template will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-10-20

### Changed

#### Okta Terraform provider v7 (okta/okta `>= 7.0.0, < 8.0.0`)
- Provider constraint bumped from `>= 6.4.0, < 7.0.0` to `>= 7.0.0, < 8.0.0` in `environments/myorg/terraform/provider.tf`, both Okta modules, and the Terraformer bootstrap script. Run `terraform init -upgrade` in each environment.
- v7.0.0 breaking changes that affect example code: `okta_trusted_origin` (`scopes` is now a repeated block, `active` became `status`), `okta_threat_insight_settings` (`network_excludes` -> `exclude_zones`), `okta_template_sms` (`translations` is a map), `okta_role_subscription` (`role_type` -> `role_ref`), `okta_captcha_org_wide_settings` deprecated in favour of `okta_org_captcha`. None of the resources used by the modules are affected.
- `environments/myorg/terraform/RESOURCE_EXAMPLES.tf` re-verified against v7.0.0 with `terraform validate` (the previous OIG examples used multi-argument single-line blocks that HCL rejects, and 12 other examples carried attributes that no longer exist). New sections cover `okta_label`, `okta_resource_owner`, `okta_group_owners`, `okta_app_connection` / `okta_app_features`, `okta_realm` / `okta_realm_assignment`, ITP policy rules and `okta_security_events_provider`, app sign-on policies, rate limits, and the v7 replacements above.
- `docs/reference/provider-coverage.md` rewritten for v7.0.0 (162 resources, 109 data sources): resource owners and label definitions are now Terraform; label assignment, risk rules and bundle grants remain API-only.

### Fixed

- `modules/lifecycle-management`: `okta_event_hook.channel` is a map attribute, not a block, and every `okta_entitlement_bundle` needs a `target` (new `oig_target_app_id` input plus per-bundle overrides). The module did not pass `terraform validate` on any 6.x provider.
- `modules/saml-federation`: `okta_policy_rule_idp_discovery` takes an `idp_providers` block, not `idp_type`/`idp_id`.
- Stale resource names (`okta_reviews`, `okta_request_sequences`, `okta_request_conditions`, `okta_request_settings`, `okta_access_review_campaign`, `okta_group_memberships.members`) and the wrong `okta_entitlement` schema corrected across docs, AI context files, `scripts/import_oig_resources.py`, `scripts/build_demo.py`, and the restore workflow.

### Added

- `tf-validate.yml` now validates both Okta modules and the uncommented `RESOURCE_EXAMPLES.tf` against the pinned provider on every PR.

## [2.0.0] - 2025-11-12

### Added

#### Gemini Gem Support (Tier 3 AI-Assisted Generation)
- **ai-assisted/GEM_INSTRUCTIONS.md** - Consolidated instructions for creating a Gemini Gem (~400 lines)
  - Complete system instructions for Terraform code generation
  - Repository-specific rules and patterns
  - Critical Terraform syntax rules (template escaping, OAuth validation)
  - Three-layer resource management model

- **ai-assisted/GEM_QUICK_REFERENCE.md** - Condensed context for Gem knowledge base (~250 lines)
  - Essential Terraform patterns
  - Resource type quick reference
  - OAuth app type comparison
  - Validation checklist

- **ai-assisted/GEM_SETUP_GUIDE.md** - Step-by-step Gem creation guide
  - Complete setup instructions (15 min one-time setup)
  - Three usage methods: Direct commit, PR workflow, Codespaces
  - GitHub web UI integration (no local git required)
  - Cost analysis and ROI calculation
  - Troubleshooting and best practices

#### Template Sync Automation
- **.github/workflows/sync-template.yml** - Automatic template update workflow
  - Runs weekly on Sundays at 2 AM UTC
  - Manual trigger via workflow dispatch
  - Creates pull request with template updates
  - Handles merge conflicts gracefully
  - Provides detailed PR descriptions

#### Documentation Improvements
- **README.md** - Added "Keeping Your Repository Updated" section
  - Automatic sync workflow instructions
  - Manual sync alternative
  - Stay notified guide
  - Recent updates summary

- **CHANGELOG.md** - This file, tracking all notable changes

### Changed

- **ai-assisted/README.md** - Updated to include Tier 3 (Gemini Gem)
  - Added Tier 3 to Quick Start section
  - Complete Tier 3 section with setup, usage, advantages
  - Updated comparison tables (Tier 1 vs 2 vs 3)
  - Updated cost comparison with Gem pricing
  - Updated directory structure

### Benefits of This Release

**For Solutions Engineers:**
- ✨ Fastest code generation: 1 minute vs 10-15 minutes manual
- 🌐 No installation required: Browser-based workflow
- 📱 Mobile accessible: Works on any device
- 🔄 Automatic updates: Stay current with template improvements
- 💰 Cost-effective: Free tier sufficient for most users

**For Organizations:**
- 🎯 Lower barrier to entry for demo creation
- 🤝 Easy team sharing via Gem links
- 📈 20-100x ROI vs manual demo building
- 🔒 Security: No local git installation vulnerabilities
- 🔄 Consistent quality across team

## [1.0.0] - 2025-11-07

### Initial Release

Complete GitOps template for managing Okta Identity Governance with Terraform.

#### Features

**Infrastructure as Code**
- Multi-tenant environment structure (one directory = one Okta org)
- Terraform provider configuration for Okta (v6.4.0+)
- AWS S3 backend with DynamoDB locking
- Complete Terraform state management

**GitHub Actions Workflows**
- `terraform-plan.yml` - Automatic plan on PR and push
- `terraform-apply-with-approval.yml` - Manual apply with approval gates
- `import-all-resources.yml` - Import Okta resources to Terraform
- `apply-owners.yml` - Sync resource owners
- `apply-admin-labels.yml` - Auto-label admin resources
- `apply-labels-from-config.yml` - Deploy governance labels
- `validate-label-mappings.yml` - PR validation for labels

**Python Automation Scripts**
- `import_oig_resources.py` - Import OIG resources from Okta API
- `sync_owner_mappings.py` - Sync resource owners from Okta
- `apply_resource_owners.py` - Apply owners to resources
- `sync_label_mappings.py` - Sync governance labels
- `apply_governance_labels.py` - Apply labels via API
- `find_admin_resources.py` - Identify admin entitlements
- `apply_admin_labels.py` - Auto-label admin resources

**AI-Assisted Generation (Tier 1 & 2)**
- Tier 1: Manual prompt engineering with context files
- Tier 2: CLI tool with Gemini/OpenAI/Claude integration
- Prompt templates: create_demo_environment, add_users, create_app, oig_setup
- Context files: repository_structure, terraform_examples, okta_resource_guide

**Documentation**
- QUICKSTART.md - 10-minute quick start guide
- TEMPLATE_SETUP.md - Comprehensive setup instructions
- OIG_PREREQUISITES.md - Okta Identity Governance prerequisites
- DIRECTORY_GUIDE.md - Repository structure explanation
- docs/GITOPS_WORKFLOW.md - GitOps patterns and best practices
- docs/API_MANAGEMENT.md - Python scripts reference (1190+ lines)
- docs/AWS_BACKEND_SETUP.md - S3 backend configuration
- docs/LESSONS_LEARNED.md - Troubleshooting guide
- docs/TERRAFORMER_OIG_FAQ.md - Terraformer limitations
- testing/DETAILED_DEMO_BUILD_GUIDE.md - Demo creation guide
- testing/MANUAL_VALIDATION_PLAN.md - Validation checklist

**Security Features**
- GitHub Environment secrets separation
- AWS OIDC authentication (no long-lived credentials)
- Two-phase label validation workflow
- Branch protection patterns
- Approval gates for production

### Known Limitations

- Terraformer does not support OIG resources (use Python import scripts)
- Resource owners and governance labels require Python API scripts
- Entitlement bundle assignments managed in Okta Admin UI
- System apps cannot be managed via Terraform

---

## Version History

- **2.0.0** (2025-11-12) - Gemini Gem support, template sync automation, GitHub web UI integration
- **1.0.0** (2025-11-07) - Initial complete template release

---

## Upgrading

### From 1.0.0 to 2.0.0

**No breaking changes!** All existing functionality preserved.

**New features available:**
1. Create a Gemini Gem for faster demo generation (optional)
2. Enable sync-template workflow for automatic updates (recommended)
3. Use GitHub web UI workflow for non-git users (optional)

**To adopt new features:**

```bash
# Pull latest changes
git fetch template
git merge template/main

# Or use the new sync workflow:
gh workflow run sync-template.yml
```

**Review new files:**
- `ai-assisted/GEM_*.md` - Gemini Gem documentation
- `.github/workflows/sync-template.yml` - Auto-sync workflow
- `CHANGELOG.md` - This file

---

## Contributing

See the repository's contribution guidelines for:
- Reporting bugs
- Suggesting enhancements
- Submitting pull requests
- Documentation improvements

---

## Support

**Questions or issues?**
1. Check [troubleshooting documentation](./docs/LESSONS_LEARNED.md)
2. Review [FAQ](./docs/TERRAFORMER_OIG_FAQ.md)
3. File an issue on GitHub
4. Review closed issues for solutions

---

**Template maintained by:** [@joevanhorn](https://github.com/joevanhorn)
