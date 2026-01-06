# GitHub GitOps Setup (Team Collaboration)

**Difficulty:** Intermediate | **Time:** 45-60 minutes | **Prerequisites:** Completed [LOCAL-USAGE.md](./LOCAL-USAGE.md) and [GITHUB-BASIC.md](./GITHUB-BASIC.md)

Set up automated Terraform workflows with GitHub Actions for team collaboration.

---

## What You'll Get

- **Automated validation** - Terraform plan runs on every pull request
- **Team collaboration** - Peer review before deployment
- **Approval gates** - Manual approval for production changes
- **Audit trail** - Complete history in Git
- **Shared state** - Team members work without conflicts (with AWS backend)

**Prerequisites:**
- [x] Completed [LOCAL-USAGE.md](./LOCAL-USAGE.md) - understand Terraform basics
- [x] Completed [GITHUB-BASIC.md](./GITHUB-BASIC.md) - code in GitHub
- [ ] Okta API token
- [ ] GitHub account with Actions enabled

---

## Overview

### GitOps Workflow

```
Make Changes → Create PR → Automated Plan → Review → Merge → Manual Apply
```

1. **Developer** creates feature branch and makes changes
2. **GitHub Actions** automatically runs `terraform plan`
3. **Team** reviews plan output in PR comments
4. **Approver** merges to main
5. **Developer** manually triggers apply with approval gate

### What You'll Configure

1. **GitHub Environments** - Secrets per Okta org
2. **GitHub Actions** - Automated workflows
3. **Branch Protection** - Require reviews
4. **AWS Backend** (Optional) - Shared state for teams

---

## Part 1: GitHub Environment Setup (15 minutes)

GitHub Environments isolate secrets per Okta organization.

### 1.1 Create Environment

1. Go to your repository → **Settings** → **Environments**
2. Click **New environment**
3. Name it: `MyOrg` (will match your Okta org)
4. Click **Configure environment**

### 1.2 Add Secrets

In Environment secrets, click **Add secret** for each:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `OKTA_API_TOKEN` | Your API token | `00abc123...` |
| `OKTA_ORG_NAME` | Org from URL | `dev-12345678` |
| `OKTA_BASE_URL` | Base domain | `okta.com` or `oktapreview.com` |

**Important:** Names must be UPPERCASE with underscores.

### 1.3 Configure Protection Rules (Optional)

For production environments:

1. Enable **Required reviewers**
2. Add team members who must approve
3. Set **Wait timer** to 5 minutes (optional)

---

## Part 2: Create Environment Directory (10 minutes)

### 2.1 Create Structure

```bash
mkdir -p environments/myorg/{terraform,imports,config}
```

### 2.2 Create provider.tf

```hcl
# environments/myorg/terraform/provider.tf

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    okta = {
      source  = "okta/okta"
      version = "~> 6.4.0"
    }
  }

  # Optional: S3 backend for team collaboration
  # Uncomment after Part 4 (AWS Backend)
  # backend "s3" {
  #   bucket         = "your-bucket-name"
  #   key            = "Okta-GitOps/myorg/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "okta-terraform-state-lock"
  # }
}

provider "okta" {
  org_name  = var.okta_org_name
  base_url  = var.okta_base_url
  api_token = var.okta_api_token
}

variable "okta_org_name" {
  type = string
}

variable "okta_base_url" {
  type    = string
  default = "okta.com"
}

variable "okta_api_token" {
  type      = string
  sensitive = true
}
```

### 2.3 Commit and Push

```bash
git add environments/myorg/
git commit -m "Add myorg environment"
git push
```

---

## Part 3: GitHub Actions Workflows (15 minutes)

### 3.1 Terraform Plan on PRs

Create `.github/workflows/terraform-plan.yml`:

```yaml
name: Terraform Plan

on:
  pull_request:
    branches: [main]
    paths:
      - 'environments/**/terraform/**'
  push:
    branches: [main]
    paths:
      - 'environments/**/terraform/**'

jobs:
  plan:
    runs-on: ubuntu-latest
    environment: MyOrg  # Must match your environment name

    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.0"

      - name: Terraform Init
        working-directory: environments/myorg/terraform
        run: terraform init

      - name: Terraform Format
        working-directory: environments/myorg/terraform
        run: terraform fmt -check

      - name: Terraform Validate
        working-directory: environments/myorg/terraform
        run: terraform validate

      - name: Terraform Plan
        working-directory: environments/myorg/terraform
        env:
          TF_VAR_okta_org_name: ${{ secrets.OKTA_ORG_NAME }}
          TF_VAR_okta_base_url: ${{ secrets.OKTA_BASE_URL }}
          TF_VAR_okta_api_token: ${{ secrets.OKTA_API_TOKEN }}
        run: terraform plan -no-color
```

### 3.2 Terraform Apply with Approval

Create `.github/workflows/terraform-apply.yml`:

```yaml
name: Terraform Apply

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to apply'
        required: true
        default: 'myorg'

jobs:
  apply:
    runs-on: ubuntu-latest
    environment: MyOrg  # Triggers approval gate

    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.0"

      - name: Terraform Init
        working-directory: environments/${{ github.event.inputs.environment }}/terraform
        run: terraform init

      - name: Terraform Apply
        working-directory: environments/${{ github.event.inputs.environment }}/terraform
        env:
          TF_VAR_okta_org_name: ${{ secrets.OKTA_ORG_NAME }}
          TF_VAR_okta_base_url: ${{ secrets.OKTA_BASE_URL }}
          TF_VAR_okta_api_token: ${{ secrets.OKTA_API_TOKEN }}
        run: terraform apply -auto-approve
```

### 3.3 Commit Workflows

```bash
git add .github/workflows/
git commit -m "Add Terraform workflows"
git push
```

---

## Part 4: AWS Backend (Optional - Team State)

**Skip this if working solo.** AWS backend enables:
- Multiple team members working simultaneously
- State locking prevents conflicts
- State history for rollback

### 4.1 Deploy Backend Infrastructure

```bash
cd aws-backend
terraform init
terraform apply
```

Outputs:
- S3 bucket name
- DynamoDB table name
- IAM role ARN for GitHub Actions

### 4.2 Add AWS Secret

Add repository secret (not environment):
- **Name:** `AWS_ROLE_ARN`
- **Value:** Output from `terraform output github_actions_role_arn`

### 4.3 Update provider.tf

Uncomment the backend block in `provider.tf`:

```hcl
backend "s3" {
  bucket         = "your-bucket-name"
  key            = "Okta-GitOps/myorg/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "okta-terraform-state-lock"
}
```

### 4.4 Update Workflows for AWS

Add AWS authentication to workflows:

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - name: Configure AWS
    uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
      aws-region: us-east-1
```

See [docs/AWS_BACKEND_SETUP.md](./docs/AWS_BACKEND_SETUP.md) for complete guide.

---

## Part 5: Branch Protection (5 minutes)

### Enable Protection

1. Go to **Settings** → **Branches**
2. Click **Add rule**
3. Branch name: `main`
4. Enable:
   - [x] Require pull request reviews
   - [x] Require status checks (select "Terraform Plan")
   - [x] Include administrators

### Result

- Can't push directly to main
- Must create PR
- PR must pass terraform plan
- Requires approval

---

## Using Your GitOps Workflow

### Making Changes

```bash
# 1. Create branch
git checkout -b feature/add-users

# 2. Make changes
vim environments/myorg/terraform/users.tf

# 3. Commit and push
git add .
git commit -m "Add marketing users"
git push -u origin feature/add-users

# 4. Create PR
gh pr create --title "Add marketing users"
```

### Review Process

1. PR triggers terraform plan automatically
2. Review plan output in Actions tab
3. Teammates review and approve
4. Merge to main

### Apply Changes

```bash
# Manual trigger (requires approval if configured)
gh workflow run terraform-apply.yml -f environment=myorg
```

Or use GitHub UI: **Actions** → **Terraform Apply** → **Run workflow**

---

## Multiple Environments

### Add Another Okta Org

1. Create GitHub Environment: `Production`
2. Add secrets for production Okta
3. Create directory: `environments/production/terraform/`
4. Update workflows to handle multiple environments

### Workflow Pattern

```yaml
jobs:
  plan:
    strategy:
      matrix:
        environment: [myorg, production]

    environment: ${{ matrix.environment }}
    # ... rest of job
```

---

## Advanced Features

### Import Resources

```bash
gh workflow run import-all-resources.yml \
  -f tenant_environment=MyOrg \
  -f update_terraform=true \
  -f commit_changes=true
```

### Resource Owners

```bash
gh workflow run oig-owners.yml \
  -f environment=myorg \
  -f dry_run=false
```

### Governance Labels

```bash
gh workflow run labels-apply-from-config.yml \
  -f environment=myorg \
  -f dry_run=false
```

See existing workflows in `.github/workflows/` for more options.

---

## Troubleshooting

### "Environment not found"
Environment names are **case-sensitive**. Check exact name in Settings → Environments.

### "Secret not found"
Secrets must be:
- In **Environment** secrets (not repository)
- **UPPERCASE** with underscores
- Exactly: `OKTA_API_TOKEN`, `OKTA_ORG_NAME`, `OKTA_BASE_URL`

### "Permission denied" creating PRs
1. Settings → Actions → General
2. Enable "Read and write permissions"
3. Enable "Allow Actions to create PRs"

### Workflow not running
Check:
- Workflow file in `.github/workflows/`
- Path filters match your changes
- Branch name matches trigger

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for more issues.

---

## Next Steps

### Explore More Workflows
See `.github/workflows/` for available automation:
- Import workflows
- Label management
- Risk rules

### Advanced Documentation
- [TEMPLATE_SETUP.md](./TEMPLATE_SETUP.md) - Complete setup reference
- [docs/03-WORKFLOWS-GUIDE.md](./docs/03-WORKFLOWS-GUIDE.md) - Workflow patterns
- [docs/AWS_BACKEND_SETUP.md](./docs/AWS_BACKEND_SETUP.md) - S3 backend details

### OIG Features
- [OIG_PREREQUISITES.md](./OIG_PREREQUISITES.md) - Enable Identity Governance
- [docs/API_MANAGEMENT.md](./docs/API_MANAGEMENT.md) - Python automation scripts

---

## Summary

You now have:
- GitHub Environments with Okta secrets
- Automated terraform plan on PRs
- Manual terraform apply with approval
- Branch protection for safety
- (Optional) AWS backend for team state

**Your team workflow:**
1. Create branch and make changes
2. Push and create PR
3. Review automated plan
4. Approve and merge
5. Manually trigger apply

This gives you full CI/CD automation with safety gates. For local-only usage, see [LOCAL-USAGE.md](./LOCAL-USAGE.md).
