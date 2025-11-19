# Documentation Index

**Welcome to the Okta Terraform Demo Template Documentation!**

This index helps you find the right documentation for your needs.

---

## 🚀 Getting Started

**New to this template? Start here:**

1. **[README.md](../README.md)** - Overview and features
2. **[TEMPLATE_SETUP.md](../TEMPLATE_SETUP.md)** - Complete setup guide (secrets, environments, GitHub)
3. **[OIG_PREREQUISITES.md](../OIG_PREREQUISITES.md)** - Required OIG setup in Okta Admin UI
4. **[FORKING_GUIDE.md](FORKING_GUIDE.md)** - How to customize for your organization

**Quick References:**
- **[DIRECTORY_GUIDE.md](../DIRECTORY_GUIDE.md)** - Repository structure explained
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Detailed file organization

---

## 📖 Core Documentation

### Setup & Configuration

| Document | Purpose |
|----------|---------|
| [TEMPLATE_SETUP.md](../TEMPLATE_SETUP.md) | First-time setup (GitHub secrets, environments, AWS backend) |
| [OIG_PREREQUISITES.md](../OIG_PREREQUISITES.md) | Okta Identity Governance prerequisites |
| [ENVIRONMENT_SETUP_EXAMPLE.md](ENVIRONMENT_SETUP_EXAMPLE.md) | Step-by-step environment creation example |
| [AWS_BACKEND_SETUP.md](AWS_BACKEND_SETUP.md) | S3 + DynamoDB backend setup |
| [BACKEND_SETUP_WIZARD.md](BACKEND_SETUP_WIZARD.md) | Interactive backend setup script |

### Workflows & Automation

| Document | Purpose |
|----------|---------|
| [03-WORKFLOWS-GUIDE.md](03-WORKFLOWS-GUIDE.md) | Complete workflows reference |
| [WORKFLOWS.md](WORKFLOWS.md) | Workflow descriptions and usage |
| [GITOPS_WORKFLOW.md](GITOPS_WORKFLOW.md) | GitOps patterns and best practices |
| [LABEL_WORKFLOW_GUIDE.md](LABEL_WORKFLOW_GUIDE.md) | Label management workflow (2-phase validation) |
| [LABEL_MANAGEMENT.md](LABEL_MANAGEMENT.md) | Governance labels overview |

### API Management

| Document | Purpose |
|----------|---------|
| [API_MANAGEMENT.md](API_MANAGEMENT.md) | **Main API guide** - Owners, Labels, Risk Rules (1190+ lines) |
| [LABELS_API_VALIDATION.md](LABELS_API_VALIDATION.md) | Labels API investigation and findings |
| [LESSONS_LEARNED.md](LESSONS_LEARNED.md) | Troubleshooting insights and workarounds |

### Terraform

| Document | Purpose |
|----------|---------|
| [TERRAFORM_RESOURCES.md](TERRAFORM_RESOURCES.md) | Terraform resource reference |
| [TERRAFORMER.md](TERRAFORMER.md) | Terraformer import tool usage |
| [TERRAFORMER_OIG_FAQ.md](TERRAFORMER_OIG_FAQ.md) | Terraformer + OIG limitations |
| [TROUBLESHOOTING_ENTITLEMENT_BUNDLES.md](TROUBLESHOOTING_ENTITLEMENT_BUNDLES.md) | Campaign association errors and fixes |
| [OIG_MANUAL_IMPORT.md](OIG_MANUAL_IMPORT.md) | Manual OIG import procedures |

### Okta Terraform Provider Analysis

| Document | Purpose |
|----------|---------|
| [PROVIDER_ANALYSIS.md](PROVIDER_ANALYSIS.md) | **Complete provider analysis** - Resources, documentation, gaps (15K words) |
| [PROVIDER_COVERAGE_MATRIX.md](PROVIDER_COVERAGE_MATRIX.md) | Resource coverage by category - What's available vs missing (8K words) |
| [../PROVIDER_REVIEW_SUMMARY.md](../PROVIDER_REVIEW_SUMMARY.md) | **Executive summary** of provider review and recommendations |

**Key Insights:**
- 103 resources and 47 data sources analyzed
- 3 CRITICAL missing OIG features (owners, labels, risk rules)
- Validation workflow recommendations
- Documentation enhancement opportunities

---

## 🤖 AI-Assisted Development

**Location:** `ai-assisted/` directory

| Document | Purpose |
|----------|---------|
| [ai-assisted/README.md](../ai-assisted/README.md) | Main AI generation guide |
| [ai-assisted/GEM_SETUP_GUIDE.md](../ai-assisted/GEM_SETUP_GUIDE.md) | Google Gemini setup |
| [ai-assisted/GEM_QUICK_REFERENCE.md](../ai-assisted/GEM_QUICK_REFERENCE.md) | Gemini quick commands |
| [ai-assisted/prompts/](../ai-assisted/prompts/) | Ready-to-use prompts |
| [ai-assisted/examples/](../ai-assisted/examples/) | Example sessions |

---

## 🧪 Testing & Validation

**Location:** `testing/` directory

| Document | Purpose |
|----------|---------|
| [testing/README.md](../testing/README.md) | Testing overview |
| [testing/MANUAL_VALIDATION_PLAN.md](../testing/MANUAL_VALIDATION_PLAN.md) | Complete validation checklist |
| [testing/DETAILED_DEMO_BUILD_GUIDE.md](../testing/DETAILED_DEMO_BUILD_GUIDE.md) | Step-by-step demo creation |

---

## 📋 Reference Materials

### Architecture & Design

| Document | Purpose |
|----------|---------|
| [COMPLETE_SOLUTION.md](COMPLETE_SOLUTION.md) | Architecture overview |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | File and directory layout |
| [01-GETTING-STARTED.md](01-GETTING-STARTED.md) | Getting started guide |

### Operational Guides

| Document | Purpose |
|----------|---------|
| [ROLLBACK_GUIDE.md](ROLLBACK_GUIDE.md) | How to rollback changes |
| [TESTING.md](TESTING.md) | Testing strategies |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |

---

## 🔍 Finding What You Need

### "I want to..."

| Task | Start Here |
|------|-----------|
| **Set up for the first time** | [TEMPLATE_SETUP.md](../TEMPLATE_SETUP.md) |
| **Fork for my organization** | [FORKING_GUIDE.md](FORKING_GUIDE.md) |
| **Import existing Okta config** | [03-WORKFLOWS-GUIDE.md](03-WORKFLOWS-GUIDE.md) → Import All Resources |
| **Manage governance labels** | [LABEL_WORKFLOW_GUIDE.md](LABEL_WORKFLOW_GUIDE.md) |
| **Manage resource owners** | [API_MANAGEMENT.md](API_MANAGEMENT.md) → Resource Owners |
| **Manage risk rules (SOD policies)** | [API_MANAGEMENT.md](API_MANAGEMENT.md) → Risk Rules |
| **Create a demo environment** | [testing/DETAILED_DEMO_BUILD_GUIDE.md](../testing/DETAILED_DEMO_BUILD_GUIDE.md) |
| **Use AI to generate code** | [ai-assisted/README.md](../ai-assisted/README.md) |
| **Troubleshoot issues** | [LESSONS_LEARNED.md](LESSONS_LEARNED.md) |
| **Set up AWS backend** | [AWS_BACKEND_SETUP.md](AWS_BACKEND_SETUP.md) |
| **Understand Terraformer** | [TERRAFORMER_OIG_FAQ.md](TERRAFORMER_OIG_FAQ.md) |
| **Check provider resource coverage** | [PROVIDER_COVERAGE_MATRIX.md](PROVIDER_COVERAGE_MATRIX.md) |
| **Understand provider limitations** | [PROVIDER_ANALYSIS.md](PROVIDER_ANALYSIS.md) |

---

## 📚 Documentation By Topic

### Governance Features

- **Labels:** [LABEL_MANAGEMENT.md](LABEL_MANAGEMENT.md), [LABEL_WORKFLOW_GUIDE.md](LABEL_WORKFLOW_GUIDE.md)
- **Owners:** [API_MANAGEMENT.md](API_MANAGEMENT.md) → Resource Owners section
- **Risk Rules:** [API_MANAGEMENT.md](API_MANAGEMENT.md) → Risk Rules section

### Import & Export

- **Complete Import:** [03-WORKFLOWS-GUIDE.md](03-WORKFLOWS-GUIDE.md) → Import All Resources
- **Terraformer:** [TERRAFORMER.md](TERRAFORMER.md), [TERRAFORMER_OIG_FAQ.md](TERRAFORMER_OIG_FAQ.md)
- **OIG Manual Import:** [OIG_MANUAL_IMPORT.md](OIG_MANUAL_IMPORT.md)

### Infrastructure

- **AWS Backend:** [AWS_BACKEND_SETUP.md](AWS_BACKEND_SETUP.md)
- **State Management:** [AWS_BACKEND_SETUP.md](AWS_BACKEND_SETUP.md) → State section
- **GitHub Actions:** [03-WORKFLOWS-GUIDE.md](03-WORKFLOWS-GUIDE.md)

---

## 🆘 Need Help?

1. **Check [LESSONS_LEARNED.md](LESSONS_LEARNED.md)** - Common issues and solutions
2. **Check [TROUBLESHOOTING_ENTITLEMENT_BUNDLES.md](TROUBLESHOOTING_ENTITLEMENT_BUNDLES.md)** - Bundle-specific issues
3. **Review [API_MANAGEMENT.md](API_MANAGEMENT.md)** - Comprehensive API operations guide
4. **Check GitHub Issues** - Search for similar problems

---

## 📝 Special Purpose Documents

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](../CLAUDE.md) | AI assistant context (for Claude Code) |
| [CHANGELOG.md](../CHANGELOG.md) | Version history |
| [SECURITY.md](../SECURITY.md) | Security policy |

---

**Last Updated:** 2025-11-13
**Maintained By:** Template maintainers
**Feedback:** Open an issue if you find broken links or missing documentation
