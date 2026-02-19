# Backend Setup Wizard

**Question:** Where should Terraform store its state?

**This wizard will help you choose!** Answer a few questions to find the right backend for your needs.

---

## 🤔 Quick Decision Helper

Answer these questions:

### Question 1: Are you working alone or with a team?

**👤 Working alone** → Consider [Terraform Cloud](#path-2-terraform-cloud-easiest) or [Local](#path-3-local-testing-only)

**👥 Working with a team** → Use [AWS S3](#path-1-aws-s3-recommended-for-teams)

### Question 2: Is this for production use?

**✅ Yes, production** → Use [AWS S3](#path-1-aws-s3-recommended-for-teams)

**🧪 No, just testing/learning** → Use [Local](#path-3-local-testing-only)

### Question 3: Do you want to manage infrastructure?

**✅ Yes, I want full control** → Use [AWS S3](#path-1-aws-s3-recommended-for-teams)

**❌ No, I want zero infrastructure** → Use [Terraform Cloud](#path-2-terraform-cloud-easiest)

---

## 📊 Backend Comparison

| Feature | AWS S3 | Terraform Cloud | Local |
|---------|--------|-----------------|-------|
| **Best For** | Teams, production | Individuals, small teams | Testing only |
| **Setup Time** | 30 minutes | 10 minutes | 2 minutes |
| **Monthly Cost** | ~$1 | Free tier available | Free |
| **Team Collaboration** | ✅ Yes | ✅ Yes | ❌ No |
| **State Locking** | ✅ Yes (DynamoDB) | ✅ Yes (built-in) | ❌ No |
| **State History** | ✅ Yes (S3 versioning) | ✅ Yes (built-in) | ❌ No |
| **Encryption** | ✅ Yes (AES256) | ✅ Yes (TLS) | ⚠️ Local only |
| **Infrastructure to Manage** | S3, DynamoDB, IAM | None | None |
| **GitHub Actions Support** | ✅ Yes (OIDC) | ✅ Yes (API token) | ❌ No |
| **Backup/Recovery** | ✅ Automated | ✅ Automated | ❌ Manual |
| **Access Control** | ✅ IAM policies | ✅ Team permissions | ❌ File system |

---

## Decision Matrix

### Choose AWS S3 if:
- ✅ You're working with a team (2+ people)
- ✅ This is for production use
- ✅ You need full control over infrastructure
- ✅ You have AWS account/experience
- ✅ You want state locking to prevent conflicts
- ✅ You need automated backups and versioning
- ✅ You're okay managing S3, DynamoDB, and IAM

**→ [Go to AWS S3 Setup](#path-1-aws-s3-recommended-for-teams)**

### Choose Terraform Cloud if:
- ✅ You're working alone or small team (1-5 people)
- ✅ You want zero infrastructure management
- ✅ You want easiest setup (10 minutes)
- ✅ Free tier is enough for your needs
- ✅ You're okay with SaaS solution
- ✅ You want built-in CI/CD features

**→ [Go to Terraform Cloud Setup](#path-2-terraform-cloud-easiest)**

### Choose Local if:
- ✅ You're just testing/learning
- ✅ You're working alone
- ✅ NOT for production
- ✅ You don't need team collaboration
- ✅ You want quickest setup (2 minutes)
- ⚠️ You understand the limitations

**→ [Go to Local Setup](#path-3-local-testing-only)**

---

## Path 1: AWS S3 (Recommended for Teams)

**Best for:** Production use, teams, full control

### Prerequisites

- AWS account with admin access
- AWS CLI configured locally
- Terraform >= 1.9.0 installed

### Setup Steps

**Step 1: Deploy Backend Infrastructure**

```bash
cd aws-backend
terraform init
terraform apply
```

This creates:
- S3 bucket: `okta-terraform-demo` (versioned, encrypted)
- DynamoDB table: `okta-terraform-state-lock` (for locking)
- IAM role: `GitHubActions-OktaTerraform` (for OIDC)

**Expected time:** 5 minutes

**Step 2: Save Outputs**

```bash
# Get the role ARN (needed for GitHub secret)
terraform output github_actions_role_arn

# Save this value!
# Example: arn:aws:iam::123456789012:role/GitHubActions-OktaTerraform
```

**Step 3: Add GitHub Secret**

```bash
# Via GitHub CLI
gh secret set AWS_ROLE_ARN --body "arn:aws:iam::YOUR-ACCOUNT-ID:role/GitHubActions-OktaTerraform"

# Or via web UI:
# Settings → Secrets and variables → Actions → New repository secret
# Name: AWS_ROLE_ARN
# Value: [paste role ARN from step 2]
```

**Step 4: Configure Provider**

Your `environments/*/terraform/provider.tf` already has S3 backend configured!

Just update the key for each environment:

```hcl
terraform {
  backend "s3" {
    bucket         = "okta-terraform-demo"
    key            = "Okta-GitOps/myenv/terraform.tfstate"  # ← Update this
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }
}
```

**Step 5: Initialize**

```bash
cd environments/myenv/terraform
terraform init
```

**✅ Done!** Your team can now collaborate safely.

### Cost Estimate

- **S3:** ~$0.03/GB/month (typically <$0.10)
- **DynamoDB:** ~$0.25/month (on-demand, low usage)
- **Total:** ~$1/month or less

### Benefits You Get

- ✅ **State locking** - No more "who's running terraform?"
- ✅ **Version history** - Rollback to any previous state
- ✅ **Team collaboration** - Everyone uses same state
- ✅ **Encryption** - State encrypted at rest and in transit
- ✅ **Backup** - S3 versioning provides automatic backups
- ✅ **GitHub Actions** - OIDC means no long-lived AWS keys

### Detailed Guide

See [AWS_BACKEND_SETUP.md](./AWS_BACKEND_SETUP.md) for:
- Detailed setup instructions
- Troubleshooting
- Migration from local state
- Cost optimization
- Security best practices

---

## Path 2: Terraform Cloud (Easiest)

**Best for:** Individuals, small teams, zero infrastructure management

### Prerequisites

- Terraform Cloud account (free: https://app.terraform.io/signup)
- Terraform >= 1.9.0 installed

### Setup Steps

**Step 1: Create Terraform Cloud Account**

1. Go to https://app.terraform.io/signup
2. Sign up (free tier available)
3. Confirm email
4. Create organization (e.g., "my-company")

**Step 2: Create Workspace**

1. Click **New** → **Workspace**
2. Choose **CLI-driven workflow**
3. Name it: `okta-myenv-terraform`
4. Click **Create workspace**

**Step 3: Get API Token**

1. Click your profile (top right)
2. Go to **User Settings** → **Tokens**
3. Click **Create an API token**
4. Name it: `GitHub Actions`
5. Copy token immediately

**Step 4: Add GitHub Secret**

```bash
# Via GitHub CLI
gh secret set TF_CLOUD_TOKEN --body "your-api-token-here"

# Or via web UI:
# Settings → Secrets → New repository secret
# Name: TF_CLOUD_TOKEN
# Value: [paste token from step 3]
```

**Step 5: Configure Provider**

Update `environments/myenv/terraform/provider.tf`:

```hcl
terraform {
  cloud {
    organization = "my-company"  # Your org name from step 1

    workspaces {
      name = "okta-myenv-terraform"  # Your workspace name from step 2
    }
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

**Step 6: Set Workspace Variables**

In Terraform Cloud workspace:

1. Go to **Variables** tab
2. Add environment variables:
   - `TF_VAR_okta_api_token` (sensitive)
   - `TF_VAR_okta_org_name`
   - `TF_VAR_okta_base_url`

**Step 7: Initialize**

```bash
cd environments/myenv/terraform
terraform login  # Authenticate (one-time)
terraform init
```

**✅ Done!** Zero infrastructure to manage.

### Cost

**Free tier includes:**
- Up to 500 resources
- State management
- Remote operations
- Team collaboration (up to 5 users)

**Paid plans** start at $20/user/month if you need more.

### Benefits You Get

- ✅ **Zero infrastructure** - No S3, DynamoDB, or IAM to manage
- ✅ **Built-in CI/CD** - Run plans/applies in cloud
- ✅ **Web UI** - View state, plans, and runs in browser
- ✅ **Policy as Code** - Sentinel policies (paid plans)
- ✅ **Cost estimates** - See infrastructure costs
- ✅ **Team management** - Built-in access control

### Limitations

- ⚠️ SaaS solution (data stored in Terraform Cloud)
- ⚠️ Free tier limits (500 resources, 5 users)
- ⚠️ Internet connectivity required
- ⚠️ Less control over infrastructure

---

## Path 3: Local (Testing Only)

**Best for:** Learning, testing, solo development (NOT production)

### Prerequisites

- Terraform >= 1.9.0 installed
- Git repository cloned locally

### Setup Steps

**Step 1: Remove S3 Backend**

Edit `environments/myenv/terraform/provider.tf`:

```hcl
terraform {
  # Remove or comment out backend block:
  # backend "s3" { ... }

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

**Step 2: Create Environment Variables File**

```bash
cd environments/myenv/terraform

# Create .env file (don't commit!)
cat > .env <<EOF
export TF_VAR_okta_api_token="your-api-token"
export TF_VAR_okta_org_name="your-org"
export TF_VAR_okta_base_url="okta.com"
EOF

# Load variables
source .env
```

**Step 3: Initialize**

```bash
terraform init
```

**✅ Done!** State stored locally in `terraform.tfstate`

### Cost

**Free!** No infrastructure costs.

### Benefits

- ✅ **Quick setup** - 2 minutes
- ✅ **Simple** - No external dependencies
- ✅ **Free** - No costs
- ✅ **Offline** - Works without internet (after init)

### Limitations

⚠️ **Critical Limitations:**
- ❌ **NO team collaboration** - State is local file only
- ❌ **NO state locking** - Risk of corruption with concurrent runs
- ❌ **NO version history** - Can't rollback mistakes
- ❌ **NO backup** - If state file lost, resources orphaned
- ❌ **NO GitHub Actions** - Workflows can't access local state
- ❌ **Manual backup required** - Must copy state file manually

### ⚠️ Use Local State ONLY For:

- Learning Terraform
- Testing configurations
- Solo development
- Throwaway environments

### ❌ NEVER Use Local State For:

- Production environments
- Team collaboration
- Long-lived environments
- Critical infrastructure

### Backup Strategy (If Using Local)

```bash
# Backup state regularly
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d)

# Store backups securely
mkdir -p ~/terraform-backups
cp terraform.tfstate ~/terraform-backups/myenv-$(date +%Y%m%d).tfstate
```

---

## Migration Between Backends

### From Local to AWS S3

```bash
# 1. Set up S3 backend (see Path 1 above)

# 2. Update provider.tf with S3 backend config

# 3. Migrate state
cd environments/myenv/terraform
terraform init -migrate-state

# Terraform will detect change and ask to migrate
# Answer 'yes' to copy state to S3
```

### From Local to Terraform Cloud

```bash
# 1. Set up Terraform Cloud (see Path 2 above)

# 2. Update provider.tf with cloud config

# 3. Migrate state
terraform login
terraform init -migrate-state
```

### From Terraform Cloud to AWS S3

```bash
# 1. Pull state from Terraform Cloud
terraform state pull > terraform.tfstate

# 2. Update provider.tf with S3 backend

# 3. Migrate
terraform init -migrate-state
```

---

## Quick Comparison Chart

```
┌─────────────────────────────────────────────────────────┐
│                    DECISION CHART                        │
└─────────────────────────────────────────────────────────┘

Production? ──YES──> Team? ──YES──> Use AWS S3
    │                  │
    │                  └──NO───> Use Terraform Cloud
    │
    └──NO───> Testing only? ──YES──> Use Local
                              │
                              └──NO───> Use Terraform Cloud
```

---

## FAQs

### Q: Can I switch backends later?

**A:** Yes! Terraform supports state migration. See [Migration Between Backends](#migration-between-backends).

### Q: Which backend do you recommend?

**A:**
- **Teams/Production:** AWS S3
- **Individuals:** Terraform Cloud
- **Testing:** Local

### Q: Can I use a different S3 bucket name?

**A:** Yes! Edit `aws-backend/variables.tf` and update bucket name before running `terraform apply`.

### Q: Does Terraform Cloud support GitHub Actions?

**A:** Yes! Use `TF_CLOUD_TOKEN` secret and Terraform Cloud will handle state automatically.

### Q: What if I don't have AWS account?

**A:** Use Terraform Cloud instead. Zero AWS required.

### Q: Is local state ever okay for production?

**A:** **NO.** Never use local state for production. Always use remote backend (S3 or Terraform Cloud).

### Q: How much does Terraform Cloud cost?

**A:** Free tier: up to 500 resources, 5 users. Paid: $20/user/month for teams.

### Q: Can I use Azure or GCP for state backend?

**A:** Yes, but this template provides AWS S3 setup. You'd need to configure Azure/GCP backend yourself.

---

## Next Steps

Once you've chosen and set up your backend:

1. **Initialize Terraform**
   ```bash
   cd environments/myenv/terraform
   terraform init
   ```

2. **Verify State Backend**
   ```bash
   terraform state list
   # Should work without errors
   ```

3. **Continue Setup**
   → [01-GETTING-STARTED.md](./01-GETTING-STARTED.md#making-your-first-change)

---

## Getting Help

**Still not sure which to choose?**
- Ask in [GitHub Discussions](https://github.com/joevanhorn/okta-terraform-demo-template/discussions)
- Review [AWS_BACKEND_SETUP.md](./AWS_BACKEND_SETUP.md) for AWS details
- Check [Terraform Cloud docs](https://developer.hashicorp.com/terraform/cloud-docs)

**Having setup issues?**
- See [05-TROUBLESHOOTING.md](./05-TROUBLESHOOTING.md)
- Check [GitHub Issues](https://github.com/joevanhorn/okta-terraform-demo-template/issues)
