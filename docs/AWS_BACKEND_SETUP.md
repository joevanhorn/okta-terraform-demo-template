# AWS S3 Backend Setup and Migration Guide

This guide walks you through setting up AWS S3 as the Terraform state backend with DynamoDB state locking, and migrating existing local state files to S3.

---

## Overview

The repository now uses AWS S3 for storing Terraform state with the following benefits:

✅ **Remote State Storage** - State files stored securely in S3
✅ **State Locking** - DynamoDB prevents concurrent modifications
✅ **State Versioning** - S3 versioning for state history
✅ **Encryption** - State encrypted at rest and in transit
✅ **Team Collaboration** - Multiple team members can work safely
✅ **GitHub Actions Integration** - Automated CI/CD with OIDC authentication

**Architecture:**
```
GitHub Actions (OIDC) → AWS IAM Role → S3 Bucket + DynamoDB Table
```

---

## Prerequisites

Before starting, ensure you have:

- [x] AWS CLI installed and configured with admin credentials
- [x] Terraform >= 1.9.0 installed
- [x] Access to create IAM roles, S3 buckets, and DynamoDB tables
- [x] GitHub repository admin access (for secrets)

---

## Step-by-Step Setup

> **CRITICAL: S3 Bucket Names Must Be Globally Unique**
>
> S3 bucket names are **globally unique across ALL AWS accounts worldwide**. The default bucket name `okta-terraform-demo` in this template is almost certainly already taken by someone else.
>
> **You MUST update the bucket name before deploying.** Edit `aws-backend/variables.tf`:
> ```hcl
> variable "state_bucket_name" {
>   default = "okta-terraform-<your-org-name>"  # e.g., "okta-terraform-acme-corp"
> }
> ```
>
> If you see `BucketAlreadyExists` error, choose a different, more unique name.

### Step 1: Deploy AWS Backend Infrastructure

The `aws-backend/` directory contains Terraform configuration to create all necessary AWS resources.

**First, update the bucket name** in `aws-backend/variables.tf` to something unique to your organization.

Then deploy:

```bash
# Navigate to aws-backend directory
cd aws-backend

# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Apply the configuration
terraform apply
```

**What gets created:**
- S3 bucket: `okta-terraform-demo` (with versioning and encryption)
- S3 bucket: `okta-terraform-demo-logs` (for access logging)
- DynamoDB table: `okta-terraform-state-lock` (for state locking)
- IAM OIDC Provider: GitHub Actions authentication
- IAM Role: `GitHubActions-OktaTerraform` (for GitHub Actions)
- IAM Policy: `TerraformStateAccess` (S3 and DynamoDB permissions)

**Save the outputs!** You'll need them for the next steps.

```bash
# View outputs
terraform output

# Save to file for reference
terraform output > ../setup-outputs.txt
```

---

### Step 2: Configure GitHub Secrets

After deploying the backend infrastructure, configure GitHub secrets for OIDC authentication.

#### 2.1 Navigate to GitHub Repository Settings

```
Your Repository → Settings → Secrets and variables → Actions
```

#### 2.2 Add Repository Secret

Click **"New repository secret"**

**Secret Name:** `AWS_ROLE_ARN`

**Secret Value:** Copy from Terraform output `github_actions_role_arn`

Example value:
```
arn:aws:iam::123456789012:role/GitHubActions-OktaTerraform
```

**⚠️ Important:** This is the ONLY AWS secret you need. The role uses OIDC for authentication - no access keys required!

---

### Step 3: Migrate Existing State to S3

If you have existing local Terraform state files, migrate them to S3.

#### For Each Environment:

**MyOrg Example:**

```bash
# Navigate to environment
cd environments/myorg/terraform

# Check if you have existing state
ls -la terraform.tfstate

# If state file exists, proceed with migration
# Otherwise, skip to Step 4
```

**Initialize with new backend (will prompt for migration):**

```bash
terraform init -migrate-state
```

**Expected output:**
```
Initializing the backend...
Terraform detected that the backend type changed from "local" to "s3".

Do you want to copy existing state to the new backend?
  Pre-existing state was found while migrating the previous "local" backend to the
  newly configured "s3" backend. No existing state was found in the newly
  configured "s3" backend. Do you want to copy this state to the new "s3"
  backend? Enter "yes" to copy and "no" to start with an empty state.

  Enter a value:
```

**Type:** `yes` and press Enter

**Verification:**

```bash
# List state in S3
aws s3 ls s3://okta-terraform-demo/Okta-GitOps/myorg/

# Should show:
# terraform.tfstate

# Verify DynamoDB table exists
aws dynamodb describe-table --table-name okta-terraform-state-lock

# Test state locking by running plan
terraform plan
```

#### Repeat for Other Environments

```bash
# Production
cd environments/myorg/terraform
terraform init -migrate-state

# Staging
cd environments/myorg/terraform
terraform init -migrate-state

# Development
cd environments/myorg/terraform
terraform init -migrate-state
```

---

### Step 4: Verify GitHub Actions Integration

Now test that GitHub Actions can authenticate with AWS and access the state.

#### 4.1 Create a Test Change

```bash
# Make a small change (or just run workflows)
git checkout -b test-aws-backend

# Trigger the workflow
git add .
git commit -m "test: Verify AWS backend integration"
git push -u origin test-aws-backend
```

#### 4.2 Create Pull Request

```bash
gh pr create --title "Test: AWS Backend Integration" --body "Testing S3 backend and OIDC authentication"
```

#### 4.3 Monitor Workflow

Go to **Actions** tab in GitHub and watch the `Terraform Plan` workflow run.

**Expected behavior:**
- ✅ Checkout repository
- ✅ Configure AWS Credentials via OIDC
- ✅ Terraform Init (should access S3 backend)
- ✅ Terraform Plan (should acquire DynamoDB lock)
- ✅ Post plan as PR comment

**If successful:** AWS backend is working!

**If failed:** See Troubleshooting section below

---

### Step 5: Clean Up Local State Files

Once migration is verified, clean up local state files (they're now in S3).

**⚠️ ONLY do this after confirming state is in S3!**

```bash
# Verify state is in S3
aws s3 ls s3://okta-terraform-demo/Okta-GitOps/ --recursive

# For each environment with migrated state
cd environments/myorg/terraform

# Remove local state files (they're backed up in S3 versions)
rm -f terraform.tfstate
rm -f terraform.tfstate.backup

# These files are now git-ignored via .gitignore
```

**Update .gitignore** (if not already present):

```bash
# Add to .gitignore if not present
cat >> .gitignore << 'EOF'

# Local Terraform state (now in S3)
*.tfstate
*.tfstate.*
*.tfstate.backup
EOF
```

---

## State Storage Structure

Your state files are organized by environment in S3:

```
s3://okta-terraform-demo/
└── Okta-GitOps/
    ├── myorg/
    │   └── terraform.tfstate
    ├── production/
    │   └── terraform.tfstate
    ├── staging/
    │   └── terraform.tfstate
    └── development/
        └── terraform.tfstate
```

Each environment's state is:
- ✅ Isolated (no cross-environment contamination)
- ✅ Encrypted (AES256 server-side encryption)
- ✅ Versioned (S3 versioning enabled)
- ✅ Logged (access logs in separate bucket)
- ✅ Locked (DynamoDB state locking)

---

## Testing State Locking

Verify that state locking prevents concurrent modifications:

### Test 1: Concurrent Plan Attempts

Open two terminal windows:

**Terminal 1:**
```bash
cd environments/myorg/terraform
terraform apply
# Don't confirm yet - leave it waiting for confirmation
```

**Terminal 2 (while Terminal 1 is waiting):**
```bash
cd environments/myorg/terraform
terraform plan
```

**Expected result in Terminal 2:**
```
Error acquiring the state lock

Error message: ConditionalCheckFailedException: The conditional request failed
Lock Info:
  ID:        abc-123-def-456
  Path:      okta-terraform-demo/Okta-GitOps/myorg/terraform.tfstate
  Operation: OperationTypeApply
  Who:       user@hostname
  Version:   1.9.0
  Created:   2025-11-08 10:30:00 UTC
```

**This is correct behavior!** State locking is working.

Press `Ctrl+C` in Terminal 1 to release the lock.

### Test 2: Lock Auto-Release

State locks are automatically released when operations complete:

```bash
terraform plan
# Lock acquired, plan runs, lock released automatically

terraform plan
# Lock acquired again (previous lock was released)
```

---

## Viewing State History

S3 versioning provides state history for rollback if needed:

### List All State Versions

```bash
aws s3api list-object-versions \
  --bucket okta-terraform-demo \
  --prefix Okta-GitOps/myorg/terraform.tfstate
```

### Restore Previous State Version

**⚠️ Use with extreme caution!**

```bash
# Download current state first (backup)
aws s3 cp \
  s3://okta-terraform-demo/Okta-GitOps/myorg/terraform.tfstate \
  terraform.tfstate.before-restore

# Get specific version
aws s3api get-object \
  --bucket okta-terraform-demo \
  --key Okta-GitOps/myorg/terraform.tfstate \
  --version-id <VERSION_ID> \
  terraform.tfstate

# Push restored state back to S3
terraform state push terraform.tfstate
```

---

## Troubleshooting

### Error: "AccessDenied" in GitHub Actions

**Symptom:**
```
Error: failed to refresh cached credentials, failed to retrieve credentials
```

**Cause:** GitHub Actions role doesn't have permission or wrong ARN

**Solution:**
```bash
# Verify the role ARN in GitHub secrets
# Go to: Settings → Secrets → AWS_ROLE_ARN

# Check it matches Terraform output
cd aws-backend
terraform output github_actions_role_arn

# Verify trust relationship
aws iam get-role --role-name GitHubActions-OktaTerraform \
  --query 'Role.AssumeRolePolicyDocument'

# Should show your repository in the trust policy
```

### Error: "Error acquiring the state lock" (Stuck Lock)

**Symptom:**
```
Error acquiring the state lock
Lock Info ID: abc-123-def
```

**Cause:** Previous Terraform run was interrupted (Ctrl+C, crash, etc.)

**Solution 1: Wait** (locks auto-expire after timeout)

**Solution 2: Force Unlock**
```bash
# Get the Lock ID from error message
terraform force-unlock <LOCK_ID>

# Confirm when prompted
```

**Solution 3: Manual DynamoDB Cleanup** (if force-unlock fails)
```bash
# List locks
aws dynamodb scan --table-name okta-terraform-state-lock

# Delete specific lock (use LockID from error)
aws dynamodb delete-item \
  --table-name okta-terraform-state-lock \
  --key '{"LockID": {"S": "okta-terraform-demo/Okta-GitOps/myorg/terraform.tfstate"}}'
```

### Error: "Bucket does not exist"

**Symptom:**
```
Error: Failed to get existing workspaces: S3 bucket does not exist.
```

**Cause:** S3 bucket not created or wrong bucket name

**Solution:**
```bash
# Verify bucket exists
aws s3 ls s3://okta-terraform-demo

# If not found, check Terraform backend config
cat environments/myorg/terraform/provider.tf

# Should match:
#   bucket = "okta-terraform-demo"

# If different, update provider.tf or create bucket
```

### Error: "State file not found" After Migration

**Symptom:**
```
terraform plan
# Shows empty plan (no existing resources)
```

**Cause:** State wasn't migrated or migrated to wrong key path

**Solution:**
```bash
# List all states in bucket
aws s3 ls s3://okta-terraform-demo/Okta-GitOps/ --recursive

# Check backend configuration
terraform init -reconfigure

# If state is at wrong path, copy it
aws s3 cp \
  s3://okta-terraform-demo/OLD_PATH \
  s3://okta-terraform-demo/Okta-GitOps/myorg/terraform.tfstate
```

### GitHub Actions Workflow Fails to Authenticate

**Symptom:**
```
Error: Failed to assume role
```

**Cause:** OIDC provider not properly configured

**Solution:**
```bash
# Verify OIDC provider exists
aws iam list-open-id-connect-providers

# Should show:
# arn:aws:iam::ACCOUNT:oidc-provider/token.actions.githubusercontent.com

# If missing, re-apply aws-backend infrastructure
cd aws-backend
terraform apply
```

---

## Security Best Practices

### Production Recommendations

1. **Enable MFA Delete on S3 Bucket**
   ```bash
   aws s3api put-bucket-versioning \
     --bucket okta-terraform-demo \
     --versioning-configuration Status=Enabled,MFADelete=Enabled \
     --mfa "arn:aws:iam::ACCOUNT:mfa/USER TOKEN"
   ```

2. **Restrict IAM Role to Specific Branches**

   Edit trust policy in `aws-backend/main.tf`:
   ```hcl
   condition {
     test     = "StringLike"
     variable = "token.actions.githubusercontent.com:sub"
     values   = ["repo:joevanhorn/okta-terraform-complete-demo:ref:refs/heads/main"]
   }
   ```

3. **Enable CloudTrail Logging**
   ```bash
   # Track all S3 and DynamoDB API calls
   aws cloudtrail create-trail --name okta-terraform-state-audit
   ```

4. **Set S3 Lifecycle Rules**

   Delete old state versions after 90 days:
   ```bash
   aws s3api put-bucket-lifecycle-configuration \
     --bucket okta-terraform-demo \
     --lifecycle-configuration file://lifecycle.json
   ```

5. **Enable S3 Access Logging Analysis**

   Regularly review access logs for unauthorized access attempts.

---

## Cost Estimate

**Monthly AWS Costs (Approximate):**

| Service | Usage | Cost |
|---------|-------|------|
| S3 Storage | ~10 MB state files | $0.23 |
| S3 Versioning | ~10 old versions | $0.23 |
| S3 Requests | ~1000 requests/month | $0.05 |
| DynamoDB | On-demand, ~100 operations | $0.01 |
| Data Transfer | Minimal | $0.00 |
| **Total** | | **~$0.50/month** |

**Note:** Costs scale with:
- Number of Terraform operations
- Size of state files
- Number of state versions retained
- Number of environments

---

## Rollback Instructions

If you need to rollback to local state:

### Step 1: Download State from S3

```bash
cd environments/myorg/terraform

# Download current state from S3
terraform state pull > terraform.tfstate
```

### Step 2: Remove Backend Configuration

Edit `provider.tf` and comment out the backend block:

```hcl
# backend "s3" {
#   bucket         = "okta-terraform-demo"
#   key            = "Okta-GitOps/myorg/terraform.tfstate"
#   region         = "us-east-1"
#   encrypt        = true
#   dynamodb_table = "okta-terraform-state-lock"
# }
```

### Step 3: Reinitialize with Local Backend

```bash
terraform init -migrate-state
# Type "yes" to migrate state from S3 to local
```

### Step 4: Remove GitHub Actions AWS Authentication

Edit `.github/workflows/terraform-plan.yml` and remove:

```yaml
- name: Configure AWS Credentials via OIDC
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    role-session-name: GitHubActions-TerraformPlan
    aws-region: us-east-1
```

---

## Next Steps

After completing the setup:

1. ✅ **Update Documentation** - Update team documentation with S3 backend details
2. ✅ **Train Team** - Ensure team understands state locking and S3 backend
3. ✅ **Set Up Monitoring** - Configure CloudWatch alerts for S3 bucket access
4. ✅ **Configure Backups** - Set up automated S3 bucket replication (optional)
5. ✅ **Review Access** - Periodically review IAM role permissions and usage

---

## Related Documentation

- [Terraform S3 Backend Documentation](https://www.terraform.io/docs/language/settings/backends/s3.html)
- [GitHub Actions OIDC with AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [DynamoDB State Locking](https://www.terraform.io/docs/language/settings/backends/s3.html#dynamodb-state-locking)
- [aws-backend/README.md](../aws-backend/README.md) - Backend infrastructure details

---

**Last Updated:** 2025-11-09

**Questions or Issues?** See the [Troubleshooting](#troubleshooting) section or file an issue in the repository.
