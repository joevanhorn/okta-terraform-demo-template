# OPC Agent Deployment

Deploy Okta On-Prem Connector (OPC) agents on AWS EC2 for database connectivity. OPC agents bridge Okta to on-premises databases (PostgreSQL, Oracle, SAP).

## Architecture

```
Okta Tenant ←→ OPC Agent (RHEL 8 EC2) ←→ Database (RDS/On-prem)
                    ↑
              SSM for management
              OPA sftd for PAM access
```

## Quick Start

### 1. Deploy OPC Agents

```bash
cd environments/myorg/opc-infrastructure
cp main.tf.example main.tf
# Edit main.tf: set backend, Okta URL, database host
terraform init && terraform apply
```

### 2. Install Provisioning Agent

```bash
gh workflow run opc-install-agent.yml \
  -f environment=myorg-prod \
  -f target=all \
  -f connector_type=generic-db
```

### 3. Install sftd (Optional - for OPA PAM access)

```bash
gh workflow run opc-install-sftd.yml \
  -f environment=myorg-prod \
  -f target=all \
  -f connector_type=generic-db
```

## Terraform Module

The `modules/opc-agent/` module creates:

- RHEL 8 EC2 instance (from stock AMI or pre-built AMI)
- IAM role with SSM and CloudWatch access
- Instance profile
- Elastic IP for consistent connectivity
- SSM parameters for instance discovery
- User data bootstrap script

### Module Inputs

| Variable | Description | Default |
|----------|-------------|---------|
| `environment` | Environment name | (required) |
| `region_short` | Short region code (use2) | (required) |
| `connector_type` | generic-db, oracle-ebs, or sap | (required) |
| `vpc_id` | VPC for deployment | (required) |
| `subnet_id` | Subnet (public recommended) | (required) |
| `security_group_ids` | Security groups | (required) |
| `okta_org_url` | Okta organization URL | (required) |
| `instance_number` | Agent number (1-10) | `1` |
| `instance_type` | EC2 instance type | `t3.medium` |
| `database_host` | Database hostname | `""` |
| `jdbc_driver_url` | JDBC driver download URL | `""` |
| `custom_ami_id` | Pre-built AMI ID | `""` |
| `use_prebuilt_ami` | Use simplified bootstrap | `false` |
| `opa_enrollment_token` | OPA PAM enrollment token | `""` |

### Multiple Agents (HA)

Use `for_each` for deploying multiple agents:

```hcl
locals {
  opc_agents = {
    "generic-db-1" = { instance_number = 1 }
    "generic-db-2" = { instance_number = 2 }
  }
}

module "opc_agents" {
  source   = "../../../modules/opc-agent"
  for_each = local.opc_agents
  # ... see main.tf.example
}
```

## Pre-built AMI (Faster Deployment)

Build a pre-configured AMI with Packer to speed up OPC agent deployment:

```bash
cd packer/opc-agent
cp variables.pkrvars.hcl.example variables.pkrvars.hcl
# Edit variables
packer build -var-file=variables.pkrvars.hcl opc-agent.pkr.hcl
```

The AMI includes: SSM Agent, Java 11, sftd, curl/wget/nc/jq, and directory structure.

Then reference it in Terraform:

```hcl
module "opc_agent" {
  source           = "../../../modules/opc-agent"
  custom_ami_id    = "ami-xxxxxxxxxx"
  use_prebuilt_ami = true
  # ...
}
```

## Connecting via SSM

OPC agents are managed via AWS Systems Manager (no SSH key required):

```bash
aws ssm start-session --target i-0123456789abcdef0 --region us-east-2
```

## SSM Parameter Paths

Instance details are stored in SSM for discovery:

```
/${environment}/${region_short}/opc/${connector_type}/${instance_number}/instance-id
/${environment}/${region_short}/opc/${connector_type}/${instance_number}/private-ip
```

## Workflows

| Workflow | Purpose |
|----------|---------|
| `opc-deploy.yml` | Deploy/destroy OPC infrastructure via Terraform |
| `opc-install-agent.yml` | Pre-install Okta Provisioning Agent |
| `opc-install-sftd.yml` | Install OPA PAM sftd for server access |

## After Deployment

1. Download the Okta Provisioning Agent RPM from Okta Admin > Settings > Downloads
2. Upload to the OPC server: `scp OktaProvisioningAgent*.rpm ec2-user@<ip>:/installers/opc/`
3. Install: `sudo yum localinstall /installers/opc/OktaProvisioningAgent*.rpm -y`
4. Configure: `sudo /opt/OktaProvisioningAgent/configure_agent.sh`
5. Verify the agent appears in Okta Admin > Settings > Agents
