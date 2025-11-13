# Template Setup Guide

Welcome! This guide will walk you through setting up this template for your organization.

**Estimated time:** 30-45 minutes for first environment

> **💡 Secrets Reference:** See **[SECRETS_SETUP.md](./SECRETS_SETUP.md)** for a complete guide to all required GitHub secrets and how to configure them.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Create Your Repository](#step-1-create-your-repository)
3. [Step 2: Set Up AWS Backend (Optional but Recommended)](#step-2-set-up-aws-backend-optional-but-recommended)
4. [Step 3: Configure GitHub Environment](#step-3-configure-github-environment)
5. [Step 4: Create Your First Okta Environment](#step-4-create-your-first-okta-environment)
6. [Step 5: Import Resources from Okta](#step-5-import-resources-from-okta)
7. [Step 6: Verify and Apply](#step-6-verify-and-apply)
8. [Step 7: Set Up Governance Features (Optional)](#step-7-set-up-governance-features-optional)
9. [Next Steps](#next-steps)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

### Required Software (Local Machine)

- [ ] **Git** - For version control
  ```bash
  git --version  # Should be 2.0+
  ```

- [ ] **Terraform** >= 1.9.0
  ```bash
  terraform --version  # Should be 1.9.0+
  ```

- [ ] **Python** >= 3.9
  ```bash
  python3 --version  # Should be 3.9+
  ```

- [ ] **GitHub CLI** (optional but helpful)
  ```bash
  gh --version
  ```

### Required Services

- [ ] **GitHub Account** with Actions enabled
- [ ] **Okta Organization** - One of:
  - Developer account (free) from https://developer.okta.com/signup/
  - Preview organization
  - Production organization
- [ ] **Okta Identity Governance** enabled (for OIG features)
  - See [OIG_PREREQUISITES.md](./OIG_PREREQUISITES.md)
- [ ] **AWS Account** (optional but recommended for team collaboration)

### Required Okta Configuration

- [ ] **API Token** created with these scopes:
  - `okta.groups.manage`
  - `okta.users.manage`
  - `okta.apps.manage`
  - `okta.governance.accessRequests.manage`
  - `okta.governance.accessReviews.manage`
  - `okta.governance.catalogs.manage`

**How to create an Okta API token:**
1. Log into your Okta Admin Console
2. Go to **Security → API → Tokens**
3. Click **Create Token**
4. Name it `Terraform GitOps` (or similar)
5. **Save the token immediately** - you won't see it again!

---

## Step 1: Create Your Repository

### Option A: Using GitHub Web UI

1. Navigate to https://github.com/joevanhorn/okta-terraform-demo-template
2. Click **"Use this template"** button (top right, green button)
3. Fill in:
   - **Owner:** Your GitHub username or organization
   - **Repository name:** `okta-gitops` (or your preferred name)
   - **Visibility:** Private (recommended for production)
4. Click **"Create repository from template"**
5. Clone your new repository:
   ```bash
   git clone https://github.com/YOUR-USERNAME/okta-gitops.git
   cd okta-gitops
   ```

### Option B: Using GitHub CLI

```bash
# Create repository from template
gh repo create my-okta-gitops --template joevanhorn/okta-terraform-demo-template --private

# Clone it
cd my-okta-gitops
```

---

## Step 2: Set Up AWS Backend (Optional but Recommended)

**Why AWS backend?**
- ✅ Team collaboration without state conflicts
- ✅ State locking prevents concurrent modifications
- ✅ State history and versioning for rollback
- ✅ Secure encryption at rest
- ✅ No long-lived AWS credentials in GitHub (uses OIDC)

**Skip this step if:**
- You're working alone and don't need shared state
- You want to use a different backend (Terraform Cloud, Azure, etc.)

### 2.1 Configure AWS Credentials

```bash
# Ensure AWS CLI is configured
aws sts get-caller-identity

# Should show your AWS account details
```

### 2.2 Deploy Backend Infrastructure

```bash
cd aws-backend
terraform init
terraform plan
terraform apply
```

**What this creates:**
- S3 bucket: `okta-terraform-demo` (or your custom name)
- DynamoDB table: `okta-terraform-state-lock`
- IAM role for GitHub Actions OIDC authentication
- Encryption, versioning, and lifecycle policies

### 2.3 Save Outputs

```bash
# Save these values - you'll need them
terraform output github_actions_role_arn
# Example: arn:aws:iam::123456789012:role/GitHubActions-OktaTerraform

terraform output state_bucket_name
# Example: okta-terraform-demo
```

### 2.4 Add AWS Secret to GitHub

1. Go to your repository on GitHub
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **"New repository secret"**
4. Create secret:
   - **Name:** `AWS_ROLE_ARN`
   - **Value:** (paste the role ARN from terraform output)
5. Click **"Add secret"**

**Security Note:** This uses OpenID Connect (OIDC) - no long-lived AWS access keys are stored in GitHub!

---

## Step 3: Configure GitHub Repository

### Option A: Automated Setup (Recommended)

Run the setup script to configure repository settings automatically:

```bash
./scripts/setup-repository.sh
```

This script configures:
- ✅ GitHub Actions workflow permissions (read/write + PR creation)
- ✅ Repository labels (template-sync, maintenance)

**Requirements:** [GitHub CLI](https://cli.github.com/) authenticated with admin access.

### Option B: Manual Setup

If you prefer manual configuration or don't have GitHub CLI:

#### 3.1 Create GitHub Environment

GitHub Environments provide:
- Secret management per Okta tenant
- Approval gates for production deployments
- Environment-specific protection rules

1. Go to your repository on GitHub
2. Navigate to **Settings → Environments**
3. Click **"New environment"**
4. Enter environment name: `MyCompany` (or your organization name)
   - **IMPORTANT:** This name should match the directory you'll create in `environments/`
   - Case-insensitive but should be consistent (e.g., `MyCompany` → `environments/mycompany/`)
5. Click **"Configure environment"**

#### 3.2 Add Environment Secrets

Add these three secrets:

**Secret 1: OKTA_API_TOKEN**
- Click **"Add secret"**
- **Name:** `OKTA_API_TOKEN`
- **Value:** Your Okta API token (from Prerequisites)
- Click **"Add secret"**

**Secret 2: OKTA_ORG_NAME**
- Click **"Add secret"**
- **Name:** `OKTA_ORG_NAME`
- **Value:** Your Okta org name
  - Example: `dev-12345678` (from `dev-12345678.okta.com`)
  - Or: `mycompany` (from `mycompany.oktapreview.com`)
- Click **"Add secret"**

**Secret 3: OKTA_BASE_URL**
- Click **"Add secret"**
- **Name:** `OKTA_BASE_URL`
- **Value:** Your Okta base URL
  - `okta.com` for production orgs
  - `oktapreview.com` for preview orgs
  - `okta-emea.com` for EMEA orgs
- Click **"Add secret"**

#### 3.3 Configure Protection Rules (Optional)

For **production** environments, configure these protection rules:

1. Scroll to **"Deployment protection rules"**
2. Enable **"Required reviewers"**
   - Add team members who must approve deployments
   - Recommended: 2+ reviewers for production
3. Enable **"Wait timer"** (optional)
   - Set to 5-10 minutes for production changes
   - Allows time to catch mistakes before apply
4. Click **"Save protection rules"**

For **development/staging**, lighter protection is acceptable:
- 0-1 reviewers
- No wait timer
- Self-approval allowed

#### 3.4 Create Repository Labels

The template sync workflow uses labels to mark automated PRs. Create these labels:

**Option 1: Using GitHub CLI**

```bash
# Create template-sync label
gh label create template-sync \
  --description "Automated template sync pull request" \
  --color "0366d6"

# Create maintenance label
gh label create maintenance \
  --description "Repository maintenance" \
  --color "fbca04"
```

**Option 2: Using GitHub Web UI**

1. Go to your repository on GitHub
2. Navigate to **Issues** or **Pull Requests** tab
3. Click **"Labels"** (in the sub-navigation)
4. Click **"New label"**

**Create label 1:**
- Name: `template-sync`
- Description: `Automated template sync pull request`
- Color: `#0366d6` (blue)
- Click **"Create label"**

**Create label 2:**
- Name: `maintenance`
- Description: `Repository maintenance`
- Color: `#fbca04` (yellow)
- Click **"Create label"**

**Why these labels?**
- The sync-template workflow automatically applies these labels to PRs
- Makes it easy to identify automated template updates
- Helps filter PRs in the Pull Requests tab

#### 3.5 Enable Workflow Permissions for PR Creation

The sync-template workflow needs permission to create pull requests. Enable this setting:

**Option 1: Using GitHub Web UI (Recommended)**

1. Go to your repository on GitHub
2. Navigate to **Settings → Actions → General**
3. Scroll down to **"Workflow permissions"**
4. Select: **"Read and write permissions"**
5. Check the box: **"Allow GitHub Actions to create and approve pull requests"**
6. Click **"Save"**

**Option 2: Using GitHub CLI**

```bash
# Enable workflow PR creation (requires admin access)
gh api repos/OWNER/REPO/actions/permissions \
  --method PUT \
  -f default_workflow_permissions=write \
  -f can_approve_pull_request_reviews=true
```

Replace `OWNER/REPO` with your repository (e.g., `myorg/okta-terraform-demo`).

**Why this is needed:**
- The sync-template workflow automatically creates PRs with template updates
- Without this permission, the workflow will fail with: "GitHub Actions is not permitted to create or approve pull requests"
- This is a GitHub security setting that defaults to read-only for Actions

**Security note:**
- This only affects workflows in your repository
- Workflows still require explicit triggers (schedule or manual dispatch)
- PRs created by Actions are clearly marked as automated

---

## Step 4: Create Your First Okta Environment

Now create a directory for your Okta organization.

### 4.1 Create Directory Structure

```bash
# Navigate to environments directory
cd environments

# Create your environment directory
# Use the same name as your GitHub Environment (case-insensitive)
mkdir -p mycompany/{terraform,imports,config}

# Verify structure
tree mycompany
# Should show:
# mycompany/
# ├── terraform/
# ├── imports/
# └── config/
```

### 4.2 Copy Template Files

```bash
# Copy Terraform provider configuration
cp production/terraform/provider.tf mycompany/terraform/
cp production/terraform/variables.tf mycompany/terraform/

# Copy empty config templates
cp production/config/owner_mappings.json mycompany/config/
cp production/config/label_mappings.json mycompany/config/

# Copy imports documentation
cp production/imports/README.md mycompany/imports/
```

### 4.3 Update provider.tf

Edit `mycompany/terraform/provider.tf` and update the backend configuration:

```hcl
terraform {
  backend "s3" {
    bucket         = "okta-terraform-demo"  # Your bucket from Step 2
    key            = "Okta-GitOps/mycompany/terraform.tfstate"  # ← Change this!
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }

  required_version = ">= 1.9.0"

  required_providers {
    okta = {
      source  = "okta/okta"
      version = ">= 6.4.0, < 7.0.0"
    }
  }
}

provider "okta" {
  org_name  = var.okta_org_name
  base_url  = var.okta_base_url
  api_token = var.okta_api_token
}
```

**Key change:** Update `key` to use your environment name: `Okta-GitOps/mycompany/terraform.tfstate`

### 4.4 Create Environment README

Create `mycompany/README.md`:

```markdown
# MyCompany Okta Environment

**Tenant:** mycompany.okta.com (or your actual URL)
**GitHub Environment:** MyCompany
**Purpose:** [Production / Staging / Development]

## Quick Commands

### Import from Okta
\`\`\`bash
gh workflow run import-all-resources.yml \\
  -f tenant_environment=MyCompany \\
  -f update_terraform=true
\`\`\`

### Apply Terraform
\`\`\`bash
cd environments/mycompany/terraform
terraform plan
terraform apply
\`\`\`

### Manage Resource Owners
\`\`\`bash
gh workflow run apply-owners.yml \\
  -f environment=mycompany \\
  -f dry_run=false
\`\`\`
```

---

## Step 5: Import Resources from Okta

Now import your existing Okta configuration into Terraform.

### 5.1 Run Import Workflow

```bash
# From repository root
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyCompany \
  -f update_terraform=true \
  -f commit_changes=false
```

**Parameters:**
- `tenant_environment`: Your GitHub Environment name (matches Step 3.1)
- `update_terraform`: `true` generates Terraform files
- `commit_changes`: `false` for manual review (recommended first time)

### 5.2 Monitor Workflow

```bash
# Watch workflow progress
gh run watch

# Or view in GitHub web UI:
# Actions → Import All OIG Resources → latest run
```

**What gets imported:**
- ✅ Entitlement bundles → `terraform/oig_entitlements.tf`
- ✅ Access reviews → `terraform/oig_reviews.tf`
- ✅ Resource owners → `config/owner_mappings.json`
- ✅ Governance labels → `config/label_mappings.json`

### 5.3 Download Artifacts

The workflow creates artifacts with imported files:

1. Go to **Actions → Import All OIG Resources → latest run**
2. Scroll to **Artifacts** section
3. Download **terraform-files** artifact
4. Extract and copy to `environments/mycompany/terraform/`

Alternatively, if you set `commit_changes=true`, the files are automatically committed.

### 5.4 Review Imported Files

```bash
cd environments/mycompany

# Check what was imported
ls -la terraform/
# Should see: oig_entitlements.tf, oig_reviews.tf, provider.tf, variables.tf

ls -la config/
# Should see: owner_mappings.json, label_mappings.json

ls -la imports/
# Should see: entitlements.json, reviews.json (raw API data)
```

---

## Step 6: Verify and Apply

### 6.1 Initialize Terraform

```bash
cd environments/mycompany/terraform

# Initialize Terraform (connects to S3 backend)
terraform init
```

**Expected output:**
```
Initializing the backend...

Successfully configured the backend "s3"!

Terraform has been successfully initialized!
```

### 6.2 (Optional) Use Starter Templates for New Organizations

**Skip this if you imported existing resources. This section is for brand new Okta orgs.**

If you're starting with a brand new Okta organization, we provide ready-to-use templates:

#### Option A: Quick Demo (Recommended for Testing)

Deploy a working demo in 2 minutes with users, groups, and an OAuth app:

```bash
# Copy quickstart template
cp QUICKSTART_DEMO.tf.example demo.tf

# Edit file and uncomment ALL code
vim demo.tf
# Search and replace @example.com with your actual domain

# Deploy
terraform plan   # Review what will be created
terraform apply  # Create resources

# View outputs
terraform output demo_users
terraform output demo_app
```

**Creates:**
- 5 demo users (employees, manager, contractor)
- 3 groups (Engineering, Marketing, Admins)
- 1 OAuth application with group assignments

#### Option B: Browse Examples for Specific Resources

Find examples for any resource type you need:

```bash
# Browse comprehensive reference
less RESOURCE_EXAMPLES.tf

# Examples include:
# - Users, Groups, Schemas
# - OAuth, SAML, SWA apps
# - Policies, Rules, Networks
# - OIG resources (Entitlements, Reviews, Sequences)
# - Authorization Servers, Scopes
# - Hooks (Inline & Event)

# Copy examples to your own .tf files
# All examples are commented out - uncomment what you need
```

#### Template Guide

For complete template usage guide:
```bash
cat README.md  # Full guide in terraform directory
```

**📚 See:** [terraform/README.md](./environments/myorg/terraform/README.md) for:
- Explanation of all available templates
- Quick start workflows for different scenarios
- Best practices (file organization, naming, template escaping)
- Testing and troubleshooting guides

### 6.3 Validate Configuration

```bash
# Format Terraform files
terraform fmt

# Validate syntax
terraform validate

# Check for errors
echo $?  # Should output: 0 (success)
```

### 6.3 Review Plan

```bash
# Generate execution plan
terraform plan

# Review the output carefully
# First run should show resources to create/import
```

**Expected on first run:**
- If Okta resources already exist: Terraform will show resources to import
- If starting fresh: Terraform will show resources to create

### 6.4 Apply Configuration

```bash
# Apply changes
terraform apply

# Review the plan again
# Type 'yes' to confirm
```

**IMPORTANT:** This may fail if resources already exist in Okta. If so, you need to import them:

```bash
# Example: Import existing entitlement bundle
terraform import okta_entitlement_bundle.example "bundle-id-here"

# See docs/LESSONS_LEARNED.md for import strategies
```

### 6.5 Verify in Okta

1. Log into Okta Admin Console
2. Navigate to **Identity Governance**
3. Verify:
   - Entitlement bundles exist
   - Access reviews are configured
   - Resource owners are assigned
   - Labels are applied

---

## Step 7: Set Up Governance Features (Optional)

### 7.1 Configure Resource Owners

Resource owners are assigned via Python scripts (not in Terraform provider yet).

**Sync current owners from Okta:**
```bash
python3 scripts/sync_owner_mappings.py \
  --output environments/mycompany/config/owner_mappings.json
```

**Edit owner assignments:**
```bash
# Edit config/owner_mappings.json
vim environments/mycompany/config/owner_mappings.json
```

**Apply to Okta:**
```bash
# Dry-run first (shows changes without applying)
python3 scripts/apply_resource_owners.py \
  --config environments/mycompany/config/owner_mappings.json \
  --dry-run

# Apply for real
gh workflow run apply-owners.yml \
  -f environment=mycompany \
  -f dry_run=false
```

### 7.2 Configure Governance Labels

Labels categorize resources for governance workflows.

**Sync current labels from Okta:**
```bash
python3 scripts/sync_label_mappings.py \
  --output environments/mycompany/config/label_mappings.json
```

**Apply labels to Okta:**
```bash
# Dry-run first
gh workflow run apply-labels-from-config.yml \
  -f environment=mycompany \
  -f dry_run=true

# Review output in workflow logs

# Apply for real
gh workflow run apply-labels-from-config.yml \
  -f environment=mycompany \
  -f dry_run=false
```

### 7.3 Auto-Label Admin Entitlements

Automatically find and label admin entitlements:

```bash
# Find admin entitlements
python3 scripts/find_admin_resources.py

# Label them (dry-run first)
python3 scripts/apply_admin_labels.py --dry-run

# Apply via workflow
gh workflow run apply-admin-labels.yml \
  -f environment=mycompany \
  -f dry_run=false
```

---

## Next Steps

### Set Up GitOps Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/add-marketing-users
   ```

2. **Make changes to Terraform files:**
   ```bash
   vim environments/mycompany/terraform/users.tf
   # Add new users, groups, apps, etc.
   ```

3. **Commit and push:**
   ```bash
   git add .
   git commit -m "feat: Add marketing team users"
   git push -u origin feature/add-marketing-users
   ```

4. **Create pull request:**
   ```bash
   gh pr create --title "Add marketing team users"
   ```

5. **Review automated terraform plan** in PR comments

6. **Get approval and merge**

7. **Manually trigger apply:**
   ```bash
   gh workflow run terraform-apply-with-approval.yml \
     -f environment=mycompany
   ```

### Add Additional Environments

Repeat Steps 3-6 for each Okta organization:

- `environments/myorg/` → GitHub Environment: `Production`
- `environments/myorg/` → GitHub Environment: `Staging`
- `environments/myorg/` → GitHub Environment: `Development`

Each environment is completely isolated with:
- Separate GitHub Environment secrets
- Separate Terraform state file in S3
- Independent configurations

### Set Up Scheduled Imports

Detect drift by importing from Okta regularly:

Edit `.github/workflows/import-all-resources.yml` to add a schedule:

```yaml
on:
  schedule:
    - cron: '0 2 * * 1'  # Every Monday at 2 AM UTC
  workflow_dispatch:
    # ... existing inputs
```

### Enable AI-Assisted Code Generation

Speed up demo creation with AI:

```bash
cd ai-assisted

# Install dependencies
pip install google-generativeai  # or openai, anthropic

# Set API key
export GEMINI_API_KEY="your-key"

# Generate code
python generate.py \
  --prompt "Create 5 sales users and a Salesforce app with admin bundle" \
  --provider gemini \
  --output ../environments/mycompany/terraform/sales-demo.tf \
  --validate
```

See [ai-assisted/README.md](./ai-assisted/README.md) for complete guide.

---

## Troubleshooting

### Common Issues

#### Issue: `terraform init` fails with "access denied" to S3

**Cause:** GitHub Actions role doesn't have S3 permissions, or you're running locally without AWS credentials.

**Solution:**
```bash
# Configure AWS credentials locally
aws configure

# Or use AWS SSO
aws sso login

# Try again
terraform init
```

#### Issue: Workflow fails with "Environment not found"

**Cause:** GitHub Environment name doesn't match `tenant_environment` parameter.

**Solution:**
- Check GitHub Environment name in **Settings → Environments**
- Must match workflow parameter (case-insensitive)
- Example: GitHub Environment `MyCompany` → `-f tenant_environment=MyCompany`

#### Issue: Terraform plan shows resources to create that already exist

**Cause:** Resources exist in Okta but not in Terraform state.

**Solution:**
```bash
# Import existing resources
terraform import okta_entitlement_bundle.example "bundle-id"

# See docs/LESSONS_LEARNED.md for bulk import strategies
```

#### Issue: Python scripts fail with "401 Unauthorized"

**Cause:** Invalid or expired API token, or missing scopes.

**Solution:**
- Verify API token in Okta Admin Console
- Check token scopes include governance permissions
- Generate new token if expired
- Update GitHub Environment secret `OKTA_API_TOKEN`

#### Issue: Labels API returns 405 errors

**Cause:** Using label name instead of label ID in API calls.

**Solution:**
- Always use label ID, not name
- Check `label_mappings.json` for correct IDs
- See `scripts/archive/README.md` for Labels API investigation

#### Issue: Entitlement bundles show "error reading campaign"

**Cause:** Provider bug - stale campaign associations from deleted reviews.

**Solution:**
```bash
# Run fix workflow
gh workflow run fix-bundle-campaign-errors.yml \
  -f environment=mycompany \
  -f dry_run=false \
  -f bundles_to_fix=all
```

See [docs/TROUBLESHOOTING_ENTITLEMENT_BUNDLES.md](./docs/TROUBLESHOOTING_ENTITLEMENT_BUNDLES.md)

### Getting Help

1. **Check documentation:**
   - [docs/LESSONS_LEARNED.md](./docs/LESSONS_LEARNED.md) - Common issues
   - [docs/GITOPS_WORKFLOW.md](./docs/GITOPS_WORKFLOW.md) - Workflow patterns
   - [docs/API_MANAGEMENT.md](./docs/API_MANAGEMENT.md) - Python scripts reference

2. **Search existing issues:**
   - https://github.com/joevanhorn/okta-terraform-demo-template/issues

3. **Create new issue:**
   - Include error messages, logs, and steps to reproduce
   - Use issue templates provided

4. **Community support:**
   - GitHub Discussions for Q&A
   - Share your solutions to help others

---

## Checklist Summary

Use this checklist to track your setup progress:

### Prerequisites
- [ ] Terraform >= 1.9.0 installed
- [ ] Python >= 3.9 installed
- [ ] GitHub CLI installed (optional)
- [ ] Okta API token created
- [ ] OIG enabled in Okta (if using governance features)

### Repository Setup
- [ ] Created repository from template
- [ ] Cloned locally
- [ ] AWS backend infrastructure deployed (optional)
- [ ] `AWS_ROLE_ARN` secret added to GitHub (if using AWS)

### Environment Configuration
- [ ] GitHub Environment created
- [ ] `OKTA_API_TOKEN` secret added
- [ ] `OKTA_ORG_NAME` secret added
- [ ] `OKTA_BASE_URL` secret added
- [ ] Protection rules configured (for production)

### Okta Environment Setup
- [ ] Directory structure created (`environments/mycompany/`)
- [ ] Template files copied
- [ ] `provider.tf` updated with correct backend key
- [ ] Environment README created

### Import and Apply
- [ ] Import workflow executed successfully
- [ ] Terraform initialized (`terraform init`)
- [ ] Configuration validated (`terraform validate`)
- [ ] Plan reviewed (`terraform plan`)
- [ ] Resources applied (`terraform apply`)
- [ ] Verified in Okta Admin Console

### Governance Setup (Optional)
- [ ] Resource owners synced and applied
- [ ] Governance labels synced and applied
- [ ] Admin entitlements auto-labeled

### GitOps Workflow
- [ ] Created feature branch
- [ ] Made test changes
- [ ] Created pull request
- [ ] Reviewed automated plan
- [ ] Merged and applied via workflow

---

## Success!

You've successfully set up Okta GitOps!

**What you can do now:**
- ✅ Manage Okta resources with Infrastructure as Code
- ✅ Use pull requests for all changes
- ✅ Automated validation and planning
- ✅ Team collaboration with shared state
- ✅ Complete audit trail in Git
- ✅ Multi-tenant management

**Next:** Check out [docs/GITOPS_WORKFLOW.md](./docs/GITOPS_WORKFLOW.md) for daily workflow patterns.

**Questions?** See [GitHub Discussions](https://github.com/joevanhorn/okta-terraform-demo-template/discussions) or create an [issue](https://github.com/joevanhorn/okta-terraform-demo-template/issues).

Happy GitOps! 🚀
