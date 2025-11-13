# GitHub Secrets Setup Guide

This guide documents all required secrets for the Okta Terraform template repository.

---

## Table of Contents

1. [Overview](#overview)
2. [Repository-Level Secrets](#repository-level-secrets)
3. [Environment-Level Secrets](#environment-level-secrets)
4. [Setup Instructions](#setup-instructions)
5. [Validation](#validation)
6. [Troubleshooting](#troubleshooting)

---

## Overview

This template uses **two types** of GitHub secrets:

| Secret Type | Purpose | Required For |
|------------|---------|--------------|
| **Repository Secrets** | AWS backend access (shared across all environments) | All deployments |
| **Environment Secrets** | Okta credentials and infrastructure variables (per environment) | Specific environments |

**Total secrets needed:**
- **Minimal setup** (Okta only): 4 secrets
- **Full setup** (Okta + Infrastructure): 7 secrets

> **📝 Note:** Placeholder secrets have been pre-configured in this template repository for ease of setup. However, **all secret values must be updated with your actual credentials** before running any workflows. The placeholder values will not work and are provided only as examples of the expected format.

---

## Repository-Level Secrets

These secrets are configured at the repository level and shared across all environments.

### AWS_ROLE_ARN

**Purpose:** Allows GitHub Actions to authenticate with AWS via OIDC for Terraform state storage.

**Where to set:** `Settings → Secrets and variables → Actions → Repository secrets`

**How to get the value:**

1. Deploy the AWS backend infrastructure:
   ```bash
   cd aws-backend
   terraform init
   terraform apply
   ```

2. Get the role ARN:
   ```bash
   terraform output github_actions_role_arn
   ```

**Example value:**
```
arn:aws:iam::123456789012:role/GitHubActions-OktaTerraform
```

**Required:** ✅ Yes (for all Terraform operations)

---

## ⚠️ CRITICAL: Environment Naming Requirements

**GitHub Environment names and secret names are CASE-SENSITIVE and must match EXACTLY.**

### ❌ Common Mistakes That Will Cause Failures:

| What You Set | What Workflow Expects | Result |
|--------------|----------------------|--------|
| Environment: `myorg` | Workflow input: `MyOrg` | ❌ **FAILS** - Environment not found |
| Environment: `Production` | Workflow input: `production` | ❌ **FAILS** - Environment not found |
| Secret: `okta_api_token` | Expected: `OKTA_API_TOKEN` | ❌ **FAILS** - Secret not found |
| Secret: `Okta_Org_Name` | Expected: `OKTA_ORG_NAME` | ❌ **FAILS** - Secret not found |

### ✅ Correct Pattern:

1. **Environment Name:** Can be any case (e.g., `MyOrg`, `Production`, `dev-env`)
2. **Workflow Input:** Must match environment name EXACTLY
3. **Secret Names:** Must be UPPERCASE with underscores (e.g., `OKTA_API_TOKEN`)

**Example that works:**
```
Environment created: "MyOrg"
Workflow dispatch input: "MyOrg" ← Must match exactly!
Secrets in "MyOrg" environment:
  - OKTA_API_TOKEN ← Must be uppercase
  - OKTA_ORG_NAME ← Must be uppercase
  - OKTA_BASE_URL ← Must be uppercase
```

### 🔍 How to Verify Before Running Workflows:

1. **Check environment name:**
   - Go to: Settings → Environments
   - Note the EXACT name (including capitalization)

2. **Check secret names in that environment:**
   - Click on the environment
   - Verify all secret names are UPPERCASE with underscores

3. **When running workflow:**
   - Copy-paste the environment name (don't type it manually)
   - Ensures exact match

### 💡 Recommended Naming Convention:

**For consistency, we recommend:**
- **Environment names:** PascalCase (e.g., `MyOrg`, `DevEnvironment`, `Production`)
- **Secret names:** UPPERCASE_WITH_UNDERSCORES (always - not optional)

---

## Environment-Level Secrets

These secrets are configured per GitHub Environment (e.g., "MyOrg", "Production", etc.).

> **📍 Remember:** The environment name you choose here must be used EXACTLY (case-sensitive) when running workflows!

### Core Okta Secrets (Required for All Environments)

#### OKTA_API_TOKEN

**Purpose:** API token for authenticating with Okta to manage resources.

**Where to set:** `Settings → Environments → [Your Environment] → Environment secrets`

**How to get the value:**

1. Log in to Okta Admin Console: `https://[your-org]-admin.okta.com/` or `https://[your-org]-admin.oktapreview.com/`
2. Navigate to: **Security → API → Tokens**
3. Click **Create Token**
4. Name it: "GitHub Actions - Terraform"
5. Copy the token immediately (you won't be able to see it again)

**Example value:**
```
00abc123xyz789defABCDEF456...
```

**Required Scopes:**
- `okta.users.manage`
- `okta.groups.manage`
- `okta.apps.manage`
- `okta.policies.manage`
- `okta.schemas.manage`
- `okta.identityGovernance.manage` (if using OIG features)

**Required:** ✅ Yes

---

#### OKTA_ORG_NAME

**Purpose:** Your Okta organization name (subdomain).

**Where to set:** `Settings → Environments → [Your Environment] → Environment secrets`

**How to get the value:**

Extract from your Okta URL:
- If URL is `https://demo-myorg.okta.com` → use `demo-myorg`
- If URL is `https://myorg.oktapreview.com` → use `myorg`

**Example values:**
```
myorg
demo-acme
customer-demo
```

**Required:** ✅ Yes

---

#### OKTA_BASE_URL

**Purpose:** Okta base domain (determines production vs preview environment).

**Where to set:** `Settings → Environments → [Your Environment] → Environment secrets`

**Possible values:**
- `okta.com` - Production Okta environment
- `oktapreview.com` - Preview/sandbox Okta environment
- `okta-emea.com` - EMEA production environment

**Example value:**
```
oktapreview.com
```

**Required:** ✅ Yes

---

### Infrastructure Secrets (Optional - Only for Active Directory Deployment)

These secrets are only needed if you're deploying AWS infrastructure for Active Directory integration.

#### TF_VAR_admin_password

**Purpose:** Windows Administrator password for the Domain Controller EC2 instance.

**Where to set:** `Settings → Environments → [Your Environment] → Environment secrets`

**Password Requirements:**
- Minimum 8 characters
- Must include:
  - Uppercase letters (A-Z)
  - Lowercase letters (a-z)
  - Numbers (0-9)
  - Special characters (!@#$%^&*)

**Example value:**
```
Welcome123!
MySecurePassword456!
```

**Required:** Only if deploying infrastructure

---

#### TF_VAR_ad_safe_mode_password

**Purpose:** Active Directory Safe Mode (Directory Services Restore Mode) password.

**Where to set:** `Settings → Environments → [Your Environment] → Environment secrets`

**Password Requirements:** Same as admin_password

**Example value:**
```
SafeMode789!
RecoveryPassword456!
```

**Important:** This password is used for AD recovery scenarios. Store it securely!

**Required:** Only if deploying infrastructure

---

#### TF_VAR_okta_org_url

**Purpose:** Full Okta organization URL (used by infrastructure scripts to download Okta AD Agent).

**Where to set:** `Settings → Environments → [Your Environment] → Environment secrets`

**How to construct:**
- Format: `https://[OKTA_ORG_NAME].[OKTA_BASE_URL]`
- Example: `https://demo-myorg.oktapreview.com`

**Example values:**
```
https://demo-myorg.oktapreview.com
https://myorg.okta.com
https://acme-prod.okta.com
```

**Required:** Only if deploying infrastructure

---

## Setup Instructions

### Step 1: Set Repository Secret

1. Navigate to: `https://github.com/[your-username]/okta-terraform-demo-template/settings/secrets/actions`
2. Click **"New repository secret"**
3. Add secret:
   - **Name:** `AWS_ROLE_ARN`
   - **Value:** [ARN from aws-backend deployment]
4. Click **"Add secret"**

---

### Step 2: Create GitHub Environment

1. Navigate to: `https://github.com/[your-username]/okta-terraform-demo-template/settings/environments`
2. Click **"New environment"**
3. Name it: `MyOrg` (or your organization name)
4. Click **"Configure environment"**
5. (Optional) Configure protection rules:
   - ☑️ Required reviewers
   - ☑️ Wait timer: 5 minutes
   - ☑️ Deployment branches: main only

---

### Step 3: Add Okta Secrets to Environment

In your newly created environment, click **"Add secret"** for each:

**For Okta-only deployment (minimal):**
1. **OKTA_API_TOKEN** → [Token from Okta Admin Console]
2. **OKTA_ORG_NAME** → [Your org subdomain]
3. **OKTA_BASE_URL** → [okta.com or oktapreview.com]

**For infrastructure deployment (additional):**
4. **TF_VAR_admin_password** → [Windows admin password]
5. **TF_VAR_ad_safe_mode_password** → [AD safe mode password]
6. **TF_VAR_okta_org_url** → [Full Okta URL]

---

### Step 4: Verify Configuration

Run this command to verify secrets are accessible (won't show values):

```bash
# List repository secrets (names only)
gh secret list

# List environment secrets
gh secret list --env MyOrg
```

Expected output:
```
AWS_ROLE_ARN                     Updated 2024-01-01

# In MyOrg environment:
OKTA_API_TOKEN                   Updated 2024-01-01
OKTA_ORG_NAME                    Updated 2024-01-01
OKTA_BASE_URL                    Updated 2024-01-01
TF_VAR_admin_password            Updated 2024-01-01  # (if using infrastructure)
TF_VAR_ad_safe_mode_password     Updated 2024-01-01  # (if using infrastructure)
TF_VAR_okta_org_url              Updated 2024-01-01  # (if using infrastructure)
```

---

## Validation

### Test Okta Secrets

Run a simple API test:

```bash
curl -X GET \
  "https://[OKTA_ORG_NAME].[OKTA_BASE_URL]/api/v1/users/me" \
  -H "Authorization: SSWS [OKTA_API_TOKEN]" \
  -H "Accept: application/json"
```

**Expected result:** Your Okta user profile (JSON)

**If you get 401 Unauthorized:** Token is invalid or expired

---

### Test AWS Secret

Run a workflow that uses AWS (like terraform-plan):

```bash
gh workflow run terraform-plan.yml
```

Check the workflow logs for successful AWS authentication:
```
✅ Configure AWS Credentials via OIDC
   Assuming role: arn:aws:iam::123456789012:role/GitHubActions-OktaTerraform
   Successfully assumed role
```

---

## Troubleshooting

### Error: "Invalid token provided"

**Symptom:** Okta API returns 401 Unauthorized

**Possible causes:**
1. Token has expired
2. Token was copied incorrectly (missing characters)
3. Token doesn't have required scopes

**Solution:**
1. Generate a new token in Okta Admin Console
2. Ensure you copy the entire token
3. Update the `OKTA_API_TOKEN` secret in GitHub
4. Verify token has `okta.users.manage`, `okta.groups.manage`, etc.

---

### Error: "Unable to assume role"

**Symptom:** GitHub Actions fails with AWS authentication error

**Possible causes:**
1. `AWS_ROLE_ARN` is incorrect
2. GitHub OIDC trust policy not configured correctly
3. Repository name changed after AWS backend deployment

**Solution:**
1. Verify ARN: `cd aws-backend && terraform output github_actions_role_arn`
2. Check trust policy in AWS IAM console
3. Update trust policy if repository name changed:
   ```bash
   cd aws-backend
   terraform apply  # Refreshes OIDC trust policy
   ```

---

### Error: "Backend initialization failed"

**Symptom:** Terraform init fails to connect to S3 backend

**Possible causes:**
1. S3 bucket doesn't exist
2. DynamoDB table doesn't exist
3. IAM role doesn't have access to S3/DynamoDB

**Solution:**
1. Deploy AWS backend: `cd aws-backend && terraform apply`
2. Verify resources exist:
   ```bash
   aws s3 ls s3://okta-terraform-demo/
   aws dynamodb describe-table --table-name okta-terraform-state-lock
   ```
3. Check IAM role permissions

---

### Error: "Environment not found"

**Symptom:** Workflow fails with "Environment not found: MyOrg" or "❌ Environment not found: myorg"

**Root Cause:** Environment names are CASE-SENSITIVE and must match EXACTLY.

**Common Mistake Examples:**
- Created environment: `myorg` but workflow input: `MyOrg` ❌
- Created environment: `Production` but workflow input: `production` ❌
- Created environment: `Dev-Env` but workflow input: `dev-env` ❌

**Solution:**

1. **Check what environment name actually exists:**
   - Go to: `Settings → Environments`
   - Note the EXACT name (including capitalization and hyphens)
   - Example: You see `MyOrg` ← This is what you must use

2. **When running workflow:**
   - Copy-paste the environment name (don't type it manually)
   - In workflow dispatch screen, paste EXACTLY: `MyOrg`

3. **If environment doesn't exist:**
   - Click "New environment"
   - Choose a name and remember it exactly
   - Recommendation: Use PascalCase like `MyOrg` or `DevEnvironment`

**Quick Test:**
```bash
# List all environments
gh api repos/:owner/:repo/environments --jq '.environments[].name'
```

---

### Error: "Secret not found"

**Symptom:** Workflow fails with "Secret OKTA_API_TOKEN not found" or similar

**Root Cause:** Secret names must be UPPERCASE with underscores, and added to the correct environment.

**Common Mistake Examples:**
- Named secret: `okta_api_token` instead of `OKTA_API_TOKEN` ❌
- Named secret: `Okta_Org_Name` instead of `OKTA_ORG_NAME` ❌
- Added secret to Repository secrets instead of Environment secrets ❌
- Added secret to wrong environment (e.g., `Production` instead of `MyOrg`) ❌

**Solution:**

1. **Verify secret names are correct:**
   - Go to: `Settings → Environments → [Your Environment]`
   - Check secret names are UPPERCASE_WITH_UNDERSCORES:
     - ✅ `OKTA_API_TOKEN`
     - ✅ `OKTA_ORG_NAME`
     - ✅ `OKTA_BASE_URL`
     - ❌ `okta_api_token`
     - ❌ `Okta_Api_Token`

2. **Verify secrets are in the correct environment:**
   - Secrets must be in the SAME environment the workflow is using
   - If workflow uses environment "MyOrg", secrets must be in "MyOrg"
   - NOT in Repository secrets, NOT in different environment

3. **Recreate secret with correct name if needed:**
   - Delete the incorrectly named secret
   - Add new secret with EXACT name from list above

**Solution:**
1. Verify secrets in environment: `Settings → Environments → MyOrg → Secrets`
2. Check exact secret names (case-sensitive)
3. Ensure workflow specifies correct environment:
   ```yaml
   environment:
     name: MyOrg  # Must match your environment name
   ```

---

### Warning: Secrets in Logs

**GitHub Actions will automatically mask secret values in logs**, but be careful:

❌ **Don't do this:**
```bash
echo "My token is: ${{ secrets.OKTA_API_TOKEN }}"  # Will be masked
echo "${{ secrets.OKTA_API_TOKEN }}" | base64      # May leak encoded value
```

✅ **Do this instead:**
```bash
# Secrets are automatically available as environment variables
terraform plan  # Reads TF_VAR_* secrets safely
```

---

## Security Best Practices

### 1. Rotate Secrets Regularly

**Okta API Tokens:**
- Create new token quarterly
- Update GitHub secret
- Revoke old token in Okta

### 2. Use Least Privilege

**Okta API Token:**
- Only grant scopes you actually need
- For read-only operations, use a read-only token

### 3. Restrict Environment Access

**GitHub Environments:**
- Enable "Required reviewers" for production
- Use "Deployment branches" to restrict to main branch only
- Set wait timer for accidental deployment prevention

### 4. Monitor Usage

**Audit logs:**
- Review Okta system logs for API token usage
- Check AWS CloudTrail for backend access
- Monitor GitHub Actions logs for unusual activity

### 5. Never Commit Secrets

**Always use:**
- ✅ GitHub Secrets
- ✅ Environment variables
- ✅ AWS Secrets Manager (for advanced use cases)

**Never use:**
- ❌ Hardcoded values in .tf files
- ❌ terraform.tfvars committed to git
- ❌ Secrets in README or documentation

---

## Quick Reference

### Minimal Setup (Okta Only)

| Secret | Type | Value |
|--------|------|-------|
| AWS_ROLE_ARN | Repository | `arn:aws:iam::...` |
| OKTA_API_TOKEN | Environment | `00abc123...` |
| OKTA_ORG_NAME | Environment | `myorg` |
| OKTA_BASE_URL | Environment | `oktapreview.com` |

### Full Setup (Okta + Infrastructure)

| Secret | Type | Value |
|--------|------|-------|
| AWS_ROLE_ARN | Repository | `arn:aws:iam::...` |
| OKTA_API_TOKEN | Environment | `00abc123...` |
| OKTA_ORG_NAME | Environment | `myorg` |
| OKTA_BASE_URL | Environment | `oktapreview.com` |
| TF_VAR_admin_password | Environment | `Welcome123!` |
| TF_VAR_ad_safe_mode_password | Environment | `SafeMode123!` |
| TF_VAR_okta_org_url | Environment | `https://myorg.oktapreview.com` |

---

## Related Documentation

- **[AWS Backend Setup](./docs/AWS_BACKEND_SETUP.md)** - How to deploy AWS backend infrastructure
- **[Template Setup Guide](./TEMPLATE_SETUP.md)** - Complete template setup walkthrough
- **[Infrastructure README](./environments/myorg/infrastructure/README.md)** - Active Directory infrastructure guide
- **[Environment Setup Example](./docs/ENVIRONMENT_SETUP_EXAMPLE.md)** - Example environment configuration

---

**Last Updated:** 2025-11-13
