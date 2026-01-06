# AD Domain Controller Module

A reusable Terraform module for deploying Active Directory Domain Controllers on AWS EC2 for Okta integration demos.

## Features

- **Windows Server 2022** on EC2 with automatic AD DS configuration
- **AWS Systems Manager (SSM)** for secure remote management (no RDP required)
- **Secrets Manager** integration for credential storage
- **VPC creation** (optional - can use existing VPC)
- **Sample users and groups** for demo environments
- **Okta AD Agent** automated installation (optional)
- **Multi-region** deployment support

## Quick Start

```hcl
module "ad_dc" {
  source = "../../modules/ad-domain-controller"

  environment     = "demo"
  aws_region      = "us-east-1"
  region_short    = "use1"
  ad_domain_name  = "corp.demo.local"
  ad_netbios_name = "CORP"

  create_sample_users = true
}

output "ssm_command" {
  value = module.ad_dc.ssm_start_session_command
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | >= 5.0 |
| random | >= 3.0 |

## Inputs

### Required

| Name | Description | Type |
|------|-------------|------|
| `environment` | Environment name (e.g., dev, staging, prod) | `string` |
| `aws_region` | AWS region for deployment | `string` |
| `region_short` | Short region identifier (e.g., use1, usw2) | `string` |
| `ad_domain_name` | AD domain name (e.g., corp.example.com) | `string` |
| `ad_netbios_name` | NetBIOS name (e.g., CORP) | `string` |

### Network Configuration

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `create_vpc` | Create new VPC or use existing | `bool` | `true` |
| `existing_vpc_id` | Existing VPC ID (if create_vpc=false) | `string` | `""` |
| `existing_subnet_id` | Existing subnet ID (if create_vpc=false) | `string` | `""` |
| `vpc_cidr` | VPC CIDR block | `string` | `"10.0.0.0/16"` |
| `public_subnet_cidr` | Public subnet CIDR | `string` | `"10.0.1.0/24"` |
| `availability_zone` | AZ for subnet | `string` | `""` (auto) |

### Instance Configuration

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `instance_type` | EC2 instance type | `string` | `"t3.medium"` |
| `root_volume_size` | Root volume size (GB) | `number` | `100` |
| `key_pair_name` | EC2 key pair for RDP | `string` | `""` |
| `assign_elastic_ip` | Assign Elastic IP | `bool` | `false` |

### Security

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `enable_rdp` | Enable RDP in security group | `bool` | `false` |
| `rdp_allowed_cidrs` | CIDRs allowed for RDP | `list(string)` | `[]` |

### AD Configuration

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `ad_admin_username` | Admin username | `string` | `"Administrator"` |
| `create_sample_users` | Create demo users/groups | `bool` | `true` |

### Okta Integration

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `okta_agent_token` | AD Agent registration token | `string` | `""` |
| `okta_org_url` | Okta org URL | `string` | `""` |

### S3 Scripts

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `scripts_bucket_name` | S3 bucket for setup scripts | `string` | `""` |
| `setup_script_s3_key` | S3 key for setup script | `string` | `"scripts/userdata.ps1"` |

## Outputs

| Name | Description |
|------|-------------|
| `instance_id` | EC2 instance ID |
| `private_ip` | Private IP address |
| `public_ip` | Public IP address |
| `vpc_id` | VPC ID |
| `subnet_id` | Subnet ID |
| `security_group_id` | Security group ID |
| `credentials_secret_arn` | Secrets Manager ARN |
| `ssm_start_session_command` | SSM session command |
| `connection_info` | All connection details (object) |

## Sample Data

When `create_sample_users = true`, the module creates:

### Organizational Units
```
Company/
├── Users/
│   ├── Engineering/
│   ├── Sales/
│   ├── Marketing/
│   ├── Finance/
│   ├── HR/
│   ├── IT/
│   └── Executives/
├── Groups/
├── Computers/
└── Service Accounts/
```

### Groups (16 total)
- **Department:** Engineering, Sales, Marketing, Finance, HR, IT, Executives
- **Role:** Managers, Contractors, Remote Workers
- **Application:** Salesforce Users, Jira Users, Confluence Users, GitHub Users, AWS Console Users, VPN Users
- **Privilege:** IT Admins, Security Team, Help Desk

### Users (22 total)
Sample users across all departments with realistic titles and group memberships.

## Security Considerations

1. **No RDP by default** - Use SSM for secure access
2. **IMDSv2 required** - Instance metadata hardened
3. **Encrypted volumes** - EBS encryption at rest
4. **Secrets Manager** - Credentials never in code
5. **Least privilege IAM** - Minimal instance permissions

## Usage with GitHub Workflows

Deploy via the `ad-deploy.yml` workflow:

```bash
# Plan
gh workflow run ad-deploy.yml \
  -f environment=myorg \
  -f regions='["us-east-1"]' \
  -f action=plan

# Apply
gh workflow run ad-deploy.yml \
  -f environment=myorg \
  -f regions='["us-east-1"]' \
  -f action=apply
```

## Managing the Instance

Use the `ad-manage-instance.yml` workflow:

```bash
# Diagnostics
gh workflow run ad-manage-instance.yml \
  -f environment=myorg \
  -f region=us-east-1 \
  -f action=diagnose

# Reset password
gh workflow run ad-manage-instance.yml \
  -f environment=myorg \
  -f region=us-east-1 \
  -f action=reset-password
```

## Connecting via SSM

```bash
# Get the command from terraform output
terraform output ssm_session_command

# Or construct it manually
aws ssm start-session --target i-xxxxxxxxx --region us-east-1
```

## See Also

- [`docs/AD_INFRASTRUCTURE.md`](../../docs/AD_INFRASTRUCTURE.md) - Complete setup guide
- [`.github/workflows/ad-deploy.yml`](../../.github/workflows/ad-deploy.yml) - Deployment workflow
- [`.github/workflows/ad-manage-instance.yml`](../../.github/workflows/ad-manage-instance.yml) - Management workflow
- [`.github/workflows/ad-install-okta-agent.yml`](../../.github/workflows/ad-install-okta-agent.yml) - Agent installation
