# Active Directory Infrastructure Guide

This guide covers deploying and managing Active Directory Domain Controllers on AWS for Okta integration demos.

## Overview

The AD infrastructure module provides:
- **Windows Server 2022** EC2 instance as Domain Controller
- **AWS Systems Manager (SSM)** for secure remote management (no RDP needed)
- **Secrets Manager** for credential storage
- **IAM roles** with least-privilege access
- **VPC infrastructure** (optional - can use existing)
- **Sample users and groups** for demo purposes
- **Okta AD Agent** automated installation

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Region                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                        VPC                                  │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │              Public Subnet                            │  │ │
│  │  │                                                       │  │ │
│  │  │   ┌─────────────────────────────────────────────┐    │  │ │
│  │  │   │         EC2 (Windows Server 2022)           │    │  │ │
│  │  │   │                                             │    │  │ │
│  │  │   │  • AD Domain Services                       │    │  │ │
│  │  │   │  • DNS Server                               │    │  │ │
│  │  │   │  • SSM Agent                                │    │  │ │
│  │  │   │  • Okta AD Agent (optional)                 │    │  │ │
│  │  │   │                                             │    │  │ │
│  │  │   └─────────────────────────────────────────────┘    │  │ │
│  │  │              │                                        │  │ │
│  │  └──────────────│────────────────────────────────────────┘  │ │
│  │                 │                                           │ │
│  │  ┌──────────────┴──────────────────────────────────────────┐│ │
│  │  │ Security Group: DNS, LDAP, Kerberos, SMB, RPC           ││ │
│  │  └─────────────────────────────────────────────────────────┘│ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Secrets Manager │  │ SSM Parameter   │  │   IAM Role      │  │
│  │ (AD Credentials)│  │ Store           │  │ (SSM + Secrets) │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Deploy via GitHub Actions

```bash
# Plan deployment
gh workflow run ad-deploy.yml \
  -f environment=myorg \
  -f regions='["us-east-1"]' \
  -f action=plan

# Apply deployment
gh workflow run ad-deploy.yml \
  -f environment=myorg \
  -f regions='["us-east-1"]' \
  -f action=apply
```

### 2. Deploy via CLI

```bash
cd environments/myorg/ad-infrastructure

# Initialize
terraform init

# Plan
terraform plan \
  -var="aws_region=us-east-1" \
  -var="ad_domain_name=corp.demo.local" \
  -var="ad_netbios_name=CORP"

# Apply
terraform apply \
  -var="aws_region=us-east-1" \
  -var="ad_domain_name=corp.demo.local" \
  -var="ad_netbios_name=CORP"
```

### 3. Connect to Instance

```bash
# Get SSM session command from terraform output
terraform output ssm_session_command

# Start session
aws ssm start-session --target i-xxxxxxxxx --region us-east-1
```

## Multi-Region Deployment

Deploy to multiple regions simultaneously:

```bash
gh workflow run ad-deploy.yml \
  -f environment=myorg \
  -f regions='["us-east-1", "us-west-2", "eu-west-1"]' \
  -f action=apply
```

Each region gets:
- Independent VPC and subnet
- Separate AD forest (not replicated)
- Own Secrets Manager entry
- Individual state file

## GitHub Workflows

### AD - Deploy Domain Controller (`ad-deploy.yml`)

Deploys AD infrastructure to one or more AWS regions.

| Input | Description | Default |
|-------|-------------|---------|
| `environment` | Target environment | `myorg` |
| `regions` | JSON array of AWS regions | `["us-east-1"]` |
| `action` | plan, apply, or destroy | `plan` |
| `ad_domain_name` | AD domain name | `corp.demo.local` |
| `ad_netbios_name` | NetBIOS name | `CORP` |
| `instance_type` | EC2 instance type | `t3.medium` |
| `create_sample_users` | Create demo users | `true` |

### AD - Install Okta Agent (`ad-install-okta-agent.yml`)

Installs Okta AD Agent on deployed domain controllers.

**Prerequisites:**
1. Add `OKTA_AD_AGENT_TOKEN` secret to your GitHub Environment
2. Ensure `OKTA_ORG_URL` secret is set

```bash
gh workflow run ad-install-okta-agent.yml \
  -f environment=myorg \
  -f region=us-east-1
```

### AD - Manage Instance (`ad-manage-instance.yml`)

Manage running AD instances via SSM.

| Action | Description |
|--------|-------------|
| `diagnose` | Run comprehensive diagnostics |
| `reboot` | Reboot the instance |
| `reset-password` | Reset Administrator password |
| `check-services` | List Windows services status |
| `get-users` | List all AD users |
| `get-groups` | List all AD groups |

```bash
# Run diagnostics
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

## Module Reference

### Required Variables

| Variable | Description |
|----------|-------------|
| `environment` | Environment name |
| `aws_region` | AWS region |
| `region_short` | Short region identifier (e.g., use1) |
| `ad_domain_name` | AD domain name (e.g., corp.example.com) |
| `ad_netbios_name` | NetBIOS name (e.g., CORP) |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `create_vpc` | `true` | Create new VPC or use existing |
| `vpc_cidr` | `10.0.0.0/16` | VPC CIDR block |
| `instance_type` | `t3.medium` | EC2 instance type |
| `root_volume_size` | `100` | Root volume size in GB |
| `enable_rdp` | `false` | Enable RDP access |
| `create_sample_users` | `true` | Create demo users/groups |
| `okta_agent_token` | `""` | Okta AD Agent token |
| `okta_org_url` | `""` | Okta org URL |

### Outputs

| Output | Description |
|--------|-------------|
| `instance_id` | EC2 instance ID |
| `private_ip` | Private IP address |
| `public_ip` | Public IP address |
| `credentials_secret_arn` | Secrets Manager ARN |
| `ssm_start_session_command` | SSM session command |

## Sample Users and Groups

When `create_sample_users = true`, the following structure is created:

### Organizational Units
- `Company` (top-level)
  - `Users` → `Engineering`, `Sales`, `Marketing`, `Finance`, `HR`, `IT`, `Executives`
  - `Groups`
  - `Computers`
  - `Service Accounts`

### Groups
**Department Groups:** Engineering, Sales, Marketing, Finance, HR, IT, Executives

**Role Groups:** Managers, Contractors, Remote Workers

**Application Groups:** Salesforce Users, Jira Users, Confluence Users, GitHub Users, AWS Console Users, VPN Users

**Privilege Groups:** IT Admins, Security Team, Help Desk

### Sample Users (22 total)

| Department | Users |
|------------|-------|
| Engineering | jsmith, ejohnson, mwilliams, sbrown, dlee |
| Sales | rwilson, jdavis, tmartin, agarcia |
| Marketing | cmartinez, lrodriguez, kthompson |
| Finance | mwhite, bharris, nclark |
| HR | plewis, jwalker |
| IT | shernandez, ayoung, dking, rscott |
| Executives | cexec, vpresident |

## Okta AD Agent Integration

### Manual Installation

1. Get agent token from Okta Admin Console:
   - Go to **Directory > Directory Integrations**
   - Click **Add Active Directory**
   - Download agent or copy registration token

2. Add secrets to GitHub:
   - `OKTA_AD_AGENT_TOKEN`: Registration token
   - `OKTA_ORG_URL`: Your Okta org URL (e.g., https://myorg.okta.com)

3. Run installation workflow:
   ```bash
   gh workflow run ad-install-okta-agent.yml \
     -f environment=myorg \
     -f region=us-east-1
   ```

### Automatic Installation (during deployment)

Set the variables in your terraform.tfvars:
```hcl
okta_org_url     = "https://myorg.okta.com"
okta_agent_token = "your-agent-registration-token"
```

Or pass them to the deployment workflow:
```bash
gh workflow run ad-deploy.yml \
  -f environment=myorg \
  -f regions='["us-east-1"]' \
  -f action=apply \
  -f okta_org_url="https://myorg.okta.com"
# Note: Token should be stored in GitHub Secrets
```

## Troubleshooting

### Instance won't connect via SSM

1. Check instance state:
   ```bash
   aws ec2 describe-instances --instance-ids i-xxx --query 'Reservations[0].Instances[0].State.Name'
   ```

2. Verify SSM agent status:
   ```bash
   aws ssm describe-instance-information --filters "Key=InstanceIds,Values=i-xxx"
   ```

3. Check IAM role is attached and has SSM permissions

### AD Services not starting

1. Run diagnostics:
   ```bash
   gh workflow run ad-manage-instance.yml -f action=diagnose
   ```

2. Check event logs in diagnostics output

3. Verify sufficient disk space

### Okta Agent not connecting

1. Verify agent service is running:
   ```bash
   gh workflow run ad-manage-instance.yml -f action=check-services
   ```

2. Check network connectivity to Okta (outbound 443)

3. Verify agent token is valid and not expired

### Password issues

Reset the Administrator password:
```bash
gh workflow run ad-manage-instance.yml \
  -f environment=myorg \
  -f region=us-east-1 \
  -f action=reset-password
```

New password will be stored in Secrets Manager.

## Security Considerations

1. **No RDP by default**: Use SSM for secure access
2. **IMDSv2 required**: Instance metadata service hardened
3. **Encrypted volumes**: EBS volumes encrypted at rest
4. **Secrets Manager**: Credentials never stored in code
5. **Least privilege IAM**: Instance role has minimal permissions
6. **Security group**: Only necessary AD ports open within VPC

### Enabling RDP (not recommended)

If you must enable RDP:
```hcl
enable_rdp        = true
rdp_allowed_cidrs = ["10.0.0.0/8"]  # Restrict to VPN/internal
```

## Cost Optimization

- **t3.medium**: ~$30/month (sufficient for demos)
- **Stop when not in use**: EC2 costs are hourly
- **Use Elastic IP only if needed**: Small monthly cost when not attached
- **Clean up old deployments**: Destroy when demo is complete

```bash
# Destroy infrastructure
gh workflow run ad-deploy.yml \
  -f environment=myorg \
  -f regions='["us-east-1"]' \
  -f action=destroy
```
