# Okta Terraform GitOps Template

**🎯 This is a GitHub Template Repository** - Click "Use this template" to create your own fork!

A complete GitOps solution for managing Okta Identity Governance (OIG) using Infrastructure as Code with Terraform, GitHub Actions, and Python automation.

## 🚀 Quick Start

### ⚡ First Time Here? Start Here!

**👉 [QUICKSTART.md](./QUICKSTART.md) - Get your first success in 10 minutes!**

No prior knowledge needed - just follow the step-by-step guide to:
1. Click "Use this template"
2. Add your Okta credentials
3. Import your Okta org into code
4. See the results!

### 📚 Detailed Setup

For comprehensive setup with all options:
**[TEMPLATE_SETUP.md](./TEMPLATE_SETUP.md)** - Complete setup guide covering:
- AWS backend configuration
- Multiple environments
- Advanced options
- Testing and validation

## What's Included

This template provides everything you need to manage Okta with GitOps:

- ✅ **Multi-tenant structure** - Manage multiple Okta organizations
- ✅ **GitHub Actions workflows** - Automated validation, planning, and deployment
- ✅ **AWS S3 state backend** - Team collaboration with state locking
- ✅ **Python automation scripts** - Resource owners, labels, and bulk operations
- ✅ **AI-assisted generation** - Quickly create demo environments
- ✅ **Comprehensive documentation** - Guides for every scenario
- ✅ **Template environments** - Production, staging, and development ready to customize

## 🚨 Important: Terraformer Limitations

**Terraformer does NOT import OIG resources** (the Terraform provider endpoints are new).

**What this means:**
- ✅ Terraformer imports: users, groups, apps, policies, etc.
- ❌ Terraformer cannot import: OIG reviews, catalogs, workflows, etc.
- ✅ Solution: Use our Python import scripts for OIG resources

See [Terraformer + OIG FAQ](./docs/TERRAFORMER_OIG_FAQ.md) for full details.

## 🏗️ Environment-Based Architecture

This repository uses an **environment-based structure** where each directory represents **one Okta organization**.

**🔒 Critical Rule: One Directory = One Okta Org**

```
environments/
├── production/         # Your production Okta tenant (template)
├── staging/            # Your staging Okta tenant (template)
└── development/        # Your development Okta tenant (template)
```

**To add your first environment:**
```bash
# Example: Create your company environment
mkdir -p environments/mycompany/{terraform,imports,config}

# Copy template files
cp environments/production/terraform/* environments/mycompany/terraform/
cp environments/production/config/* environments/mycompany/config/

# See TEMPLATE_SETUP.md for complete setup instructions
```

**Benefits:**
- ✅ Complete environment isolation - no cross-org pollution
- ✅ Each environment uses its own GitHub Environment secrets
- ✅ Independent Terraform state per organization
- ✅ Easy to add or remove tenants
- ✅ Clear separation of concerns

**[→ See Environments README](./environments/README.md)** for complete guide including:
- Environment isolation rules (CRITICAL)
- Directory structure and organization
- Import workflows for each environment
- Terraform usage examples
- Best practices for multi-tenant management

**📋 Want to use OIG features?** See **[OIG_PREREQUISITES.md](./OIG_PREREQUISITES.md)** for required setup steps (Entitlement Management must be enabled manually in GUI).

## 🎯 Okta Identity Governance Features

The Okta Terraform Provider (v6.4.0+ required) includes comprehensive support for Okta Identity Governance:

### Terraform Provider Resources

- **`okta_reviews`** - Access review campaigns for periodic certification
- **`okta_principal_entitlements`** - Define what principals have access to
- **`okta_request_conditions`** - Conditions for access requests
- **`okta_request_sequences`** - Approval workflows with multiple stages
- **`okta_request_settings`** - Global access request configuration
- **`okta_catalog_entry_default`** - Configure app catalog entries
- **`okta_catalog_entry_user_access_request_fields`** - Custom request fields
- **`okta_entitlement_bundle`** - Group entitlements into bundles

### Python API Management

These features require Python scripts (not yet in Terraform provider):

- **Resource Owners** - Assign owners to apps, groups, and bundles
- **Governance Labels** - Categorize resources for governance
- **Admin Labeling** - Automatically label admin entitlements
- **Bulk Operations** - Manage resources at scale with rate limiting

## 🏗️ GitOps Workflow

This template implements a complete GitOps workflow:

### For Terraform Resources
```
Feature Branch → Pull Request → Terraform Plan →
Code Review → Merge → Manual Apply Trigger →
Approval Gate → Terraform Apply → Okta Updated
```

### For Labels and Owners (Python API)
```
Feature Branch → Pull Request → Syntax Validation →
Code Review → Merge → Auto Dry-Run →
Review Changes → Manual Apply → Okta Updated
```

**Key Features:**
- ✅ All changes go through pull requests
- ✅ Automated validation and planning
- ✅ Peer review before deployment
- ✅ Manual approval gates for production
- ✅ Complete audit trail in Git
- ✅ Drift detection via scheduled imports

See **[docs/GITOPS_WORKFLOW.md](./docs/GITOPS_WORKFLOW.md)** for detailed workflow documentation.

## 📦 Repository Components

### GitHub Actions Workflows

**Import and Sync:**
- `import-all-resources.yml` - Import all OIG resources from Okta
- `sync-labels.yml` - Sync governance labels from Okta
- `export-oig.yml` - Export OIG configurations to JSON

**Terraform Operations:**
- `terraform-plan.yml` - Run plan on PRs (with AWS OIDC)
- `terraform-apply-with-approval.yml` - Apply with manual approval

**API Management:**
- `apply-owners.yml` - Apply resource owner assignments
- `apply-labels.yml` - Deploy governance labels
- `apply-admin-labels.yml` - Auto-label admin entitlements

**Validation:**
- `validate-pr.yml` - YAML syntax, security scanning
- `validate-label-mappings.yml` - Label configuration validation

### Python Scripts

Located in `scripts/`:

**Import and Sync:**
- `import_oig_resources.py` - Import OIG resources from Okta API
- `sync_owner_mappings.py` - Sync resource owners from Okta
- `sync_label_mappings.py` - Sync governance labels from Okta

**Apply:**
- `apply_resource_owners.py` - Apply owners to resources
- `apply_admin_labels.py` - Auto-label admin entitlements
- `apply_labels_from_config.py` - Deploy labels from config file

### AWS Backend Infrastructure

Located in `aws-backend/`:

- S3 bucket for Terraform state
- DynamoDB table for state locking
- IAM roles for GitHub Actions OIDC
- Complete setup guide

**Benefits:**
- ✅ Team collaboration without state conflicts
- ✅ State history and versioning for rollback
- ✅ Encryption at rest and in transit
- ✅ No long-lived AWS credentials in GitHub

See **[docs/AWS_BACKEND_SETUP.md](./docs/AWS_BACKEND_SETUP.md)** for setup instructions.

### AI-Assisted Code Generation

Located in `ai-assisted/`:

Quickly generate Terraform code for demos using AI:

**Tier 1: Manual** - Copy context and prompts to your AI assistant
**Tier 2: Automated** - CLI tool with Gemini/GPT/Claude integration

```bash
# Example: Generate demo environment
cd ai-assisted
python generate.py --prompt "Create 5 marketing users and Salesforce app" \
  --provider gemini --output ../environments/mycompany/terraform/demo.tf
```

See **[ai-assisted/README.md](./ai-assisted/README.md)** for complete guide.

## 📋 Prerequisites

### Required Software
- **Terraform** >= 1.9.0
- **Python** >= 3.9
- **Git** (for version control)
- **GitHub CLI** (optional, for workflow management)

### Required Services
- **Okta Organization** with Identity Governance enabled
- **GitHub Account** with Actions enabled
- **AWS Account** (for S3/DynamoDB state backend - optional but recommended)

### Okta API Permissions

Your API token needs these scopes:
- `okta.groups.manage`
- `okta.users.manage`
- `okta.apps.manage`
- `okta.governance.accessRequests.manage`
- `okta.governance.accessReviews.manage`
- `okta.governance.catalogs.manage`

## 🔧 Initial Setup

### 1. Use This Template

Click the "Use this template" button at the top of this page, or:

```bash
gh repo create my-okta-gitops --template joevanhorn/okta-terraform-demo-template
cd my-okta-gitops
```

### 2. Set Up AWS Backend (Recommended)

```bash
cd aws-backend
terraform init
terraform apply

# Save the output - you'll need it for GitHub secrets
terraform output github_actions_role_arn
```

### 3. Configure GitHub Environment

Go to **Settings → Environments** and create your first environment:

**Environment Name:** `MyCompany` (matches your directory name)

**Required Secrets:**
- `OKTA_API_TOKEN` - Okta API token with governance scopes
- `OKTA_ORG_NAME` - Your Okta org name (e.g., `dev-12345678`)
- `OKTA_BASE_URL` - Base URL (e.g., `okta.com` or `oktapreview.com`)

**Repository Secret (for AWS):**
- `AWS_ROLE_ARN` - From terraform output above

### 4. Create Your First Environment

```bash
# Create directory structure
mkdir -p environments/mycompany/{terraform,imports,config}

# Copy template files
cp environments/production/terraform/provider.tf environments/mycompany/terraform/
cp environments/production/terraform/variables.tf environments/mycompany/terraform/
cp environments/production/config/*.json environments/mycompany/config/

# Update provider.tf with your backend key
# Change: key = "Okta-GitOps/production/terraform.tfstate"
# To:     key = "Okta-GitOps/mycompany/terraform.tfstate"
```

### 5. Import Resources from Okta

```bash
# Import all OIG resources from your Okta tenant
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyCompany \
  -f update_terraform=true \
  -f commit_changes=true
```

### 6. Initialize and Apply

```bash
cd environments/mycompany/terraform
terraform init
terraform plan
terraform apply
```

**🎉 You're now managing Okta with GitOps!**

For detailed setup instructions, see **[TEMPLATE_SETUP.md](./TEMPLATE_SETUP.md)**.

---

## 🔄 Keeping Your Repository Updated

This template receives regular updates including new features, bug fixes, improved workflows, and enhanced documentation.

### Automatic Updates (Recommended)

**Use the built-in sync workflow:**

1. **Enable the workflow:**
   - Go to **Actions** tab in your repository
   - Find "Sync Template Updates" workflow
   - Click "Enable workflow" if needed

2. **Run manually anytime:**
   ```bash
   gh workflow run sync-template.yml
   ```
   Or click "Run workflow" in the Actions tab

3. **Review the PR:**
   - Workflow creates a PR with template updates
   - Review changes in the PR
   - Merge when ready

**The workflow runs automatically:**
- 🕐 Weekly on Sundays at 2 AM UTC
- 🔘 Manually via workflow dispatch
- 📦 Creates PR with all template updates
- 🔍 Shows exactly what changed

### Manual Sync (Alternative)

If you prefer manual control:

```bash
# One-time setup: Add template as remote
git remote add template https://github.com/joevanhorn/okta-terraform-demo-template.git

# Sync updates anytime:
git fetch template
git checkout -b sync-template-updates
git merge template/main --allow-unrelated-histories
git push origin sync-template-updates

# Create PR via GitHub web UI or:
gh pr create --title "Sync template updates" --body "Updates from template repository"
```

### Stay Notified

**Watch this repository for updates:**
1. Click "Watch" button (top right)
2. Select "Custom"
3. Enable "Releases"
4. Click "Apply"

You'll be notified when new features are released!

### Recent Updates

**v2.0.0 (2025-11-12):**
- ✨ Added Gemini Gem support (Tier 3 AI-assisted generation)
- 📝 GitHub web UI integration guide
- 🔄 Automatic template sync workflow

See [CHANGELOG.md](./CHANGELOG.md) for full history.

---

## 📚 Documentation

Comprehensive guides are available in the `docs/` directory:

### Getting Started
- **[TEMPLATE_SETUP.md](./TEMPLATE_SETUP.md)** - Complete setup guide for new users
- **[OIG_PREREQUISITES.md](./OIG_PREREQUISITES.md)** - Required Okta configuration
- **[DIRECTORY_GUIDE.md](./DIRECTORY_GUIDE.md)** - Repository structure explained

### Workflows and Operations
- **[docs/GITOPS_WORKFLOW.md](./docs/GITOPS_WORKFLOW.md)** - GitOps patterns and best practices
- **[docs/WORKFLOWS.md](./docs/WORKFLOWS.md)** - GitHub Actions workflow reference
- **[docs/API_MANAGEMENT.md](./docs/API_MANAGEMENT.md)** - Python scripts guide (1190+ lines)
- **[docs/AWS_BACKEND_SETUP.md](./docs/AWS_BACKEND_SETUP.md)** - S3 state backend setup

### Troubleshooting and Reference
- **[docs/LESSONS_LEARNED.md](./docs/LESSONS_LEARNED.md)** - Common issues and solutions
- **[docs/TERRAFORMER_OIG_FAQ.md](./docs/TERRAFORMER_OIG_FAQ.md)** - Terraformer limitations
- **[docs/TROUBLESHOOTING_ENTITLEMENT_BUNDLES.md](./docs/TROUBLESHOOTING_ENTITLEMENT_BUNDLES.md)** - Bundle-specific issues

### AI-Assisted Development
- **[ai-assisted/README.md](./ai-assisted/README.md)** - AI code generation guide
- **[testing/DEMO_BUILD_GUIDE.md](./testing/DEMO_BUILD_GUIDE.md)** - Creating demo environments

## 🤝 Common Tasks

### Import Resources from Okta
```bash
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyCompany \
  -f update_terraform=true
```

### Plan Terraform Changes
```bash
cd environments/mycompany/terraform
terraform plan
```

### Apply Changes with Approval
```bash
# Trigger manual apply workflow (requires approval)
gh workflow run terraform-apply-with-approval.yml \
  -f environment=mycompany
```

### Manage Resource Owners
```bash
# Sync from Okta
python3 scripts/sync_owner_mappings.py \
  --output environments/mycompany/config/owner_mappings.json

# Apply to Okta
gh workflow run apply-owners.yml \
  -f environment=mycompany \
  -f dry_run=false
```

### Manage Governance Labels
```bash
# Sync from Okta
python3 scripts/sync_label_mappings.py \
  --output environments/mycompany/config/label_mappings.json

# Apply to Okta
gh workflow run apply-labels-from-config.yml \
  -f environment=mycompany \
  -f dry_run=false
```

### Auto-Label Admin Entitlements
```bash
gh workflow run apply-admin-labels.yml \
  -f environment=mycompany \
  -f dry_run=false
```

## 🔍 Working Example

Want to see this template in action with a real, configured environment?

👉 **[okta-terraform-complete-demo](https://github.com/joevanhorn/okta-terraform-complete-demo)**

This working repository demonstrates:
- Fully configured LowerDeckLabs demo environment
- 31 entitlement bundles
- 200 access review campaigns
- Complete governance label setup
- Resource owner assignments
- Real-world workflow examples

## 🧩 Architecture Patterns

### Three-Layer Resource Management

Understanding what goes where is critical:

**Layer 1: Terraform Provider (Full CRUD)**
- Standard Okta resources: users, groups, apps, policies
- OIG resources: entitlement bundles, access reviews, approval sequences
- Managed in `environments/{env}/terraform/*.tf` files

**Layer 2: Python API Scripts (Read/Write)**
- Resource Owners (not in Terraform provider yet)
- Governance Labels (not in Terraform provider yet)
- Managed in `environments/{env}/config/*.json` files

**Layer 3: Manual Management (Okta Admin UI)**
- Entitlement assignments (which users/groups have bundles)
- Access review decisions and approvals
- Certain advanced OIG configurations

### State Management

Each environment maintains independent state:

```
s3://your-bucket/
└── Okta-GitOps/
    ├── mycompany/terraform.tfstate
    ├── production/terraform.tfstate
    ├── staging/terraform.tfstate
    └── development/terraform.tfstate
```

**Key Features:**
- State locking via DynamoDB
- AES256 encryption at rest
- Versioning enabled for rollback
- GitHub Actions authentication via AWS OIDC (no long-lived credentials)

## 🛡️ Security Best Practices

### Secrets Management
- ✅ Use GitHub Environments for Okta credentials
- ✅ Use AWS OIDC for state backend (no long-lived AWS keys)
- ✅ Rotate API tokens regularly (every 90 days)
- ✅ Use least-privilege scopes
- ✅ Never commit secrets to Git

### Change Management
- ✅ All changes via pull requests
- ✅ Required approvals for production
- ✅ Automated validation on PRs
- ✅ Manual approval gates for applies
- ✅ Complete audit trail in Git

### State Protection
- ✅ State stored in encrypted S3
- ✅ DynamoDB locking prevents conflicts
- ✅ State versioning for rollback
- ✅ Never commit state files to Git

## 📊 Project Status

This template is actively maintained and used in production environments.

### Current Capabilities
- ✅ Full OIG resource management via Terraform
- ✅ Resource owners and labels via Python API
- ✅ Multi-tenant environment support
- ✅ GitHub Actions automation
- ✅ AWS S3/DynamoDB state backend
- ✅ AI-assisted code generation
- ✅ Comprehensive documentation
- ✅ Working examples and demos

### Known Limitations
- ⚠️ Terraformer doesn't support OIG resources (use Python import scripts)
- ⚠️ Principal assignments must be managed in Okta UI
- ⚠️ Some OIG features still in development (check provider docs)

## 🤝 Contributing

Found a bug or have a suggestion? Please:

1. Check [existing issues](https://github.com/joevanhorn/okta-terraform-demo-template/issues)
2. Create a new issue with details
3. Or submit a pull request!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [Okta Terraform Provider](https://registry.terraform.io/providers/okta/okta/latest/docs)
- [Terraform](https://www.terraform.io/)
- [GitHub Actions](https://github.com/features/actions)
- [Python](https://www.python.org/)
- [AWS](https://aws.amazon.com/) (S3, DynamoDB, IAM)

## 📞 Support

- **Documentation:** See `docs/` directory
- **Issues:** [GitHub Issues](https://github.com/joevanhorn/okta-terraform-demo-template/issues)
- **Discussions:** [GitHub Discussions](https://github.com/joevanhorn/okta-terraform-demo-template/discussions)
- **Working Example:** [okta-terraform-complete-demo](https://github.com/joevanhorn/okta-terraform-complete-demo)

---

**Ready to get started?** → [TEMPLATE_SETUP.md](./TEMPLATE_SETUP.md)
