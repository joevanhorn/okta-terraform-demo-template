# Quick Reference for Okta Terraform Code Generation

This condensed reference provides the most critical patterns and examples for generating Okta Terraform code. Use this as your knowledge base when creating a Gemini Gem.

---

## Critical Rules (Never Forget)

1. **Template strings:** Always use `$$` not `$` → `user_name_template = "$${source.login}"`
2. **Status:** Always set `status = "ACTIVE"` for all resources
3. **Naming:** Use snake_case → `okta_user.john_doe` not `okta_user.johnDoe`
4. **OAuth visibility:** Can't have `hide_ios=false` with `login_mode=DISABLED`

---

## File Organization

```
environments/{env}/terraform/
├── users.tf              # User resources
├── groups.tf             # Group and membership resources
├── apps.tf               # OAuth applications
├── oig_entitlements.tf   # Entitlement bundles
└── oig_reviews.tf        # Access review campaigns
```

---

## Resource Type Quick Reference

### Users

```hcl
resource "okta_user" "john_doe" {
  email      = "john.doe@example.com"
  first_name = "John"
  last_name  = "Doe"
  login      = "john.doe@example.com"
  department = "Engineering"
  title      = "Senior Engineer"
  status     = "ACTIVE"
}
```

**Key fields:**
- `email` (required, string)
- `first_name` (required, string)
- `last_name` (required, string)
- `login` (required, usually = email)
- `department` (optional, string)
- `title` (optional, string)
- `status` (required, always "ACTIVE")

---

### Groups

```hcl
resource "okta_group" "engineering" {
  name        = "Engineering Team"
  description = "All engineering department employees"
}
```

**Key fields:**
- `name` (required, string)
- `description` (optional, string)

---

### Group Memberships

```hcl
resource "okta_group_memberships" "engineering" {
  group_id = okta_group.engineering.id
  members = [
    okta_user.john_doe.id,
    okta_user.jane_smith.id,
  ]
  depends_on = [
    okta_user.john_doe,
    okta_user.jane_smith,
  ]
}
```

**Key fields:**
- `group_id` (required, reference)
- `members` (required, list of user IDs)
- `depends_on` (recommended for reliability)

---

### OAuth Applications

#### Single Page Application (SPA)

```hcl
resource "okta_app_oauth" "admin_dashboard" {
  label          = "Admin Dashboard"
  type           = "browser"
  grant_types    = ["authorization_code"]
  redirect_uris  = ["https://app.example.com/callback"]
  response_types = ["code"]

  pkce_required              = true
  token_endpoint_auth_method = "none"

  login_mode = "DISABLED"
  hide_ios   = true
  hide_web   = true

  user_name_template      = "$${source.login}"
  user_name_template_type = "BUILT_IN"
}
```

**SPA Requirements:**
- `type = "browser"`
- `pkce_required = true`
- `token_endpoint_auth_method = "none"` (public client)
- `grant_types = ["authorization_code"]` only

#### Web Application

```hcl
resource "okta_app_oauth" "portal" {
  label          = "Customer Portal"
  type           = "web"
  grant_types    = ["authorization_code", "refresh_token"]
  redirect_uris  = ["https://portal.example.com/callback"]
  response_types = ["code"]

  pkce_required              = true
  token_endpoint_auth_method = "client_secret_post"

  login_mode = "DISABLED"
  hide_ios   = true
  hide_web   = true

  user_name_template      = "$${source.login}"
  user_name_template_type = "BUILT_IN"
}
```

**Web App Requirements:**
- `type = "web"`
- `pkce_required = true` (recommended)
- `token_endpoint_auth_method = "client_secret_post"` or `"client_secret_basic"`
- `grant_types` can include `refresh_token`

#### Backend Service/API

```hcl
resource "okta_app_oauth" "api_service" {
  label       = "Payment API"
  type        = "service"
  grant_types = ["client_credentials"]

  token_endpoint_auth_method = "client_secret_post"
  response_types             = []

  login_mode = "DISABLED"
  hide_ios   = true
  hide_web   = true
}
```

**Service App Requirements:**
- `type = "service"`
- `grant_types = ["client_credentials"]` only
- `response_types = []` (empty)
- No redirect URIs needed

#### Native/Mobile Application

```hcl
resource "okta_app_oauth" "mobile_app" {
  label          = "Mobile App"
  type           = "native"
  grant_types    = ["authorization_code", "refresh_token"]
  redirect_uris  = ["com.example.app:/callback"]
  response_types = ["code"]

  pkce_required              = true
  token_endpoint_auth_method = "none"

  login_mode = "DISABLED"
  hide_ios   = false
  hide_web   = false

  user_name_template      = "$${source.login}"
  user_name_template_type = "BUILT_IN"
}
```

**Native App Requirements:**
- `type = "native"`
- `pkce_required = true` (required)
- `token_endpoint_auth_method = "none"` (public client)
- Custom URL schemes for redirect URIs

---

### App Group Assignments

```hcl
resource "okta_app_group_assignment" "salesforce_marketing" {
  app_id   = okta_app_oauth.salesforce.id
  group_id = okta_group.marketing_team.id
}
```

**Key fields:**
- `app_id` (required, reference to app)
- `group_id` (required, reference to group)

---

### Entitlement Bundles (OIG)

```hcl
resource "okta_entitlement_bundle" "marketing_access" {
  name        = "Marketing Access Bundle"
  description = "Complete access package for marketing team"
  status      = "ACTIVE"
}
```

**Key fields:**
- `name` (required, string)
- `description` (required, string)
- `status` (required, always "ACTIVE")

**CRITICAL:** This creates the bundle DEFINITION only. Assigning bundles to users/groups is done in Okta Admin UI, NOT in Terraform.

---

### Access Review Campaigns (OIG)

```hcl
resource "okta_reviews" "q1_2025_review" {
  name        = "Quarterly Access Review - Q1 2025"
  description = "Review of all user access"

  start_date = "2025-01-15T00:00:00Z"
  end_date   = "2025-02-15T23:59:59Z"

  review_type   = "USER_ACCESS_REVIEW"
  reviewer_type = "MANAGER"
}
```

**Key fields:**
- `name` (required, string)
- `description` (required, string)
- `start_date` (required, ISO 8601 format with Z timezone)
- `end_date` (required, ISO 8601 format with Z timezone)
- `review_type` (required, usually "USER_ACCESS_REVIEW")
- `reviewer_type` (required, "MANAGER" or "APPLICATION_OWNER")

---

## OAuth App Types Comparison

| Type | Grant Types | PKCE | Client Auth | Use Case |
|------|-------------|------|-------------|----------|
| **browser** | authorization_code | Required | none | React/Vue/Angular SPAs |
| **web** | authorization_code, refresh_token | Recommended | client_secret_post/basic | Traditional web apps |
| **native** | authorization_code, refresh_token | Required | none | iOS/Android/Desktop apps |
| **service** | client_credentials | N/A | client_secret_post/basic | Backend APIs, M2M |

---

## OAuth Visibility Rules

**Valid Combinations:**

| Scenario | hide_ios | hide_web | login_mode | Valid? |
|----------|----------|----------|------------|--------|
| Internal API | `true` | `true` | `DISABLED` | ✅ Yes |
| User-facing app | `false` | `false` | `SPEC` + login_uri | ✅ Yes |
| **Invalid** | `false` | - | `DISABLED` | ❌ No |

**Common pattern for internal/API apps:**
```hcl
login_mode = "DISABLED"
hide_ios   = true
hide_web   = true
```

**Common pattern for user-facing apps:**
```hcl
login_mode = "SPEC"
login_uri  = "https://app.example.com/login"
hide_ios   = false
hide_web   = false
```

---

## Template String Patterns

**Always use double dollar signs for Okta templates:**

```hcl
# ✅ CORRECT
user_name_template         = "$${source.login}"
user_name_template         = "$${source.email}"
user_name_template         = "$${source.firstName}.$${source.lastName}"

# ❌ WRONG - Terraform will fail
user_name_template         = "${source.login}"
```

**Common templates:**
- `$${source.login}` - Use login attribute
- `$${source.email}` - Use email attribute
- `$${source.firstName}.$${source.lastName}` - first.last format

**Always set template type:**
```hcl
user_name_template_type = "BUILT_IN"
```

---

## Common Patterns

### Create Users + Group + Memberships

```hcl
# Users
resource "okta_user" "user1" {
  email      = "user1@example.com"
  first_name = "User"
  last_name  = "One"
  login      = "user1@example.com"
  status     = "ACTIVE"
}

resource "okta_user" "user2" {
  email      = "user2@example.com"
  first_name = "User"
  last_name  = "Two"
  login      = "user2@example.com"
  status     = "ACTIVE"
}

# Group
resource "okta_group" "team" {
  name        = "Team Name"
  description = "Team description"
}

# Memberships
resource "okta_group_memberships" "team" {
  group_id = okta_group.team.id
  members  = [
    okta_user.user1.id,
    okta_user.user2.id,
  ]
  depends_on = [
    okta_user.user1,
    okta_user.user2,
  ]
}
```

### Create App + Assign to Group

```hcl
# Application
resource "okta_app_oauth" "app" {
  label          = "App Name"
  type           = "web"
  grant_types    = ["authorization_code", "refresh_token"]
  redirect_uris  = ["https://app.example.com/callback"]
  response_types = ["code"]

  pkce_required              = true
  token_endpoint_auth_method = "client_secret_post"

  login_mode = "DISABLED"
  hide_ios   = true
  hide_web   = true

  user_name_template      = "$${source.login}"
  user_name_template_type = "BUILT_IN"
}

# Assign to group
resource "okta_app_group_assignment" "app_team" {
  app_id   = okta_app_oauth.app.id
  group_id = okta_group.team.id
}
```

### OIG Bundle + Review Campaign

```hcl
# Entitlement bundle
resource "okta_entitlement_bundle" "access_bundle" {
  name        = "Department Access Bundle"
  description = "Access package for department employees"
  status      = "ACTIVE"
}

# Access review campaign
resource "okta_reviews" "quarterly_review" {
  name        = "Q1 2025 Access Review"
  description = "Quarterly review of user access"

  start_date = "2025-01-01T00:00:00Z"
  end_date   = "2025-01-31T23:59:59Z"

  review_type   = "USER_ACCESS_REVIEW"
  reviewer_type = "MANAGER"
}
```

---

## Infrastructure Patterns (AWS + Active Directory)

### Directory Structure

Infrastructure lives in separate directory from Okta resources:

```
environments/{env}/
├── terraform/        # Okta resources (users, groups, apps)
└── infrastructure/   # AWS resources (VPC, EC2, AD)
```

### Key Infrastructure Resources

**VPC + Networking:**
```hcl
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
}
```

**Security Group (AD Ports):**
```hcl
resource "aws_security_group" "domain_controller" {
  vpc_id = aws_vpc.main.id
}

# RDP
resource "aws_security_group_rule" "dc_rdp" {
  type              = "ingress"
  from_port         = 3389
  to_port           = 3389
  protocol          = "tcp"
  cidr_blocks       = var.allowed_rdp_cidrs
  security_group_id = aws_security_group.domain_controller.id
}

# DNS, LDAP, Kerberos, SMB, etc.
```

**Domain Controller EC2:**
```hcl
resource "aws_instance" "domain_controller" {
  ami           = data.aws_ami.windows_2022.id
  instance_type = "t3.medium"
  subnet_id     = aws_subnet.public.id

  user_data = templatefile("$${path.module}/scripts/userdata.ps1", {
    admin_password        = var.admin_password
    ad_domain_name        = var.ad_domain_name
    ad_safe_mode_password = var.ad_safe_mode_password
  })
}

resource "aws_eip" "dc" {
  instance = aws_instance.domain_controller.id
}
```

**Infrastructure Variables:**
```hcl
variable "ad_domain_name" {
  type    = string
  default = "demo.local"
}

variable "admin_password" {
  type      = string
  sensitive = true
}
```

### When to Generate Infrastructure

Generate infrastructure when user requests:
- "Deploy AD infrastructure"
- "Create Domain Controller"
- "Set up Active Directory for Okta"

**Key points:**
- Use S3 backend with environment-specific key
- Always include comprehensive security groups (DNS, LDAP, Kerberos, etc.)
- Warn about RDP access restrictions
- Use sensitive variables for passwords

---

## What NOT to Generate

**Don't generate Terraform for:**

1. **Resource owners** - Use Python scripts (`apply_resource_owners.py`)
2. **Governance labels** - Use Python scripts (`apply_governance_labels.py`)
3. **Entitlement assignments** - Managed in Okta Admin UI
4. **System apps** - Okta-managed, can't be in Terraform:
   - `okta-iga-reviewer`
   - `okta-flow-sso`
   - `okta-access-requests-resource-catalog`
   - `flow`
   - `okta-atspoke-sso`

---

## Validation Checklist

Before generating code, verify:

- [ ] All template strings use `$$` not `$`
- [ ] All resources have `status = "ACTIVE"`
- [ ] Resource names are snake_case
- [ ] OAuth apps follow visibility rules
- [ ] No system apps included
- [ ] Comments explain purpose
- [ ] No placeholder values (use realistic examples)
- [ ] Proper indentation (2 spaces)

---

## Example: Complete Demo Environment

**Prompt:** "Create 2 users, a group, and a Salesforce OAuth app"

**Generated Code:**

```hcl
# Save to: environments/demo/terraform/users.tf

resource "okta_user" "alice_marketing" {
  email      = "alice.marketing@example.com"
  first_name = "Alice"
  last_name  = "Marketing"
  login      = "alice.marketing@example.com"
  department = "Marketing"
  title      = "Marketing Manager"
  status     = "ACTIVE"
}

resource "okta_user" "bob_sales" {
  email      = "bob.sales@example.com"
  first_name = "Bob"
  last_name  = "Sales"
  login      = "bob.sales@example.com"
  department = "Sales"
  title      = "Sales Representative"
  status     = "ACTIVE"
}
```

```hcl
# Save to: environments/demo/terraform/groups.tf

resource "okta_group" "revenue_team" {
  name        = "Revenue Team"
  description = "Marketing and Sales team members"
}

resource "okta_group_memberships" "revenue_team" {
  group_id = okta_group.revenue_team.id
  members = [
    okta_user.alice_marketing.id,
    okta_user.bob_sales.id,
  ]
  depends_on = [
    okta_user.alice_marketing,
    okta_user.bob_sales,
  ]
}
```

```hcl
# Save to: environments/demo/terraform/apps.tf

resource "okta_app_oauth" "salesforce" {
  label          = "Salesforce CRM"
  type           = "web"
  grant_types    = ["authorization_code", "refresh_token"]
  redirect_uris  = ["https://login.salesforce.com/services/oauth2/callback"]
  response_types = ["code"]

  pkce_required              = true
  token_endpoint_auth_method = "client_secret_post"

  login_mode = "DISABLED"
  hide_ios   = true
  hide_web   = true

  user_name_template      = "$${source.login}"
  user_name_template_type = "BUILT_IN"
}

resource "okta_app_group_assignment" "salesforce_revenue" {
  app_id   = okta_app_oauth.salesforce.id
  group_id = okta_group.revenue_team.id
}
```

---

## Date Format for OIG Reviews

**ISO 8601 format with Z timezone:**

```hcl
start_date = "2025-01-15T00:00:00Z"  # ✅ Correct
end_date   = "2025-02-15T23:59:59Z"  # ✅ Correct

start_date = "2025-01-15"            # ❌ Wrong - missing time
start_date = "01/15/2025"            # ❌ Wrong - wrong format
```

**Pattern:**
- `YYYY-MM-DDTHH:MM:SSZ`
- Start dates usually: `T00:00:00Z`
- End dates usually: `T23:59:59Z`

---

## Common Grant Type Combinations

**Authorization Code (Web/SPA):**
```hcl
grant_types = ["authorization_code"]
# OR with refresh tokens:
grant_types = ["authorization_code", "refresh_token"]
```

**Client Credentials (Service/API):**
```hcl
grant_types = ["client_credentials"]
```

**Never mix:**
```hcl
# ❌ WRONG - Don't mix auth code with client credentials
grant_types = ["authorization_code", "client_credentials"]
```

---

## Response Type Rules

**Authorization Code flow:**
```hcl
response_types = ["code"]
```

**Service apps (client credentials):**
```hcl
response_types = []  # Empty array
```

---

## Okta Privileged Access (OPA) Quick Reference

**Provider:** `okta/oktapam` (separate from `okta/okta`)

### OPA Provider Setup
```hcl
provider "oktapam" {
  oktapam_key    = var.oktapam_key    # Service user key
  oktapam_secret = var.oktapam_secret # Service user secret
  oktapam_team   = var.oktapam_team   # Team name
}
```

### Resource Group & Project
```hcl
resource "oktapam_resource_group" "production" {
  name = "Production"
}

resource "oktapam_resource_group_project" "servers" {
  name                 = "Web Servers"
  resource_group       = oktapam_resource_group.production.id
  ssh_certificate_type = "CERT_TYPE_ED25519"
}

resource "oktapam_resource_group_server_enrollment_token" "token" {
  resource_group = oktapam_resource_group.production.id
  project        = oktapam_resource_group_project.servers.id
  description    = "Server enrollment token"
}
```

### Secret Management
```hcl
resource "oktapam_secret_folder" "creds" {
  name           = "Credentials"
  resource_group = oktapam_resource_group.production.id
  project        = oktapam_resource_group_project.servers.id
}

resource "oktapam_secret" "password" {
  name           = "db-password"
  resource_group = oktapam_resource_group.production.id
  project        = oktapam_resource_group_project.servers.id
  parent_folder  = oktapam_secret_folder.creds.id
  secret {
    type  = "password"
    value = var.db_password
  }
}
```

### Key OPA Resources
- `oktapam_resource_group` - Top-level container
- `oktapam_resource_group_project` - Project for servers
- `oktapam_resource_group_server_enrollment_token` - Server enrollment
- `oktapam_gateway_setup_token` - Gateway registration
- `oktapam_secret_folder` / `oktapam_secret` - Secrets
- `oktapam_group` - OPA groups
- `oktapam_project_group` - Group access to projects
- `oktapam_security_policy_v2` - Access policies

**Note:** OPA provider is optional - only enable when Privileged Access features are needed.

---

This quick reference covers 95% of common Okta Terraform patterns. For edge cases, refer to full documentation or ask for clarification.
