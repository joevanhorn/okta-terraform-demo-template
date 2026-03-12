# Active Directory Integration Prompt Template

Use this template to generate Terraform code for Active Directory infrastructure and Okta AD Agent integration.

## Context to Provide

Before using this prompt, gather:
1. AD Domain configuration
2. AWS region and instance requirements
3. OU and group structure needed
4. User provisioning requirements
5. Okta AD Agent settings

## Prompt Template

```
Create Active Directory infrastructure for Okta integration with these specifications:

## Environment
- Environment name: [dev | staging | prod]
- AWS Region: [us-east-1]
- Domain name: [corp.example.com]
- NetBIOS name: [CORP]

## Infrastructure
- Instance type: [t3.medium | t3.large]
- Create new VPC: [yes/no]
- VPC CIDR: [10.0.0.0/16] (if creating new)
- Existing VPC ID: [vpc-xxx] (if using existing)

## AD Structure
Create these Organizational Units:
- [OU path 1, e.g., "Company/Users/Engineering"]
- [OU path 2, e.g., "Company/Users/Sales"]
- [OU path 3, e.g., "Company/Groups"]

Create these Security Groups:
- [Group 1 name and description]
- [Group 2 name and description]

## Sample Users (if needed)
Create [number] sample users with:
- Departments: [Engineering, Sales, Marketing, etc.]
- Titles: [various job titles]
- Group memberships: [which groups to assign]

## Okta AD Agent
- Install agent: [yes/no]
- Okta Org URL: [https://myorg.okta.com]
- Import users: [yes/no]
- Sync direction: [Okta to AD | AD to Okta | Both]

## Security Settings
- Enable RDP: [yes/no]
- RDP allowed CIDRs: [10.0.0.0/8] (if RDP enabled)
- Assign Elastic IP: [yes/no]

Generate complete Terraform code using the ad-domain-controller module.
```

## Example: Demo Environment

```
Create Active Directory infrastructure for Okta integration with these specifications:

## Environment
- Environment name: demo
- AWS Region: us-east-1
- Domain name: corp.demo.local
- NetBIOS name: CORP

## Infrastructure
- Instance type: t3.medium
- Create new VPC: yes
- VPC CIDR: 10.0.0.0/16

## AD Structure
Create these Organizational Units:
- Company/Users/Engineering
- Company/Users/Sales
- Company/Users/Marketing
- Company/Users/Finance
- Company/Users/IT
- Company/Groups
- Company/Service Accounts

Create these Security Groups:
- Engineering: Engineering department members
- Sales: Sales team members
- Marketing: Marketing team members
- Finance: Finance team members
- IT: IT department members
- IT Admins: IT administrators with elevated access
- VPN Users: Users with VPN access
- Salesforce Users: Users with Salesforce access

## Sample Users
Create 20 sample users with:
- Departments: Engineering (5), Sales (4), Marketing (3), Finance (3), IT (5)
- Titles: Various (Manager, Engineer, Analyst, etc.)
- Group memberships: Department group + role-based groups

## Okta AD Agent
- Install agent: yes
- Okta Org URL: https://demo.oktapreview.com

## Security Settings
- Enable RDP: no
- Assign Elastic IP: no

Generate complete Terraform code using the ad-domain-controller module.
```

## Expected Output Structure

```hcl
# =============================================================================
# ACTIVE DIRECTORY DOMAIN CONTROLLER
# =============================================================================
# Deploys AD infrastructure for Okta integration
# =============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }

  backend "s3" {
    bucket         = "okta-terraform-demo"
    key            = "Okta-GitOps/demo/ad-infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region
}

# =============================================================================
# AD DOMAIN CONTROLLER MODULE
# =============================================================================

module "ad_dc" {
  source = "../../../modules/ad-domain-controller"

  environment     = "demo"
  aws_region      = "us-east-1"
  region_short    = "use1"
  ad_domain_name  = "corp.demo.local"
  ad_netbios_name = "CORP"

  # Network
  create_vpc         = true
  vpc_cidr           = "10.0.0.0/16"
  public_subnet_cidr = "10.0.1.0/24"

  # Instance
  instance_type     = "t3.medium"
  root_volume_size  = 100
  assign_elastic_ip = false

  # Security
  enable_rdp = false

  # AD Configuration
  create_sample_users = true

  # Okta Agent (optional)
  okta_org_url     = var.okta_org_url
  okta_agent_token = var.okta_agent_token

  tags = {
    Project = "okta-demo"
    Owner   = "admin@example.com"
  }
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "aws_region" {
  default = "us-east-1"
}

variable "okta_org_url" {
  description = "Okta organization URL"
  default     = ""
}

variable "okta_agent_token" {
  description = "Okta AD Agent registration token"
  sensitive   = true
  default     = ""
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "instance_id" {
  value = module.ad_dc.instance_id
}

output "private_ip" {
  value = module.ad_dc.private_ip
}

output "domain_name" {
  value = module.ad_dc.domain_name
}

output "ssm_session_command" {
  value = module.ad_dc.ssm_start_session_command
}

output "credentials_secret" {
  value     = module.ad_dc.credentials_secret_arn
  sensitive = true
}
```

## Post-Generation Steps

### 1. Deploy Infrastructure

```bash
cd environments/demo/ad-infrastructure
terraform init
terraform plan
terraform apply
```

### 2. Wait for AD Configuration

AD configuration takes 10-15 minutes after instance launch:
- Windows Server boots
- AD DS role installs
- Forest configuration completes
- Sample users created (if enabled)

### 3. Connect via SSM

```bash
# Get SSM session command
terraform output ssm_session_command

# Connect
aws ssm start-session --target i-xxxxxxxxx --region us-east-1
```

### 4. Install Okta AD Agent (if not auto-installed)

```bash
# Via GitHub workflow
gh workflow run ad-install-okta-agent.yml \
  -f environment=demo \
  -f region=us-east-1
```

### 5. Configure Okta Directory Integration

In Okta Admin Console:
1. Go to **Directory > Directory Integrations**
2. Wait for AD Agent to appear
3. Configure import settings
4. Run initial import

## Multi-Region Deployment

Deploy to multiple regions simultaneously:

```bash
gh workflow run ad-deploy.yml \
  -f environment=demo \
  -f regions='["us-east-1", "us-west-2", "eu-west-1"]' \
  -f action=apply
```

Each region gets independent:
- VPC and networking
- AD forest (not replicated)
- State file
- Secrets Manager entry

## Okta AD Agent Configuration Options

### Just-In-Time Provisioning
```hcl
# In Okta, configure:
# - JIT provisioning enabled
# - Profile mapping
# - Group assignments
```

### Scheduled Import
```hcl
# Configure in Okta Admin Console:
# - Import schedule (hourly, daily, etc.)
# - Incremental vs full import
# - Conflict resolution
```

### Password Sync
```hcl
# Requires AD Agent with:
# - Password sync enabled
# - Domain admin credentials
# - Additional firewall rules
```

## See Also

- [docs/AD_INFRASTRUCTURE.md](../../docs/AD_INFRASTRUCTURE.md) - Complete AD guide
- [modules/ad-domain-controller/](../../modules/ad-domain-controller/) - Module documentation
- [deploy_infrastructure.md](deploy_infrastructure.md) - General AWS infrastructure
