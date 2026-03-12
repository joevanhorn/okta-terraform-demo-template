# ITP Demo — AWS Requirements

This document covers the AWS infrastructure needed for the ITP (Identity Threat Protection) demo module.

---

## Overview

The ITP demo module uses AWS for three optional components:

| Component | AWS Services | Required For |
|-----------|-------------|-------------|
| **Session Replayer** | Lambda (cross-region) | Real mode — cookie replay from different geography |
| **SSF JWKS Endpoint** | Lambda, SSM Parameter Store | SSF mode — public key serving + secret storage |
| **Video Storage** | S3 | Real mode — demo video recording storage |

**All components are optional.** Quick mode requires no AWS infrastructure at all.

---

## IAM Permissions

### Terraform Deployment Role

The role used to deploy the ITP module via Terraform needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LambdaManagement",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:CreateFunctionUrlConfig",
        "lambda:DeleteFunctionUrlConfig",
        "lambda:GetFunctionUrlConfig",
        "lambda:TagResource",
        "lambda:UntagResource",
        "lambda:ListTags"
      ],
      "Resource": "arn:aws:lambda:*:*:function:*-itp-*"
    },
    {
      "Sid": "LambdaSsfJwks",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:CreateFunctionUrlConfig",
        "lambda:DeleteFunctionUrlConfig",
        "lambda:GetFunctionUrlConfig",
        "lambda:TagResource",
        "lambda:UntagResource",
        "lambda:ListTags"
      ],
      "Resource": "arn:aws:lambda:*:*:function:*-ssf-jwks"
    },
    {
      "Sid": "IAMRoleManagement",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PassRole",
        "iam:TagRole",
        "iam:UntagRole",
        "iam:ListRolePolicies",
        "iam:ListAttachedRolePolicies"
      ],
      "Resource": [
        "arn:aws:iam::*:role/*-itp-*",
        "arn:aws:iam::*:role/*-ssf-jwks-role"
      ]
    },
    {
      "Sid": "SSMManagement",
      "Effect": "Allow",
      "Action": [
        "ssm:PutParameter",
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:DeleteParameter",
        "ssm:DescribeParameters",
        "ssm:AddTagsToResource",
        "ssm:ListTagsForResource"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/*/itp/*"
    },
    {
      "Sid": "S3BucketManagement",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:GetBucketPolicy",
        "s3:PutBucketPolicy",
        "s3:DeleteBucketPolicy",
        "s3:GetBucketVersioning",
        "s3:PutBucketVersioning",
        "s3:GetEncryptionConfiguration",
        "s3:PutEncryptionConfiguration",
        "s3:GetLifecycleConfiguration",
        "s3:PutLifecycleConfiguration",
        "s3:GetBucketPublicAccessBlock",
        "s3:PutBucketPublicAccessBlock",
        "s3:GetBucketTagging",
        "s3:PutBucketTagging"
      ],
      "Resource": "arn:aws:s3:::*-itp-demo-videos"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DeleteLogGroup",
        "logs:PutRetentionPolicy",
        "logs:DescribeLogGroups",
        "logs:TagResource"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/*-itp-*"
    }
  ]
}
```

### GitHub Actions Runtime Role

The role used by GitHub Actions workflows to run ITP demos needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SSMReadCredentials",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/*/itp/*"
    },
    {
      "Sid": "LambdaInvoke",
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": [
        "arn:aws:lambda:*:*:function:*-itp-session-replayer",
        "arn:aws:lambda:*:*:function:*-ssf-jwks"
      ]
    },
    {
      "Sid": "S3VideoUpload",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::*-itp-demo-videos/*"
    }
  ]
}
```

---

## Cross-Region Deployment

The ITP demo module deploys Lambda functions in multiple regions:

| Component | Region | Purpose |
|-----------|--------|---------|
| SSF JWKS Lambda | Default AWS region | Serves public key for JWT verification |
| Session Replayer Lambda | `attacker_region` (default: `eu-west-1`) | Cookie replay from different geography |

### AWS Provider Configuration

Your Terraform must include a provider alias for the attacker region:

```hcl
# Primary AWS provider (your default region)
provider "aws" {
  region = "us-east-1"
}

# Attacker region for session replayer Lambda
provider "aws" {
  alias  = "attacker"
  region = "eu-west-1"
}
```

The ITP module expects the attacker provider to be passed in:

```hcl
module "itp_demo" {
  source = "../../modules/itp-demo"
  providers = {
    aws          = aws
    aws.attacker = aws.attacker
  }
  # ...
}
```

---

## GitHub Actions OIDC Role

ITP workflows that use AWS services (real mode, SSF mode) require OIDC authentication:

```yaml
permissions:
  id-token: write    # Required for OIDC
  contents: read

- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    role-session-name: GitHubActions-ITPDemo
    aws-region: us-east-1
```

The `AWS_ROLE_ARN` secret should be set in your GitHub Environment. The role must trust your GitHub repository via OIDC federation.

---

## SSM Parameter Store Layout

All ITP-related parameters follow this convention:

```
/{environment}/itp/
├── password              # (SecureString) Test user password for real mode
├── totp-secret           # (SecureString) Test user TOTP seed for real mode
└── ssf-demo/
    ├── private-key       # (SecureString) RSA private key for SET signing
    └── provider-config   # (String) JSON with issuer, jwks_url, key_id, provider_id
```

### Manual Parameters (Create Before Running Demos)

These must be created manually — they contain user credentials:

```bash
# For real mode — test user credentials
aws ssm put-parameter \
  --name "/{environment}/itp/password" \
  --value "USER_PASSWORD" \
  --type SecureString

aws ssm put-parameter \
  --name "/{environment}/itp/totp-secret" \
  --value "TOTP_BASE32_SECRET" \
  --type SecureString
```

### Terraform-Managed Parameters (Created Automatically)

These are created by the Terraform module when `enable_ssf_endpoint = true`:

- `/{environment}/itp/ssf-demo/private-key` — RSA private key (from `tls_private_key`)
- `/{environment}/itp/ssf-demo/provider-config` — JSON config (populated by `setup_ssf_provider.py`)

---

## Cost Estimate

The ITP demo infrastructure has negligible AWS costs:

| Resource | Cost |
|----------|------|
| Lambda functions (2) | Free tier covers typical demo usage |
| SSM parameters (4) | Free for standard parameters; ~$0.20/month for advanced (SecureString) |
| S3 bucket | ~$0.023/GB/month (demo videos are typically < 50 MB each) |
| CloudWatch Logs | Free tier covers typical usage |

**Estimated monthly cost: < $1** for typical demo usage.

---

## Terraform Module Configuration

See the example file at `environments/myorg/terraform/itp_demo.tf.example` for a complete module invocation. Key variables:

```hcl
module "itp_demo" {
  source = "../../modules/itp-demo"

  providers = {
    aws          = aws
    aws.attacker = aws.attacker
  }

  environment = "myorg"

  # Feature flags — enable only what you need
  enable_session_replayer = true   # Real mode Lambda
  enable_ssf_endpoint    = true   # SSF mode Lambda + SSM
  enable_video_bucket    = true   # S3 for video recordings

  # Optional customization
  attacker_region         = "eu-west-1"
  video_retention_days    = 90
  github_actions_role_arn = "arn:aws:iam::123456789012:role/GitHubActions"

  tags = {
    Project     = "okta-itp-demo"
    Environment = "myorg"
  }
}
```

See [ITP Demo Guide](../guides/itp-demo.md) for usage instructions.
