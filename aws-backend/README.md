# AWS Backend Infrastructure

This directory contains Terraform configuration for setting up the AWS backend infrastructure used by all Okta environments.

> **IMPORTANT: S3 Bucket Names Must Be Globally Unique**
>
> S3 bucket names are **globally unique across ALL AWS accounts worldwide**. The default bucket name `okta-terraform-demo` is likely already taken. You **MUST** choose a unique name before running `terraform apply`.
>
> **Update `variables.tf` before deploying:**
> ```hcl
> variable "state_bucket_name" {
>   default = "okta-terraform-demo-<your-unique-suffix>"  # e.g., "okta-terraform-demo-acme-corp-2025"
> }
> ```

## What This Creates

1. **S3 Bucket** (`okta-terraform-demo`)
   - Stores Terraform state files for all environments
   - Versioning enabled for state history
   - Encryption enabled (AES256)
   - Public access blocked
   - Access logging enabled

2. **S3 Bucket** (`okta-terraform-demo-logs`)
   - Stores access logs for the state bucket
   - Security and compliance tracking

3. **DynamoDB Table** (`okta-terraform-state-lock`)
   - State locking to prevent concurrent modifications
   - On-demand billing (pay only for what you use)
   - Point-in-time recovery enabled
   - Encryption enabled

4. **IAM OIDC Provider** (GitHub Actions)
   - Enables secure authentication from GitHub Actions
   - No long-lived AWS credentials needed

5. **IAM Role** (`GitHubActions-OktaTerraform`)
   - Assumed by GitHub Actions workflows
   - Has permission to read/write Terraform state
   - Scoped to your repository only

6. **IAM Policy** (`TerraformStateAccess`)
   - Grants necessary S3 and DynamoDB permissions
   - Attached to the GitHub Actions role

## State Storage Structure

States are organized by environment:

```
okta-terraform-demo/
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

## Setup Instructions

### Prerequisites

- AWS CLI configured with admin credentials
- Terraform >= 1.9.0 installed
- Access to create IAM roles and S3 buckets

### Step 1: Deploy Backend Infrastructure

**Before you start:** Update the S3 bucket name in `variables.tf` to something unique:

```hcl
variable "state_bucket_name" {
  default = "okta-terraform-<your-org-name>"  # Must be globally unique!
}
```

Then deploy:

```bash
# Navigate to aws-backend directory
cd aws-backend

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply
```

**Important:** Save the outputs! You'll need them for the next steps.

### Step 2: Configure GitHub Secrets

After applying, Terraform will output instructions. Add this secret to your GitHub repository:

**Go to:** Settings → Secrets and variables → Actions → New repository secret

**Secret Name:** `AWS_ROLE_ARN`

**Secret Value:** (Copy from Terraform output `github_actions_role_arn`)

Example: `arn:aws:iam::123456789012:role/GitHubActions-OktaTerraform`

### Step 3: Update Environment Backend Configurations

The backend configuration has been created for each environment. See `environments/{env}/terraform/backend.tf`.

### Step 4: Migrate Existing State (If Any)

If you have existing local state files:

```bash
# For each environment
cd environments/myorg/terraform

# This will prompt to migrate state
terraform init -migrate-state

# Confirm the migration when prompted
```

### Step 5: Verify GitHub Actions

Push a change and verify that GitHub Actions can authenticate with AWS and access the state:

```bash
git add .
git commit -m "feat: Configure S3 backend for Terraform state"
git push
```

Watch the workflow run in GitHub Actions. It should successfully authenticate and run Terraform.

## Testing the Setup

### Test State Locking

In two separate terminals:

```bash
# Terminal 1
cd environments/myorg/terraform
terraform apply

# Terminal 2 (while Terminal 1 is waiting)
cd environments/myorg/terraform
terraform plan
# Should see: "Error acquiring the state lock"
```

This confirms state locking is working!

### Test State Versioning

```bash
# List state versions
aws s3api list-object-versions \
  --bucket okta-terraform-demo \
  --prefix Okta-GitOps/myorg/terraform.tfstate

# Restore a previous version if needed
aws s3api get-object \
  --bucket okta-terraform-demo \
  --key Okta-GitOps/myorg/terraform.tfstate \
  --version-id <VERSION_ID> \
  terraform.tfstate.backup
```

## Security Considerations

### Production Recommendations

1. **Enable MFA Delete on S3 Bucket**
   ```bash
   aws s3api put-bucket-versioning \
     --bucket okta-terraform-demo \
     --versioning-configuration Status=Enabled,MFADelete=Enabled \
     --mfa "arn:aws:iam::ACCOUNT:mfa/USER SERIAL_NUMBER"
   ```

2. **Enable S3 Object Lock** (prevents deletion)
   - Consider for compliance requirements
   - Must be enabled at bucket creation

3. **Restrict IAM Role Permissions**
   - Remove the ReadOnlyAccess policy attachment if added
   - Grant only minimum necessary permissions

4. **Enable CloudTrail Logging**
   - Track all API calls to S3 and DynamoDB
   - Monitor for unauthorized access attempts

5. **Set Up Budget Alerts**
   - S3 storage costs
   - DynamoDB costs (should be minimal with on-demand)

### Current Security Features

✅ **Encryption at rest** (S3 and DynamoDB)
✅ **Encryption in transit** (HTTPS only)
✅ **State locking** (prevents concurrent modifications)
✅ **Public access blocked** (no internet exposure)
✅ **OIDC authentication** (no long-lived credentials)
✅ **Versioning enabled** (state history and recovery)
✅ **Access logging** (audit trail)
✅ **Repository-scoped** (only your repo can assume role)

## Troubleshooting

### Error: "AccessDenied" in GitHub Actions

**Cause:** GitHub Actions role doesn't have permission

**Solution:**
```bash
# Verify the role ARN in GitHub secrets matches Terraform output
terraform output github_actions_role_arn

# Check the trust relationship
aws iam get-role --role-name GitHubActions-OktaTerraform --query 'Role.AssumeRolePolicyDocument'
```

### Error: "Error acquiring state lock"

**Cause:** Previous Terraform run was interrupted

**Solution:**
```bash
# Force unlock (use with caution!)
terraform force-unlock <LOCK_ID>

# Or check DynamoDB for stuck locks
aws dynamodb scan --table-name okta-terraform-state-lock
```

### Error: "Bucket already exists"

**Cause:** Bucket name is globally unique and already taken

**Solution:**
```bash
# Update the bucket name in variables.tf
variable "state_bucket_name" {
  default = "okta-terraform-demo-<your-unique-suffix>"
}

# Re-run terraform apply
```

### State File Not Found After Migration

**Cause:** Incorrect backend configuration

**Solution:**
```bash
# Verify backend configuration
terraform init -backend-config="key=Okta-GitOps/myorg/terraform.tfstate"

# List all objects in bucket
aws s3 ls s3://okta-terraform-demo/Okta-GitOps/ --recursive
```

## Cost Estimate

**Monthly costs (approximate):**
- **S3 Storage:** $0.023 per GB (~$0.10/month for small states)
- **S3 Requests:** $0.005 per 1,000 PUT requests (~$0.05/month)
- **S3 Versioning:** $0.023 per GB for old versions (~$0.10/month)
- **DynamoDB:** Pay-per-request (~$0.01/month for typical usage)
- **Data Transfer:** First 100 GB free

**Total: ~$0.30 - $1.00/month** for typical demo usage

**Note:** Costs scale with:
- Number of Terraform operations
- Size of state files
- Number of state versions retained

## Maintenance

### Cleanup Old State Versions

S3 versioning keeps all historical versions. Set up lifecycle rules:

```bash
# Create lifecycle policy to delete old versions after 90 days
aws s3api put-bucket-lifecycle-configuration \
  --bucket okta-terraform-demo \
  --lifecycle-configuration file://lifecycle-policy.json
```

Example `lifecycle-policy.json`:
```json
{
  "Rules": [
    {
      "Id": "DeleteOldVersions",
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90
      }
    }
  ]
}
```

### Monitor State Bucket

```bash
# Check bucket size
aws s3 ls s3://okta-terraform-demo --recursive --summarize

# Check recent state changes
aws s3api list-object-versions \
  --bucket okta-terraform-demo \
  --prefix Okta-GitOps/ \
  --max-items 10
```

## Destroying Backend Infrastructure

**⚠️ WARNING:** Only do this if you're sure you want to delete all state history!

```bash
# First, migrate all environments back to local state
cd environments/myorg/terraform
terraform init -migrate-state -backend=false

# Repeat for all environments
# Then destroy backend infrastructure
cd ../../aws-backend
terraform destroy
```

## Related Documentation

- [Terraform S3 Backend Documentation](https://www.terraform.io/docs/language/settings/backends/s3.html)
- [AWS IAM OIDC for GitHub Actions](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [DynamoDB State Locking](https://www.terraform.io/docs/language/settings/backends/s3.html#dynamodb-state-locking)
