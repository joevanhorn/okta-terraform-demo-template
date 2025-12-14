# Okta Privileged Access (OPA) Terraform Integration

This guide covers setting up the Okta Privileged Access (OPA) Terraform provider alongside the standard Okta provider in this repository.

## Overview

The Okta PAM Terraform provider (`oktapam`) manages Okta Privileged Access resources separately from the main Okta provider. This includes:

- **Server Access**: Projects, enrollment tokens, gateways
- **Secret Management**: Secret folders and secrets
- **Access Control**: Security policies, groups, project assignments
- **Kubernetes**: Cluster access management
- **Active Directory**: AD connections and user sync

## Prerequisites

1. **Okta Privileged Access License** - OPA must be enabled for your Okta org
2. **OPA Team** - A team configured in Okta Privileged Access
3. **Service User** - A service user account with administrator role(s)

---

## Part 1: Create OPA Service User

### Step 1: Access OPA Admin Console

1. Log into your Okta Admin Console
2. Navigate to **Security** → **Privileged Access**
3. Click **Launch Console** to open the OPA Admin Console

### Step 2: Create Service User

1. In OPA Console, go to **Settings** → **Service Users**
2. Click **Create Service User**
3. Configure:
   - **Name**: `terraform-automation`
   - **Description**: `Service user for Terraform automation`
4. Click **Create**
5. **Save the credentials** - they're shown only once:
   - **Key** (Service User ID)
   - **Secret** (Service User Secret)

### Step 3: Assign Administrator Role

1. Go to **Settings** → **Roles**
2. Select the **PAM Administrator** role (or appropriate role)
3. Add the service user to the role

---

## Part 2: Configure GitHub Secrets

Add these secrets to your GitHub Environment (alongside existing Okta secrets):

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `OKTAPAM_KEY` | Service user key (ID) | `svcuser-abc123...` |
| `OKTAPAM_SECRET` | Service user secret | `secret-xyz789...` |
| `OKTAPAM_TEAM` | OPA team name | `mycompany` |

### Steps:

1. Go to **Settings** → **Environments** → **Your Environment**
2. Click **Add secret**
3. Add each OPA secret

---

## Part 3: Enable Provider in Terraform

### Step 1: Update provider.tf

Uncomment the oktapam provider in `environments/{env}/terraform/provider.tf`:

```hcl
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    okta = {
      source  = "okta/okta"
      version = ">= 6.4.0, < 7.0.0"
    }

    # Uncomment to enable OPA
    oktapam = {
      source  = "okta/oktapam"
      version = ">= 0.6.0"
    }
  }

  # ... backend config
}

# ... okta provider

# Uncomment OPA provider
provider "oktapam" {
  oktapam_key    = var.oktapam_key
  oktapam_secret = var.oktapam_secret
  oktapam_team   = var.oktapam_team
}
```

### Step 2: Update variables.tf

Uncomment the OPA variables in `environments/{env}/terraform/variables.tf`:

```hcl
variable "oktapam_key" {
  description = "OPA service user key (ID)"
  type        = string
  sensitive   = true
}

variable "oktapam_secret" {
  description = "OPA service user secret"
  type        = string
  sensitive   = true
}

variable "oktapam_team" {
  description = "OPA team name"
  type        = string
}
```

### Step 3: Update GitHub Actions Workflow

Update `terraform-plan.yml` and `terraform-apply-with-approval.yml` to pass OPA secrets:

```yaml
- name: Terraform Plan
  env:
    # Existing Okta secrets
    TF_VAR_okta_api_token: ${{ secrets.OKTA_API_TOKEN }}
    TF_VAR_okta_org_name: ${{ secrets.OKTA_ORG_NAME }}
    TF_VAR_okta_base_url: ${{ secrets.OKTA_BASE_URL }}
    # Add OPA secrets
    TF_VAR_oktapam_key: ${{ secrets.OKTAPAM_KEY }}
    TF_VAR_oktapam_secret: ${{ secrets.OKTAPAM_SECRET }}
    TF_VAR_oktapam_team: ${{ secrets.OKTAPAM_TEAM }}
  run: terraform plan
```

---

## Part 4: Create OPA Resources

Copy from the example file and customize:

```bash
# Copy example file
cp environments/myorg/terraform/opa_resources.tf.example \
   environments/myorg/terraform/opa_resources.tf

# Edit and uncomment resources you need
vim environments/myorg/terraform/opa_resources.tf
```

### Common Resource Patterns

#### Basic Resource Group and Project

```hcl
resource "oktapam_resource_group" "production" {
  name        = "Production"
  description = "Production servers"
}

resource "oktapam_resource_group_project" "web_servers" {
  name                 = "Web Servers"
  resource_group       = oktapam_resource_group.production.id
  ssh_certificate_type = "CERT_TYPE_ED25519"
  account_discovery    = true
  create_server_users  = true
}

resource "oktapam_resource_group_server_enrollment_token" "web_token" {
  resource_group = oktapam_resource_group.production.id
  project        = oktapam_resource_group_project.web_servers.id
  description    = "Web server enrollment token"
}
```

#### Secret Management

```hcl
resource "oktapam_secret_folder" "api_keys" {
  name           = "API Keys"
  resource_group = oktapam_resource_group.production.id
  project        = oktapam_resource_group_project.web_servers.id
}

resource "oktapam_secret" "api_key" {
  name           = "external-api-key"
  resource_group = oktapam_resource_group.production.id
  project        = oktapam_resource_group_project.web_servers.id
  parent_folder  = oktapam_secret_folder.api_keys.id

  secret {
    type  = "password"
    value = var.external_api_key
  }
}
```

#### Group Assignment

```hcl
resource "oktapam_group" "developers" {
  name = "Developers"
}

resource "oktapam_project_group" "dev_access" {
  project_name = oktapam_resource_group_project.web_servers.name
  group_name   = oktapam_group.developers.name
  server_admin = false
  server_access = true

  server_account_permissions {
    server_account    = "developer"
    password_checkout = false
  }
}
```

---

## Available Resources

### Resources (Write)

| Resource | Description |
|----------|-------------|
| `oktapam_resource_group` | Top-level organizational unit |
| `oktapam_resource_group_project` | Project within resource group |
| `oktapam_project` | Standalone project |
| `oktapam_server_enrollment_token` | Token for server enrollment |
| `oktapam_resource_group_server_enrollment_token` | Token for RG project |
| `oktapam_gateway_setup_token` | Token for gateway registration |
| `oktapam_group` | OPA group |
| `oktapam_user_group_attachment` | User to group assignment |
| `oktapam_project_group` | Group to project assignment |
| `oktapam_secret_folder` | Secret folder |
| `oktapam_secret` | Secret (password, key, etc.) |
| `oktapam_security_policy` | Security policy (v1, legacy) |
| `oktapam_security_policy_v2` | Security policy (v2, active development) |
| `oktapam_password_settings` | Password rotation settings |
| `oktapam_sudo_command_bundle` | Allowed sudo commands |
| `oktapam_kubernetes_cluster` | K8s cluster |
| `oktapam_kubernetes_cluster_connection` | K8s cluster connection |
| `oktapam_kubernetes_cluster_group` | K8s cluster group assignment |
| `oktapam_ad_connection` | Active Directory connection |
| `oktapam_ad_certificate_object` | AD certificate |
| `oktapam_ad_certificate_request` | AD certificate request |
| `oktapam_ad_task_settings` | AD task configuration |
| `oktapam_ad_user_sync_task_settings` | AD user sync settings |
| `oktapam_team_settings` | Team-wide settings |
| `oktapam_user` | OPA user |

### Data Sources (Read)

| Data Source | Description |
|-------------|-------------|
| `oktapam_resource_groups` | List all resource groups |
| `oktapam_resource_group` | Get specific resource group |
| `oktapam_resource_group_projects` | List projects in RG |
| `oktapam_resource_group_project` | Get specific RG project |
| `oktapam_projects` | List standalone projects |
| `oktapam_project` | Get specific project |
| `oktapam_project_groups` | List project group assignments |
| `oktapam_project_group` | Get specific project group |
| `oktapam_groups` | List OPA groups |
| `oktapam_group` | Get specific group |
| `oktapam_gateways` | List registered gateways |
| `oktapam_gateway_setup_tokens` | List gateway tokens |
| `oktapam_gateway_setup_token` | Get specific gateway token |
| `oktapam_server_enrollment_tokens` | List server tokens |
| `oktapam_server_enrollment_token` | Get specific server token |
| `oktapam_secret_folders` | List secret folders |
| `oktapam_secrets` | List secrets |
| `oktapam_secret` | Get specific secret |
| `oktapam_security_policies` | List security policies |
| `oktapam_security_policy` | Get specific policy |
| `oktapam_password_settings` | Get password settings |
| `oktapam_sudo_command_bundles` | List sudo bundles |
| `oktapam_sudo_command_bundle` | Get specific bundle |
| `oktapam_ad_connections` | List AD connections |
| `oktapam_ad_user_sync_task_settings` | Get AD sync settings |
| `oktapam_ad_user_sync_task_settings_id_list` | List AD sync task IDs |
| `oktapam_team_settings` | Get team settings |
| `oktapam_current_user` | Get current service user info |

---

## Environment Variables

The provider supports authentication via environment variables:

| Variable | Description |
|----------|-------------|
| `OKTAPAM_KEY` | Service user key |
| `OKTAPAM_SECRET` | Service user secret |
| `OKTAPAM_TEAM` | Team name |
| `OKTAPAM_API_HOST` | API host override (non-production) |
| `OKTAPAM_TRUSTED_DOMAIN_OVERRIDE` | Domain override (non-production) |

---

## Important Notes

### Security Policy V2

The `oktapam_security_policy_v2` resource is under active development. Breaking changes may occur. For production, consider using the legacy `oktapam_security_policy` until v2 is stable.

### OPA vs ASA

The provider supports both:
- **Okta Privileged Access (OPA)** - Current product
- **Advanced Server Access (ASA)** - Legacy product

Not all resources apply to both. Check the [provider documentation](https://registry.terraform.io/providers/okta/oktapam/latest/docs) for compatibility.

### State Management

OPA resources use the same S3 backend as Okta resources. State is stored together:
```
s3://okta-terraform-demo/Okta-GitOps/{environment}/terraform.tfstate
```

### Two-Provider Architecture

This repository now supports two Okta providers:

| Provider | Purpose | Resources |
|----------|---------|-----------|
| `okta/okta` | Core Okta | Users, groups, apps, OIG |
| `okta/oktapam` | Privileged Access | Servers, secrets, policies |

Both providers can be used together in the same configuration.

---

## Import Existing OPA Resources

If you have existing OPA resources, use the import script to generate Terraform code:

```bash
# Set credentials
export OKTAPAM_KEY="your-key"
export OKTAPAM_SECRET="your-secret"
export OKTAPAM_TEAM="your-team"

# Preview what will be imported (dry run)
python3 scripts/import_opa_resources.py --dry-run

# Import and generate Terraform files
python3 scripts/import_opa_resources.py --output-dir environments/myorg/terraform

# Review generated files
cat environments/myorg/terraform/opa_resources_imported.tf

# Run import commands
cd environments/myorg/terraform
terraform init
bash opa_import_commands.sh

# Verify state
terraform plan
```

### Generated Files

| File | Description |
|------|-------------|
| `opa_resources_imported.tf` | Terraform configuration for discovered resources |
| `opa_import_commands.sh` | Shell script with terraform import commands |
| `opa_resources_export.json` | JSON export of discovered resources for reference |

---

## GitHub Actions Workflow

A dedicated workflow for OPA resources is available:

```bash
# Manually trigger OPA plan
gh workflow run opa-plan.yml -f environment=myorg
```

The workflow:
- Only runs when `opa_*.tf` files change
- Checks if OPA provider is enabled
- Validates OPA secrets are configured
- Plans only OPA resources (using -target)
- Comments results on PRs

---

## Active Directory Integration

OPA can integrate with Active Directory for:
- **Account Discovery**: Sync AD users to OPA
- **Server Access**: RDP to Windows domain-joined servers
- **Password Management**: Rotate AD service account passwords
- **Session Recording**: Record privileged sessions for compliance

### Prerequisites for AD Integration

1. **OPA Gateway Installed**
   - Deploy gateway on-premises or in cloud with network access to AD
   - Use gateway setup token from Terraform

2. **AD Service Account**
   - Create a service account in AD with read access
   - For password rotation, needs password reset permissions

3. **Network Connectivity**
   - Gateway → AD Domain Controller (LDAP 389/636, Kerberos 88)
   - Gateway → OPA Cloud (HTTPS 443)

### AD Integration Resources

| Resource | Purpose |
|----------|---------|
| `oktapam_gateway_setup_token` | Token to install OPA Gateway |
| `oktapam_ad_connection` | Connect to AD domain |
| `oktapam_ad_user_sync_task_settings` | Sync AD users to OPA |
| `oktapam_ad_task_settings` | Configure account discovery rules |
| `oktapam_ad_certificate_object` | Manage AD certificates |

### Example: AD Connection

```hcl
# Gateway for AD connectivity
resource "oktapam_gateway_setup_token" "ad_gateway" {
  description = "Gateway for Active Directory"
  labels = {
    environment = "production"
    purpose     = "active-directory"
  }
}

# AD Connection
resource "oktapam_ad_connection" "corporate" {
  name                     = "Corporate AD"
  gateway_id               = "GATEWAY_UUID"  # From installed gateway
  domain                   = "corp.example.com"
  service_account_username = var.ad_service_account_username
  service_account_password = var.ad_service_account_password
  use_passwordless         = false
  domain_controllers       = ["dc1.corp.example.com", "dc2.corp.example.com"]
}

# User Sync
resource "oktapam_ad_user_sync_task_settings" "user_sync" {
  connection_id     = oktapam_ad_connection.corporate.id
  name              = "Corporate User Sync"
  is_active         = true
  frequency_seconds = 3600  # Every hour
  base_dn           = "OU=Users,DC=corp,DC=example,DC=com"
  ldap_query_filter = "(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
  sid_field         = "objectSid"
  upn_field         = "userPrincipalName"
}
```

### Example File

See `environments/myorg/terraform/opa_ad_integration.tf.example` for comprehensive AD integration patterns including:

- Resource groups and projects for AD servers
- Server enrollment tokens for domain controllers
- AD connection and user sync configuration
- Security policies for AD server access
- Password rotation settings
- Secret storage for AD credentials

### AD Infrastructure

This repository includes optional AWS infrastructure for deploying an AD domain controller for demos:

```
environments/myorg/infrastructure/
├── ad-domain-controller.tf    # EC2 Windows Server
├── networking.tf              # VPC, subnets, security groups
├── scripts/userdata.ps1       # AD setup automation
└── variables.tf               # Configuration variables
```

Deploy with:
```bash
cd environments/myorg/infrastructure
terraform init
terraform apply -var="admin_password=YourPassword123!" \
                -var="ad_safe_mode_password=YourDSRMPassword123!" \
                -var="okta_org_url=https://your-org.okta.com"
```

---

## References

- [Okta PAM Provider - Terraform Registry](https://registry.terraform.io/providers/okta/oktapam/latest/docs)
- [Provider GitHub Repository](https://github.com/okta/terraform-provider-oktapam)
- [Okta Privileged Access Documentation](https://help.okta.com/en-us/content/topics/privileged-access/pam-overview.htm)
- [Create OPA Service User](https://help.okta.com/en-us/content/topics/privileged-access/pam-service-users.htm)
- [OPA AD Integration Guide](https://help.okta.com/en-us/content/topics/privileged-access/pam-ad-integration.htm)
