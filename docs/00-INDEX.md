# Documentation Index

**Welcome to the Okta Terraform Demo Template Documentation!**

This index helps you find the right documentation for your needs.

---

## Quick Start - Choose Your Path

**New to this repository?** Start with the simplified guides at the root level:

| Your Goal | Guide | Time |
|-----------|-------|------|
| **Learn Terraform basics** | [LOCAL-USAGE.md](../LOCAL-USAGE.md) | 15 min |
| **Back up code in GitHub** | [GITHUB-BASIC.md](../GITHUB-BASIC.md) | 20 min |
| **Full GitOps with CI/CD** | [GITHUB-GITOPS.md](../GITHUB-GITOPS.md) | 45 min |
| **Build demos** | [DEMO_GUIDE.md](../DEMO_GUIDE.md) | 30-60 min |
| **Terraform examples** | [TERRAFORM-BASICS.md](../TERRAFORM-BASICS.md) | Reference |
| **Fix problems** | [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Reference |

**Recommended learning path:**
```
LOCAL-USAGE.md → GITHUB-BASIC.md → GITHUB-GITOPS.md
   (15 min)        (20 min)          (45 min)
```

---

## Reference Documentation

This folder contains advanced reference documentation for specific topics.

### Workflows & Operations

| Document | Purpose |
|----------|---------|
| [03-WORKFLOWS-GUIDE.md](03-WORKFLOWS-GUIDE.md) | Complete GitHub Actions workflow reference |

### Infrastructure

| Document | Purpose |
|----------|---------|
| [AWS_BACKEND_SETUP.md](AWS_BACKEND_SETUP.md) | S3/DynamoDB state backend setup |
| [BACKEND_SETUP_WIZARD.md](BACKEND_SETUP_WIZARD.md) | Choose the right backend for your needs |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Repository layout and file organization |
| [DIRECTORY_GUIDE.md](DIRECTORY_GUIDE.md) | Environment-based directory structure |

### API & Python Scripts

| Document | Purpose |
|----------|---------|
| [API_MANAGEMENT.md](API_MANAGEMENT.md) | **Main API guide** - Owners, Labels, Risk Rules (1190+ lines) |
| [LABELS_API_VALIDATION.md](LABELS_API_VALIDATION.md) | Labels API investigation and findings |
| [LESSONS_LEARNED.md](LESSONS_LEARNED.md) | Troubleshooting insights and workarounds |

### OIG & Governance

| Document | Purpose |
|----------|---------|
| [../OIG_PREREQUISITES.md](../OIG_PREREQUISITES.md) | OIG setup requirements |
| [ENTITLEMENT_SETTINGS.md](ENTITLEMENT_SETTINGS.md) | Enable/disable entitlement management via API (Beta) |
| [LABEL_MANAGEMENT.md](LABEL_MANAGEMENT.md) | Governance labels technical guide |
| [LABEL_WORKFLOW_GUIDE.md](LABEL_WORKFLOW_GUIDE.md) | Label management GitOps workflow |
| [TROUBLESHOOTING_ENTITLEMENT_BUNDLES.md](TROUBLESHOOTING_ENTITLEMENT_BUNDLES.md) | Bundle-specific troubleshooting |

### Backup & Disaster Recovery

| Document | Purpose |
|----------|---------|
| [BACKUP_RESTORE.md](BACKUP_RESTORE.md) | Complete backup and restore guide |
| [ROLLBACK_GUIDE.md](ROLLBACK_GUIDE.md) | Git and state rollback procedures |

### Import & Migration

| Document | Purpose |
|----------|---------|
| [TERRAFORMER.md](TERRAFORMER.md) | Terraformer import tool - complete guide |
| [CROSS_ORG_MIGRATION.md](CROSS_ORG_MIGRATION.md) | Cross-org migration workflows and scripts |

### Okta Terraform Provider Analysis

| Document | Purpose |
|----------|---------|
| [PROVIDER_REVIEW_SUMMARY.md](PROVIDER_REVIEW_SUMMARY.md) | Executive summary of provider analysis |
| [PROVIDER_ANALYSIS.md](PROVIDER_ANALYSIS.md) | Complete resource analysis (15K words) |
| [PROVIDER_COVERAGE_MATRIX.md](PROVIDER_COVERAGE_MATRIX.md) | Resource coverage by category |

### Integration & Advanced

| Document | Purpose |
|----------|---------|
| [DEMO_PLATFORM_INTEGRATION.md](DEMO_PLATFORM_INTEGRATION.md) | Demo Platform webhook integration |
| [OAUTH_AUTHENTICATION_NOTES.md](OAUTH_AUTHENTICATION_NOTES.md) | OAuth authentication setup |
| [SCIM_OKTA_AUTOMATION.md](SCIM_OKTA_AUTOMATION.md) | SCIM provisioning guide |
| [TEMPLATE_SYNC_SETUP.md](TEMPLATE_SYNC_SETUP.md) | Template synchronization |
| [GITOPS_VALUE.md](GITOPS_VALUE.md) | Business value of GitOps with citations |

### Contributing

| Document | Purpose |
|----------|---------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |

---

## Find Documentation By Topic

### "I want to..."

| Task | Start Here |
|------|-----------|
| **Get started quickly** | [LOCAL-USAGE.md](../LOCAL-USAGE.md) |
| **Set up full GitOps** | [GITHUB-GITOPS.md](../GITHUB-GITOPS.md) |
| **Build a demo** | [DEMO_GUIDE.md](../DEMO_GUIDE.md) |
| **Set up AWS backend** | [AWS_BACKEND_SETUP.md](AWS_BACKEND_SETUP.md) |
| **Manage governance labels** | [LABEL_WORKFLOW_GUIDE.md](LABEL_WORKFLOW_GUIDE.md) |
| **Manage resource owners** | [API_MANAGEMENT.md](API_MANAGEMENT.md) |
| **Enable entitlement management on apps** | [ENTITLEMENT_SETTINGS.md](ENTITLEMENT_SETTINGS.md) |
| **Set up Okta Privileged Access** | [OPA_SETUP.md](OPA_SETUP.md) |
| **Import from Okta** | [03-WORKFLOWS-GUIDE.md](03-WORKFLOWS-GUIDE.md) |
| **Copy resources between orgs** | [CROSS_ORG_MIGRATION.md](CROSS_ORG_MIGRATION.md) |
| **Backup and restore tenant** | [BACKUP_RESTORE.md](BACKUP_RESTORE.md) |
| **Troubleshoot issues** | [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) |
| **Use AI to generate code** | [ai-assisted/README.md](../ai-assisted/README.md) |
| **Understand provider coverage** | [PROVIDER_COVERAGE_MATRIX.md](PROVIDER_COVERAGE_MATRIX.md) |

---

## Special Purpose Documents

| Document | Purpose |
|----------|---------|
| [../CLAUDE.md](../CLAUDE.md) | AI assistant context (for Claude Code) |
| [../CHANGELOG.md](../CHANGELOG.md) | Version history |
| [../SECURITY.md](../SECURITY.md) | Security policy |

---

## Archived Documentation

Older documentation that has been superseded is available in [archive/](archive/).

---

**Last Updated:** 2025-12-22
