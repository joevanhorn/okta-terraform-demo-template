# GitHub Basic Setup (Version Control)

**Difficulty:** Beginner | **Time:** 20 minutes | **Prerequisites:** Completed [LOCAL-USAGE.md](./LOCAL-USAGE.md)

Store your Terraform code in GitHub for backup, history, and easy sharing.

---

## What You'll Get

- Code safely backed up in GitHub
- Complete change history (who changed what, when)
- Ability to roll back to any previous version
- Easy sharing with team members

**What this guide does NOT cover:**
- Automated testing on pull requests
- Team approval workflows
- CI/CD pipelines
→ For those, see [GITHUB-GITOPS.md](./GITHUB-GITOPS.md)

---

## Prerequisites

- [x] Completed [LOCAL-USAGE.md](./LOCAL-USAGE.md)
- [x] Working Terraform configuration
- [ ] GitHub account
- [ ] Git installed locally

### Install Git (if needed)

```bash
# Check if installed
git --version

# Install if needed
# Mac: brew install git
# Windows: Download from git-scm.com
# Linux: apt install git (or yum install git)
```

---

## Step 1: Initialize Git in Your Project

```bash
cd okta-terraform

# Initialize git repository
git init

# Create .gitignore to protect sensitive files
cat > .gitignore << 'EOF'
# Terraform
*.tfstate
*.tfstate.*
*.tfvars
.terraform/
.terraform.lock.hcl
crash.log

# Secrets - NEVER commit these
*.pem
*.key
*secret*
*token*

# OS files
.DS_Store
Thumbs.db

# Editor files
*.swp
*.swo
*~
.vscode/
.idea/
EOF
```

**Important:** The `.gitignore` prevents you from accidentally committing sensitive files.

---

## Step 2: Secure Your Credentials

Before pushing to GitHub, make sure your API token isn't in any files.

### Option A: Use Environment Variables (Recommended)

Update your `provider.tf` to use variables:

```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    okta = {
      source  = "okta/okta"
      version = "~> 6.4.0"
    }
  }
}

provider "okta" {
  org_name  = var.okta_org_name
  base_url  = var.okta_base_url
  api_token = var.okta_api_token
}

variable "okta_org_name" {
  type        = string
  description = "Okta organization name"
}

variable "okta_base_url" {
  type        = string
  default     = "okta.com"
}

variable "okta_api_token" {
  type        = string
  sensitive   = true
}
```

Create a local variables file (won't be committed):

```bash
cat > terraform.tfvars << 'EOF'
okta_org_name  = "your-org-name"
okta_base_url  = "okta.com"
okta_api_token = "your-api-token"
EOF
```

### Option B: Use Environment Variables Only

Set these in your shell:

```bash
export TF_VAR_okta_org_name="your-org-name"
export TF_VAR_okta_base_url="okta.com"
export TF_VAR_okta_api_token="your-token"
```

Add to your `~/.bashrc` or `~/.zshrc` to persist.

---

## Step 3: Create GitHub Repository

### Option A: Using GitHub Web UI

1. Go to [github.com/new](https://github.com/new)
2. Fill in:
   - **Repository name:** `okta-terraform`
   - **Description:** `Okta configuration managed with Terraform`
   - **Visibility:** **Private** (recommended)
3. **Don't** check "Add README" (you already have files)
4. Click **Create repository**

### Option B: Using GitHub CLI

```bash
# Install gh if needed: brew install gh
gh auth login
gh repo create okta-terraform --private --source=. --remote=origin
```

---

## Step 4: Push Your Code

```bash
# Stage all files
git add .

# Commit
git commit -m "Initial Okta Terraform configuration"

# Add GitHub as remote (if not done by gh)
git remote add origin https://github.com/YOUR-USERNAME/okta-terraform.git

# Push to GitHub
git push -u origin main
```

---

## Step 5: Verify on GitHub

1. Go to your repository on GitHub
2. Verify your files are there
3. Confirm **no secrets** are visible (no API tokens, no .tfvars files)

---

## Daily Workflow

### Making Changes

```bash
# 1. Edit your Terraform files
vim main.tf

# 2. Test locally
terraform plan
terraform apply

# 3. Commit and push
git add .
git commit -m "Add new marketing users"
git push
```

### Viewing History

```bash
# See all commits
git log --oneline

# See what changed in a commit
git show abc1234

# See who changed what
git blame main.tf
```

### Rolling Back

```bash
# See history
git log --oneline

# Checkout previous version
git checkout abc1234 -- main.tf

# Or revert entire commit
git revert abc1234
```

---

## Optional: Add Basic Automation

Want GitHub to validate your Terraform when you push? Add this workflow:

Create `.github/workflows/validate.yml`:

```yaml
name: Validate Terraform

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.0"

      - name: Terraform Format
        run: terraform fmt -check

      - name: Terraform Init
        run: terraform init -backend=false

      - name: Terraform Validate
        run: terraform validate
```

This runs automatically and checks:
- Code is properly formatted
- Syntax is valid

**Note:** This doesn't run `terraform plan` (that requires credentials). For that, see [GITHUB-GITOPS.md](./GITHUB-GITOPS.md).

---

## Collaborating with Others

### Adding a Collaborator

1. Go to repository **Settings**
2. Click **Collaborators**
3. Click **Add people**
4. Enter their GitHub username
5. They'll receive an invitation

### They'll Need Credentials

Each collaborator needs their own:
- Okta API token
- Local `terraform.tfvars` or environment variables

**Never share credentials through GitHub!**

---

## Branching for Safety

For larger changes, use branches:

```bash
# Create and switch to new branch
git checkout -b add-salesforce-app

# Make changes, test locally
terraform plan
terraform apply

# Commit
git add .
git commit -m "Add Salesforce app"

# Push branch
git push -u origin add-salesforce-app

# Merge to main when ready
git checkout main
git merge add-salesforce-app
git push
```

---

## Troubleshooting

### "fatal: not a git repository"
Run `git init` in your project directory.

### "error: failed to push"
```bash
# Pull latest changes first
git pull origin main
# Then push again
git push
```

### "Your branch is behind"
```bash
git pull origin main
```

### Accidentally Committed Secrets

**Immediately:**
1. Revoke the exposed API token in Okta
2. Create a new token
3. Remove from Git history:
   ```bash
   # Remove file from history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch terraform.tfvars" \
     --prune-empty --tag-name-filter cat -- --all

   # Force push
   git push origin --force --all
   ```

---

## Next Steps

### Continue Local Development
Keep using `terraform plan` and `terraform apply` locally, pushing changes to GitHub for backup.

### Ready for Team Workflows?
Need automated terraform plan on PRs? Approval gates? Team collaboration?
→ See [GITHUB-GITOPS.md](./GITHUB-GITOPS.md)

### Learn More Terraform
→ See [TERRAFORM-BASICS.md](./TERRAFORM-BASICS.md)

---

## Summary

You now have:
- Code safely stored in GitHub
- Change history for auditing
- Ability to roll back mistakes
- Easy collaboration with others

**Your workflow:**
1. Edit Terraform files
2. Run `terraform plan` and `terraform apply` locally
3. Commit and push to GitHub

This gives you 80% of the benefit with 20% of the complexity. When you're ready for full CI/CD automation, see [GITHUB-GITOPS.md](./GITHUB-GITOPS.md).
