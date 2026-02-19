# Okta Privileged Access (OPA) Integration

Deploy and manage Okta Privileged Access resources via Terraform and GitHub Actions workflows. OPA provides server access, secret management, security policies, and gateway deployment.

## Architecture

```
Okta Tenant → OPA Console → Enrolled Servers (Linux/Windows)
                   ↑
           OPA Gateway (optional, for private subnets)
                   ↑
         sftd agent on each server
```

## Quick Start

### 1. Create OPA Service User

1. Okta Admin → Security → Privileged Access → Launch Console
2. Settings → Service Users → Create Service User
   - Name: `terraform-automation`
3. Save the **Key** and **Secret** (shown only once)
4. Settings → Roles → Add service user to **PAM Administrator**

### 2. Configure GitHub Secrets

Add to your GitHub Environment (alongside existing Okta secrets):

| Secret | Description |
|--------|-------------|
| `OKTAPAM_KEY` | Service user key (ID) |
| `OKTAPAM_SECRET` | Service user secret |
| `OKTAPAM_TEAM` | OPA team name |
| `OKTAPAM_API_HOST` | API host (optional, for non-production) |

### 3. Enable Provider in Terraform

Uncomment the oktapam provider in `provider.tf`:

```hcl
terraform {
  required_providers {
    oktapam = {
      source  = "okta/oktapam"
      version = ">= 0.6.0"
    }
  }
}

provider "oktapam" {
  oktapam_key    = var.oktapam_key
  oktapam_secret = var.oktapam_secret
  oktapam_team   = var.oktapam_team
}
```

Uncomment the OPA variables in `variables.tf`:

```hcl
variable "oktapam_key" {
  type      = string
  sensitive = true
}
variable "oktapam_secret" {
  type      = string
  sensitive = true
}
variable "oktapam_team" {
  type = string
}
```

### 4. Create OPA Resources

```bash
# Copy example and customize
cp environments/myorg/terraform/opa_resources.tf.example \
   environments/myorg/terraform/opa_resources.tf

# For security policies with tiered sudo bundles
cp environments/myorg/terraform/opa_security_policies.tf.example \
   environments/myorg/terraform/opa_security_policies.tf

# Plan and apply
gh workflow run opa-plan.yml -f environment=myorg
gh workflow run opa-apply.yml -f environment=myorg
```

## Workflows

| Workflow | Purpose |
|----------|---------|
| `opa-plan.yml` | Plan OPA resources (auto on PR, manual dispatch) |
| `opa-apply.yml` | Apply OPA resources |
| `opa-test.yml` | Test OPA provider connectivity |
| `opa-discover.yml` | List all OPA resources via API |
| `opa-deploy-gateway.yml` | Deploy OPA gateway EC2 instance |
| `opa-install-agents.yml` | Install sftd on AD DC, SCIM, or OPC servers |
| `opa-state-cleanup.yml` | Remove OPA entries from Terraform state |

### Usage Examples

```bash
# Plan OPA changes
gh workflow run opa-plan.yml -f environment=myorg

# Apply OPA resources
gh workflow run opa-apply.yml -f environment=myorg

# Test connectivity
gh workflow run opa-test.yml -f environment=myorg

# Discover existing OPA resources
gh workflow run opa-discover.yml -f environment=myorg

# Deploy OPA gateway
gh workflow run opa-deploy-gateway.yml \
  -f environment=myorg \
  -f action=apply

# Install OPA agent on servers
gh workflow run opa-install-agents.yml \
  -f environment=myorg \
  -f target=all  # or ad-dc, scim-server, opc-agents

# Clean up OPA state (does NOT destroy resources)
gh workflow run opa-state-cleanup.yml -f environment=myorg
```

## Security Policies (Tiered Access)

The `opa_security_policies.tf.example` file provides a production-tested tiered access pattern:

| Policy | Group | Privileges |
|--------|-------|------------|
| Read-Only-Server-Access | PAM-ReadOnly-Users | View logs, status, processes |
| Operator-Server-Access | PAM-Operators | Restart services, security updates |
| Database-Admin-Access | PAM-Database-Admins | DB tools + password checkout (root/postgres/oracle) |
| Full-Admin-Access | PAM_ADMINISTRATORS | Full admin + password checkout |

### Sudo Command Bundles

| Bundle | Commands |
|--------|----------|
| Read-Only-Operations | tail, less, cat (logs), systemctl status, journalctl, df, free, ps, top, ss, netstat |
| Operator-Operations | systemctl restart/reload, rm (tmp), dnf security updates, sftd/SSM management |
| Admin-Operations | Full systemctl, dnf/yum/rpm, useradd/usermod/passwd, chmod/chown, ip/iptables, vi/vim/nano, reboot |
| Database-Operations | psql, pg_dump, pg_restore, mysql, mysqldump, service management |

## Critical Gotchas

### 1. `type = "default"` Required

All `security_policy_v2` resources **must** include `type = "default"`:

```hcl
resource "oktapam_security_policy_v2" "example" {
  type = "default"  # REQUIRED - prevents state drift
  name = "My Policy"
  # ...
}
```

### 2. Rule Ordering: Password Checkout Before SSH

Password checkout rules **must come before** SSH rules to match the order returned by the OPA API:

```hcl
rules = [
  # Rule 1: Password checkout FIRST
  {
    name = "password-checkout"
    # ...
    privileges = [
      { password_checkout_ssh = { password_checkout_ssh = true } },
    ]
  },
  # Rule 2: SSH access SECOND
  {
    name = "ssh-access"
    # ...
    privileges = [
      { principal_account_ssh = { principal_account_ssh = true } }
    ]
  },
]
```

### 3. `admin_level_permissions` vs `sudo_command_bundles`

These **cannot coexist** in the same privilege block:

```hcl
# WRONG - will cause errors
privileges = [{
  principal_account_ssh = {
    admin_level_permissions = true
    sudo_command_bundles   = [bundle.id]  # CAN'T USE BOTH
  }
}]

# CORRECT - admin implies full sudo
privileges = [{
  principal_account_ssh = {
    principal_account_ssh   = true
    admin_level_permissions = true
  }
}]
```

### 4. `password_checkout_ssh` Requires Username Selector

```hcl
# Password checkout needs specific usernames
server_label = {
  account_selector_type = "username"
  account_selector = {
    usernames = ["root", "postgres", "oracle"]
  }
  # ...
}
```

### 5. OKTAPAM_API_HOST for Non-Production

If using `oktapreview.com`, set `OKTAPAM_API_HOST` as a GitHub secret. The default (`app.scaleft.com`) only works for production OPA tenants.

### 6. Group Assignments for Resource Group Projects

`oktapam_project_group` only works with regular ASA projects, **not** resource group projects. For resource group projects, assign groups manually in the OPA Console:

1. OPA Console → Resources → Your Resource Group
2. Select project → Groups tab
3. Add group with server_admin and server_access permissions

## Common Resource Patterns

### Resource Group + Project + Enrollment Token

```hcl
resource "oktapam_resource_group" "servers" {
  name        = "My-Servers"
  description = "Server access management"
}

resource "oktapam_resource_group_project" "linux" {
  name                 = "Linux-Servers"
  resource_group       = oktapam_resource_group.servers.id
  ssh_certificate_type = "CERT_TYPE_ED25519_01"
  account_discovery    = true
}

resource "oktapam_resource_group_server_enrollment_token" "token" {
  resource_group = oktapam_resource_group.servers.id
  project        = oktapam_resource_group_project.linux.id
  description    = "Server enrollment token"
}

output "opa_enrollment_token" {
  value     = oktapam_resource_group_server_enrollment_token.token.token_value
  sensitive = true
}
```

### Gateway Setup Token

```hcl
resource "oktapam_gateway_setup_token" "gw" {
  resource_group = oktapam_resource_group.servers.id
  description    = "Gateway for private subnet access"
  labels = {
    environment = var.environment
    region      = var.aws_region
  }
}

output "opa_gateway_token" {
  value     = oktapam_gateway_setup_token.gw.token
  sensitive = true
}
```

### Secret Folder

```hcl
resource "oktapam_secret_folder" "credentials" {
  name           = "Database-Credentials"
  resource_group = oktapam_resource_group.servers.id
  project        = oktapam_resource_group_project.linux.id
}
```

## Server Enrollment

After creating enrollment tokens via Terraform, enroll servers:

### Linux (sftd)

```bash
# Install sftd
rpm --import https://dist.scaleft.com/GPG-KEY-OktaPAM-2023
# Add yum repo, then:
dnf install -y scaleft-server-tools

# Enroll
mkdir -p /var/lib/sftd
echo "YOUR_TOKEN" > /var/lib/sftd/enrollment.token
systemctl enable --now sftd
```

### Windows (ScaleFT Server Tools)

```powershell
# Download and install MSI
Invoke-WebRequest -Uri "https://dist.scaleft.com/repos/windows/stable/amd64/server-tools/v1.99.5/ScaleFT-Server-Tools-1.99.5.msi" -OutFile agent.msi
msiexec /i agent.msi /quiet

# Enroll
New-Item -Path "C:\Windows\System32\config\systemprofile\AppData\Local\scaleft" -ItemType Directory -Force
Set-Content -Path "...\scaleft\enrollment.token" -Value "YOUR_TOKEN"
Start-Service "ScaleFT Server Agent"
```

Or use the `opa-install-agents.yml` workflow to automate via SSM.

## Two-Provider Architecture

| Provider | Purpose | Resources |
|----------|---------|-----------|
| `okta/okta` | Core Okta | Users, groups, apps, OIG |
| `okta/oktapam` | Privileged Access | Servers, secrets, policies |

Both providers share the same S3 backend state. OPA resources are in `opa_*.tf` files for easy identification.

## References

- [Okta PAM Provider - Terraform Registry](https://registry.terraform.io/providers/okta/oktapam/latest/docs)
- [Okta Privileged Access Documentation](https://help.okta.com/en-us/content/topics/privileged-access/pam-overview.htm)
- [Create OPA Service User](https://help.okta.com/en-us/content/topics/privileged-access/pam-service-users.htm)
