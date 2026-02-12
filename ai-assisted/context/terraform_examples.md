# Terraform Examples for AI Generation

This document provides example patterns for generating Okta Terraform resources.

## User Examples

### Basic User
```hcl
resource "okta_user" "john_doe" {
  email      = "john.doe@example.com"
  first_name = "John"
  last_name  = "Doe"
  login      = "john.doe@example.com"
  status     = "ACTIVE"
}
```

### User with Department and Manager
```hcl
resource "okta_user" "jane_smith" {
  email        = "jane.smith@example.com"
  first_name   = "Jane"
  last_name    = "Smith"
  login        = "jane.smith@example.com"
  department   = "Engineering"
  title        = "Senior Engineer"
  manager_id   = okta_user.john_doe.id
  status       = "ACTIVE"
}
```

### User with Custom Attributes
```hcl
resource "okta_user" "bob_jones" {
  email      = "bob.jones@example.com"
  first_name = "Bob"
  last_name  = "Jones"
  login      = "bob.jones@example.com"
  department = "Sales"

  custom_profile_attributes = jsonencode({
    "employeeNumber" = "12345"
    "costCenter"     = "SALES-001"
  })

  status = "ACTIVE"
}
```

### Bulk User Management with CSV (1000+ Users)

For large-scale user management, use CSV-based import with for_each:

**CSV Format (`users.csv`):**
```csv
email,first_name,last_name,login,status,department,title,manager_email,groups,custom_profile_attributes
alice@example.com,Alice,Chen,alice@example.com,ACTIVE,Executive,CEO,,"Executive,Leadership","{""employeeNumber"":""E0001""}"
bob@example.com,Bob,Smith,bob@example.com,ACTIVE,Engineering,Developer,alice@example.com,"Engineering,Developers","{""employeeNumber"":""E0010""}"
```

**Terraform Implementation:**
```hcl
# Load and transform CSV data
locals {
  csv_users_raw = csvdecode(file("${path.module}/users.csv"))
  csv_users_filtered = [
    for user in local.csv_users_raw : user
    if !startswith(user.email, "#")  # Skip comment rows
  ]
  csv_users = {
    for user in local.csv_users_filtered : user.email => {
      email         = user.email
      first_name    = user.first_name
      last_name     = user.last_name
      login         = user.login
      status        = coalesce(trimspace(user.status), "ACTIVE")
      department    = trimspace(try(user.department, ""))
      title         = trimspace(try(user.title, ""))
      manager_email = trimspace(try(user.manager_email, ""))
      groups        = trimspace(try(user.groups, ""))
    }
  }
  user_email_to_id = { for email, user in okta_user.csv_users : email => user.id }
  user_groups = {
    for email, user in local.csv_users : email => (
      user.groups != "" ? [for g in split(",", user.groups) : trimspace(g)] : []
    )
  }
  users_by_manager = {
    for email, user in local.csv_users : user.manager_email => email...
    if user.manager_email != ""
  }
}

# Create users (Phase 1 - without manager)
resource "okta_user" "csv_users" {
  for_each   = local.csv_users
  email      = each.value.email
  first_name = each.value.first_name
  last_name  = each.value.last_name
  login      = each.value.login
  status     = each.value.status
  department = each.value.department != "" ? each.value.department : null
  title      = each.value.title != "" ? each.value.title : null

  lifecycle { ignore_changes = [manager_id] }
}

# Manager relationships (Phase 2 - after users exist)
resource "okta_link_value" "manager_subordinates" {
  for_each        = local.users_by_manager
  primary_user_id = lookup(local.user_email_to_id, each.key, null)
  primary_name    = "manager"
  associated_user_ids = [
    for email in each.value : lookup(local.user_email_to_id, email, null)
    if lookup(local.user_email_to_id, email, null) != null
  ]
  depends_on = [okta_user.csv_users]
}
```

**Key Points:**
- Two-phase approach: create users first, then establish manager relationships via `okta_link_value`
- Manager by email reference avoids circular dependency issues
- Groups can be parsed from comma-separated column
- Use `terraform apply -parallelism=10` for 1000+ users
- See `environments/myorg/terraform/users_from_csv.tf.example` for complete implementation

## Group Examples

### Basic Group
```hcl
resource "okta_group" "engineering" {
  name        = "Engineering Team"
  description = "All engineering department members"
}
```

### Group with Members
```hcl
resource "okta_group" "marketing" {
  name        = "Marketing Team"
  description = "Marketing department members"
}

resource "okta_group_memberships" "marketing_members" {
  group_id = okta_group.marketing.id
  users = [
    okta_user.jane_smith.id,
    okta_user.bob_jones.id,
  ]
}
```

## Application Examples

### OAuth 2.0 Web Application
```hcl
resource "okta_app_oauth" "example_web_app" {
  label                      = "Example Web Application"
  type                       = "web"
  grant_types                = ["authorization_code", "refresh_token"]
  redirect_uris              = ["https://app.example.com/callback"]
  post_logout_redirect_uris  = ["https://app.example.com/logout"]
  response_types             = ["code"]

  # Client authentication
  token_endpoint_auth_method = "client_secret_post"

  # PKCE (recommended for security)
  pkce_required              = true

  # Additional settings
  client_uri                 = "https://app.example.com"
  logo_uri                   = "https://app.example.com/logo.png"

  # Login settings
  login_mode                 = "DISABLED"

  # Hide from end user dashboard
  hide_ios                   = true
  hide_web                   = true

  # User name template (IMPORTANT: Use $$ to escape)
  user_name_template         = "$${source.login}"
  user_name_template_type    = "BUILT_IN"
}
```

### Single Page Application (SPA)
```hcl
resource "okta_app_oauth" "example_spa" {
  label                      = "Example SPA"
  type                       = "browser"
  grant_types                = ["authorization_code"]
  redirect_uris              = ["http://localhost:3000/callback"]
  response_types             = ["code"]

  # SPAs must use PKCE
  pkce_required              = true

  # Public client (no client secret)
  token_endpoint_auth_method = "none"

  client_uri                 = "http://localhost:3000"
  login_mode                 = "DISABLED"
  hide_ios                   = true
  hide_web                   = true

  user_name_template         = "$${source.login}"
  user_name_template_type    = "BUILT_IN"
}
```

### Application with Group Assignment
```hcl
resource "okta_app_oauth" "salesforce" {
  label          = "Salesforce"
  type           = "web"
  grant_types    = ["authorization_code", "refresh_token"]
  redirect_uris  = ["https://login.salesforce.com/services/oauth2/callback"]
  response_types = ["code"]

  pkce_required              = true
  token_endpoint_auth_method = "client_secret_post"
  login_mode                 = "DISABLED"
  hide_ios                   = true
  hide_web                   = true

  user_name_template         = "$${source.login}"
  user_name_template_type    = "BUILT_IN"
}

resource "okta_app_group_assignment" "salesforce_marketing" {
  app_id   = okta_app_oauth.salesforce.id
  group_id = okta_group.marketing.id
}
```

## OIG Examples

### Entitlement (Application-Level Access Rights)

**IMPORTANT:** Values MUST be in alphabetical order by `external_value`. Okta API returns values sorted alphabetically, and the provider compares by index position.

```hcl
resource "okta_entitlement" "app_accounts" {
  app_id         = okta_app_oauth.money_movement.id
  key            = "accounts"
  type           = "array<string>"
  display_name   = "Account Access"

  # Values in alphabetical order by external_value
  values {
    value          = "CASH MANAGEMENT II"
    external_value = "26DEMO14"
  }
  values {
    value          = "CASH MANAGEMENT III"
    external_value = "26DEMO26"
  }
  values {
    value          = "ANCHOR CHECKING II"
    external_value = "DEMO38"
  }
  values {
    value          = "INTEREST CHECKING"
    external_value = "DEMO42"
  }
}

# For yes/no entitlements, "no" comes before "yes" alphabetically
resource "okta_entitlement" "app_permission" {
  app_id         = okta_app_oauth.money_movement.id
  key            = "canApprove"
  type           = "string"
  display_name   = "Can Approve"

  values {
    value          = "No"
    external_value = "no"
  }
  values {
    value          = "Yes"
    external_value = "yes"
  }
}
```

### Entitlement Bundle (Basic)
```hcl
resource "okta_entitlement_bundle" "marketing_tools" {
  name        = "Marketing Tools Bundle"
  description = "Access to all marketing applications and resources"
  status      = "ACTIVE"
}
```

### Entitlement Bundle with Dynamic Value Lookups (Recommended)

**IMPORTANT:** Entitlement bundles require Okta-generated value IDs, not external_value strings.
Use dynamic blocks with for expressions to look up value IDs:

```hcl
# Define account groupings in locals for reusability
locals {
  standard_accounts = ["DEMO38", "26DEMO26", "26DEMO14", "DEMO42"]
  limited_accounts  = ["DEMO38", "DEMO42"]
  all_accounts      = ["DEMO38", "26DEMO26", "26DEMO14", "DEMO2", "149259"]
}

# Bundle using dynamic lookup
resource "okta_entitlement_bundle" "standard_access" {
  name        = "Standard Access Bundle"
  description = "Standard 4-account access for most users"
  status      = "ACTIVE"

  target {
    external_id = okta_app_oauth.money_movement.id
    type        = "APPLICATION"
  }

  entitlements {
    id = okta_entitlement.app_accounts.id
    dynamic "values" {
      for_each = [
        for v in okta_entitlement.app_accounts.values : v.id
        if contains(local.standard_accounts, v.external_value)
      ]
      content {
        id = values.value
      }
    }
  }
}
```

**Key points:**
- `values` is a **block type**, not an argument - use `dynamic "values"` not `values = [...]`
- The `for` expression filters values by `external_value` and returns the Okta-generated `id`
- This creates proper resource dependencies so bundles can be created in the same apply as entitlements

### Access Review Campaign
```hcl
resource "okta_reviews" "quarterly_access_review" {
  name        = "Quarterly Access Review - Q1 2025"
  description = "Review user access to all applications"

  # Review schedule
  start_date  = "2025-01-01T00:00:00Z"
  end_date    = "2025-01-31T23:59:59Z"

  # Review type
  review_type = "USER_ACCESS_REVIEW"

  # Reviewers
  reviewer_type = "MANAGER"
}
```

## Authorization Server Examples

### Custom Authorization Server
```hcl
resource "okta_auth_server" "example" {
  name        = "Example Auth Server"
  description = "Authorization server for example APIs"
  audiences   = ["api://example"]

  # Optional: Set as issuer
  issuer_mode = "CUSTOM_URL"
}

resource "okta_auth_server_scope" "read" {
  auth_server_id = okta_auth_server.example.id
  name           = "read:data"
  description    = "Read access to data"
  consent        = "REQUIRED"
}

resource "okta_auth_server_claim" "email" {
  auth_server_id = okta_auth_server.example.id
  name           = "email"
  value          = "user.email"
  claim_type     = "RESOURCE"

  scopes = [
    okta_auth_server_scope.read.name,
  ]
}
```

## Policy Examples

### MFA Policy
```hcl
resource "okta_policy_mfa" "example" {
  name        = "Example MFA Policy"
  status      = "ACTIVE"
  description = "Require MFA for all users"

  groups_included = [
    okta_group.engineering.id,
  ]
}

resource "okta_policy_rule_mfa" "require_mfa" {
  policy_id = okta_policy_mfa.example.id
  name      = "Require MFA"
  status    = "ACTIVE"

  enroll = "REQUIRED"
}
```

## Infrastructure Examples (AWS)

**Important:** These go in `environments/{env}/infrastructure/`, NOT `terraform/` directory.

### VPC and Networking
```hcl
# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "okta-ad-vpc"
    Environment = var.environment_name
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "okta-ad-igw"
    Environment = var.environment_name
  }
}

# Public Subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name        = "okta-ad-public-subnet"
    Environment = var.environment_name
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "okta-ad-public-rt"
    Environment = var.environment_name
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}
```

### Security Group (Active Directory Ports)
```hcl
resource "aws_security_group" "domain_controller" {
  name        = "okta-ad-dc-sg"
  description = "Security group for Active Directory Domain Controller"
  vpc_id      = aws_vpc.main.id

  # RDP
  ingress {
    description = "RDP"
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = var.allowed_rdp_cidrs
  }

  # DNS TCP/UDP
  ingress {
    description = "DNS TCP"
    from_port   = 53
    to_port     = 53
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "DNS UDP"
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Kerberos TCP/UDP
  ingress {
    description = "Kerberos TCP"
    from_port   = 88
    to_port     = 88
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Kerberos UDP"
    from_port   = 88
    to_port     = 88
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # LDAP TCP/UDP
  ingress {
    description = "LDAP TCP"
    from_port   = 389
    to_port     = 389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "LDAP UDP"
    from_port   = 389
    to_port     = 389
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SMB/CIFS
  ingress {
    description = "SMB"
    from_port   = 445
    to_port     = 445
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # LDAPS
  ingress {
    description = "LDAPS"
    from_port   = 636
    to_port     = 636
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Dynamic RPC (required for AD)
  ingress {
    description = "Dynamic RPC"
    from_port   = 49152
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound (allow all)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "okta-ad-dc-sg"
    Environment = var.environment_name
  }
}
```

### Domain Controller EC2 Instance
```hcl
# Data source for Windows Server 2022 AMI
data "aws_ami" "windows_2022" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["Windows_Server-2022-English-Full-Base-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Domain Controller Instance
resource "aws_instance" "domain_controller" {
  ami           = data.aws_ami.windows_2022.id
  instance_type = var.dc_instance_type
  subnet_id     = aws_subnet.public.id

  vpc_security_group_ids = [
    aws_security_group.domain_controller.id
  ]

  # User data for automated setup
  user_data = templatefile("${path.module}/scripts/userdata.ps1", {
    admin_password        = var.admin_password
    ad_domain_name        = var.ad_domain_name
    ad_netbios_name       = var.ad_netbios_name
    ad_safe_mode_password = var.ad_safe_mode_password
    okta_org_url          = var.okta_org_url
    environment_name      = var.environment_name
  })

  # IMDSv2 for enhanced security
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  # Ignore AMI and user_data changes
  lifecycle {
    ignore_changes = [ami, user_data]
  }

  tags = {
    Name        = "${var.ad_netbios_name}-DC01"
    Environment = var.environment_name
    Role        = "Domain Controller"
  }
}

# Elastic IP
resource "aws_eip" "dc" {
  instance = aws_instance.domain_controller.id
  domain   = "vpc"

  tags = {
    Name        = "okta-ad-dc-eip"
    Environment = var.environment_name
  }
}
```

### Infrastructure Variables
```hcl
variable "environment_name" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "ad_domain_name" {
  description = "Active Directory domain name (e.g., demo.local)"
  type        = string
  default     = "demo.local"
}

variable "ad_netbios_name" {
  description = "Active Directory NetBIOS name (e.g., DEMO)"
  type        = string
  default     = "DEMO"
}

variable "admin_password" {
  description = "Administrator password for Windows Server"
  type        = string
  sensitive   = true
}

variable "ad_safe_mode_password" {
  description = "Active Directory Safe Mode password"
  type        = string
  sensitive   = true
}

variable "okta_org_url" {
  description = "Okta organization URL for AD Agent download"
  type        = string
}

variable "dc_instance_type" {
  description = "EC2 instance type for Domain Controller"
  type        = string
  default     = "t3.medium"
}

variable "allowed_rdp_cidrs" {
  description = "CIDR blocks allowed for RDP access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
```

### Infrastructure Outputs
```hcl
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "dc_instance_id" {
  description = "Domain Controller instance ID"
  value       = aws_instance.domain_controller.id
}

output "dc_public_ip" {
  description = "Domain Controller public IP"
  value       = aws_eip.dc.public_ip
}

output "dc_private_ip" {
  description = "Domain Controller private IP"
  value       = aws_instance.domain_controller.private_ip
}

output "ad_domain_name" {
  description = "Active Directory domain name"
  value       = var.ad_domain_name
}

output "rdp_connection_string" {
  description = "RDP connection string"
  value       = "mstsc /v:${aws_eip.dc.public_ip} (Username: Administrator)"
}

output "next_steps" {
  description = "Next steps after deployment"
  value       = <<-EOT
    Deployment complete! Next steps:

    1. Wait 15-20 minutes for automated setup
    2. Connect via RDP: ${aws_eip.dc.public_ip}
    3. Username: Administrator
    4. Password: <value from admin_password variable>
    5. Check setup logs: C:\Terraform\bootstrap.log
    6. Install Okta AD Agent: C:\Terraform\OktaADAgentSetup.exe
    7. Configure Okta AD integration in Admin Console
  EOT
}
```

### AWS Provider Configuration

> **IMPORTANT: S3 Bucket Names Must Be Globally Unique**
>
> S3 bucket names are globally unique across ALL AWS accounts worldwide. Replace the example bucket name below with your organization's unique bucket name.

```hcl
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # S3 backend for state storage
  # NOTE: Replace bucket name with your own globally unique name!
  backend "s3" {
    bucket         = "okta-terraform-<your-org-name>"  # MUST be globally unique!
    key            = "Okta-GitOps/production/infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Okta-Active-Directory"
      Environment = var.environment_name
      ManagedBy   = "Terraform"
    }
  }
}
```

## Okta Privileged Access (OPA) Examples

**Provider:** `okta/oktapam` (separate from `okta/okta`)
**Setup:** See `docs/OPA_SETUP.md`

### OPA Provider Configuration
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

### Resource Group and Project
```hcl
# Resource Group - top-level container
resource "oktapam_resource_group" "production" {
  name        = "Production"
  description = "Production environment servers"
}

# Project within resource group
resource "oktapam_resource_group_project" "web_servers" {
  name                 = "Web Servers"
  resource_group       = oktapam_resource_group.production.id
  ssh_certificate_type = "CERT_TYPE_ED25519"
  account_discovery    = true
  create_server_users  = true
}

# Server enrollment token
resource "oktapam_resource_group_server_enrollment_token" "web_token" {
  resource_group = oktapam_resource_group.production.id
  project        = oktapam_resource_group_project.web_servers.id
  description    = "Web server enrollment token"
}
```

### Secret Folder and Secret
```hcl
resource "oktapam_secret_folder" "api_keys" {
  name           = "API Keys"
  description    = "Application API keys"
  resource_group = oktapam_resource_group.production.id
  project        = oktapam_resource_group_project.web_servers.id
}

resource "oktapam_secret" "db_password" {
  name           = "database-password"
  description    = "Production database password"
  resource_group = oktapam_resource_group.production.id
  project        = oktapam_resource_group_project.web_servers.id
  parent_folder  = oktapam_secret_folder.api_keys.id

  secret {
    type  = "password"
    value = var.db_password
  }
}
```

### OPA Groups and Project Access
```hcl
resource "oktapam_group" "developers" {
  name = "Developers"
}

resource "oktapam_project_group" "dev_access" {
  project_name        = oktapam_resource_group_project.web_servers.name
  group_name          = oktapam_group.developers.name
  server_admin        = false
  server_access       = true
  create_server_group = true

  server_account_permissions {
    server_account    = "developer"
    password_checkout = false
  }
}
```

### Gateway Setup Token
```hcl
resource "oktapam_gateway_setup_token" "datacenter" {
  description = "Datacenter gateway"
  labels = {
    environment = "production"
  }
}
```

## Best Practices

### 1. Always Use Status = "ACTIVE"
For production-ready resources, set status to "ACTIVE".

### 2. Escape Template Strings
Always use `$${...}` for Okta template expressions:
```hcl
user_name_template = "$${source.login}"  # Correct
user_name_template = "${source.login}"   # WRONG - Terraform will try to interpolate
```

### 3. Use Descriptive Resource Names
```hcl
# Good
resource "okta_user" "engineering_manager_jane" { ... }

# Less clear
resource "okta_user" "user1" { ... }
```

### 4. Add Comments
```hcl
# Marketing team Salesforce integration
resource "okta_app_oauth" "marketing_salesforce" {
  label = "Salesforce - Marketing"
  # ... configuration
}
```

### 5. Group Related Resources
Keep users, groups, and their memberships together in the same file or adjacent files.

### 6. Use Dependencies When Needed
```hcl
resource "okta_group_memberships" "example" {
  depends_on = [
    okta_user.john_doe,
    okta_user.jane_smith,
  ]
  # ...
}
```

## Common Attributes Reference

### User Attributes
- `email` (required)
- `first_name` (required)
- `last_name` (required)
- `login` (required)
- `status` (optional: "ACTIVE", "STAGED", "DEPROVISIONED")
- `department`
- `title`
- `manager_id`
- `city`
- `state`
- `country_code`
- `mobile_phone`
- `custom_profile_attributes` (JSON string)

### Group Attributes
- `name` (required)
- `description`
- `skip_users` (optional: set to true if managing memberships separately)

### OAuth App Attributes
- `label` (required)
- `type` (required: "web", "browser", "native", "service")
- `grant_types` (required: array)
- `redirect_uris` (required for most types)
- `response_types` (required: array)
- `token_endpoint_auth_method`
- `pkce_required` (boolean)
- `client_uri`
- `logo_uri`
- `login_mode`
- `hide_ios`
- `hide_web`
- `user_name_template`
- `user_name_template_type`
