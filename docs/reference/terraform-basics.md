# Terraform Basics for Okta

**Difficulty:** Beginner | **Purpose:** Quick reference for common Okta resources

Copy-paste examples for managing Okta with Terraform.

---

## Quick Start Templates

### Option 1: Ready-Made Demo (2 minutes)

In the `environments/myorg/terraform/` directory:

```bash
cp QUICKSTART_DEMO.tf.example demo.tf
# Edit demo.tf: uncomment all code, change @example.com
terraform init && terraform apply
```

Creates: 5 users, 3 groups, 1 OAuth app

### Option 2: Browse All Examples

```bash
# Comprehensive reference with ALL resource types
less environments/myorg/terraform/RESOURCE_EXAMPLES.tf
```

---

## Common Resources

### Users

```hcl
resource "okta_user" "employee" {
  first_name = "John"
  last_name  = "Smith"
  login      = "john.smith@company.com"
  email      = "john.smith@company.com"
}

# With additional attributes
resource "okta_user" "detailed" {
  first_name         = "Jane"
  last_name          = "Doe"
  login              = "jane.doe@company.com"
  email              = "jane.doe@company.com"
  department         = "Engineering"
  title              = "Senior Developer"
  manager            = "john.smith@company.com"
  employee_number    = "EMP001"
  organization       = "Acme Corp"
  cost_center        = "CC-100"
  division           = "Technology"
}
```

### Bulk User Management with CSV

For managing 1000+ users, use CSV-based import. See `environments/myorg/terraform/users_from_csv.tf.example` for complete implementation.

**Quick Start:**
```bash
cp environments/myorg/terraform/users.csv.example users.csv
cp environments/myorg/terraform/users_from_csv.tf.example users_from_csv.tf
# Edit users.csv with your data
terraform apply -parallelism=10
```

**CSV Format:**
```csv
email,first_name,last_name,login,status,department,title,manager_email,groups,custom_profile_attributes
john@example.com,John,Doe,john@example.com,ACTIVE,Engineering,Developer,alice@example.com,"Engineering,Developers","{""employeeId"":""E001""}"
```

**Key Points:**
- Manager relationships use `manager_email` column, resolved via `okta_link_value`
- Groups are comma-separated, auto-created if they don't exist
- Custom attributes as JSON with escaped quotes
- Use `-parallelism=10` for faster execution

### Groups

```hcl
resource "okta_group" "engineering" {
  name        = "Engineering"
  description = "Engineering team members"
}

# With custom profile
resource "okta_group" "sales" {
  name        = "Sales"
  description = "Sales team"

  custom_profile_attributes = jsonencode({
    "costCenter" = "CC-200"
  })
}
```

### Group Memberships

```hcl
resource "okta_group_memberships" "engineering_members" {
  group_id = okta_group.engineering.id
  users = [
    okta_user.employee.id,
    okta_user.detailed.id,
  ]
}
```

### OAuth Application

```hcl
resource "okta_app_oauth" "webapp" {
  label                     = "My Web Application"
  type                      = "web"
  grant_types               = ["authorization_code", "refresh_token"]
  redirect_uris             = ["https://app.example.com/callback"]
  post_logout_redirect_uris = ["https://app.example.com/logout"]
  response_types            = ["code"]

  # Visible on user dashboard
  hide_ios = false
  hide_web = false

  lifecycle {
    ignore_changes = [groups]
  }
}

# Assign group to app
resource "okta_app_group_assignment" "webapp_engineering" {
  app_id   = okta_app_oauth.webapp.id
  group_id = okta_group.engineering.id
}
```

### SAML Application

```hcl
resource "okta_app_saml" "salesforce" {
  label             = "Salesforce"
  sso_url           = "https://login.salesforce.com"
  recipient         = "https://login.salesforce.com"
  destination       = "https://login.salesforce.com"
  audience          = "https://saml.salesforce.com"
  subject_name_id_format = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"

  attribute_statements {
    name      = "email"
    values    = ["user.email"]
  }
}
```

### Sign-On Policy

```hcl
resource "okta_policy_signon" "mfa_required" {
  name        = "MFA Required"
  status      = "ACTIVE"
  description = "Require MFA for all users"

  groups_included = [okta_group.engineering.id]
}

resource "okta_policy_rule_signon" "mfa_rule" {
  policy_id          = okta_policy_signon.mfa_required.id
  name               = "Require MFA"
  status             = "ACTIVE"
  access             = "ALLOW"
  mfa_required       = true
  mfa_prompt         = "ALWAYS"
  session_idle       = 120
  session_lifetime   = 720
}
```

### Password Policy

```hcl
resource "okta_policy_password" "strong" {
  name                   = "Strong Password Policy"
  status                 = "ACTIVE"
  description            = "Requires strong passwords"
  password_min_length    = 12
  password_min_lowercase = 1
  password_min_uppercase = 1
  password_min_number    = 1
  password_min_symbol    = 1
  password_max_age_days  = 90

  groups_included = [okta_group.engineering.id]
}
```

---

## OIG Resources (Identity Governance)

**Note:** Enable Entitlement Management first. See [OIG_PREREQUISITES.md](./OIG_PREREQUISITES.md).

### Entitlement Bundle

```hcl
resource "okta_entitlement_bundle" "admin_access" {
  name        = "Admin Access Bundle"
  description = "Administrative access to systems"
  status      = "ACTIVE"
}
```

**Dynamic Value Lookups:** When bundling entitlement values, use dynamic blocks to reference Okta-generated IDs by external_value:

```hcl
locals {
  admin_accounts = ["ACC001", "ACC002", "ACC003"]
}

resource "okta_entitlement_bundle" "admin_bundle" {
  name   = "Admin Bundle"
  status = "ACTIVE"

  target {
    external_id = okta_app_oauth.my_app.id
    type        = "APPLICATION"
  }

  entitlements {
    id = okta_entitlement.accounts.id
    dynamic "values" {
      for_each = [
        for v in okta_entitlement.accounts.values : v.id
        if contains(local.admin_accounts, v.external_value)
      ]
      content {
        id = values.value
      }
    }
  }
}
```

**Note:** `values` is a block type, not an argument. See `RESOURCE_EXAMPLES.tf` for complete examples.

### Access Review Campaign

```hcl
resource "okta_reviews" "quarterly_review" {
  name        = "Quarterly Access Review"
  description = "Review all access quarterly"

  # Schedule and scope must be configured in Okta Admin UI
  # See REQUIRED TODO in generated files

  lifecycle {
    ignore_changes = [schedule, scope]
  }
}
```

### Approval Sequence

```hcl
resource "okta_request_sequences" "manager_approval" {
  name        = "Manager Approval"
  description = "Requires manager approval"
  conditions  = jsonencode({
    type = "ALWAYS"
  })

  approval {
    type = "MANAGER"
  }
}
```

---

## Important Patterns

### Template String Escaping

Okta uses `${source.login}` syntax which conflicts with Terraform. Use double `$$`:

```hcl
# WRONG - Terraform tries to interpolate
user_name_template = "${source.login}"

# CORRECT - Escaped for Okta
user_name_template = "$${source.login}"
```

### Lifecycle Ignore

For attributes managed elsewhere (UI, API):

```hcl
resource "okta_app_oauth" "app" {
  label = "My App"
  # ...

  lifecycle {
    ignore_changes = [groups, users]
  }
}
```

### Dependencies

Terraform handles most dependencies automatically, but explicit is clearer:

```hcl
resource "okta_group_memberships" "members" {
  group_id = okta_group.mygroup.id
  users    = [okta_user.myuser.id]

  depends_on = [
    okta_user.myuser,
    okta_group.mygroup
  ]
}
```

---

## Common Commands

```bash
# Format code (run before committing)
terraform fmt

# Validate syntax
terraform validate

# Preview changes (ALWAYS run this first)
terraform plan

# Apply changes
terraform apply

# Apply specific resource only
terraform apply -target=okta_user.employee

# Destroy all resources (careful!)
terraform destroy

# Destroy specific resource
terraform destroy -target=okta_user.employee

# Show current state
terraform state list

# Show resource details
terraform state show okta_user.employee

# Import existing resource
terraform import okta_user.employee "00u1234567890"
```

---

## File Organization

### Recommended Structure

```
okta-terraform/
├── provider.tf           # Provider configuration
├── variables.tf          # Variable definitions
├── terraform.tfvars      # Variable values (don't commit!)
├── users.tf              # User resources
├── groups.tf             # Groups and memberships
├── apps.tf               # Applications
├── policies.tf           # Policies and rules
└── oig.tf                # OIG resources (if using)
```

### Naming Conventions

- **Files:** lowercase with underscores: `user_management.tf`
- **Resources:** descriptive with underscores: `okta_user.john_doe`
- **Variables:** lowercase with underscores: `okta_org_name`

---

## Common Errors & Solutions

### "Error: 401 Unauthorized"
API token is invalid or expired. Create a new one in Okta Admin Console.

### "Error: resource already exists"
Resource exists in Okta but not in Terraform state. Import it:
```bash
terraform import okta_user.existing "00u1234567890"
```

### "Error: Invalid value for 'login'"
Email must be unique across Okta. Check for duplicates.

### "Provider produced inconsistent result"
Usually a timing issue. Run `terraform apply` again.

### Template interpolation errors
Use `$$` instead of `$` for Okta template strings.

---

## Finding Resource IDs

### In Okta Admin Console

1. Navigate to the resource (user, group, app)
2. Look at the URL: `https://dev-12345.okta.com/admin/user/profile/view/00u1234567890`
3. The ID is the last part: `00u1234567890`

### Using Terraform

```bash
terraform state list
# okta_user.employee

terraform state show okta_user.employee
# Shows all attributes including id
```

### ID Prefixes

- `00u` - Users
- `00g` - Groups
- `0oa` - Applications
- `00p` - Policies

---

## Advanced Topics

### Data Sources (Read Existing)

```hcl
# Get existing user
data "okta_user" "admin" {
  search {
    name  = "profile.email"
    value = "admin@company.com"
  }
}

# Get existing group
data "okta_group" "everyone" {
  name = "Everyone"
}

# Use in resources
resource "okta_group_memberships" "add_to_everyone" {
  group_id = data.okta_group.everyone.id
  users    = [okta_user.employee.id]
}
```

### Outputs

```hcl
output "webapp_client_id" {
  value       = okta_app_oauth.webapp.client_id
  description = "OAuth client ID for the web app"
}

output "webapp_client_secret" {
  value       = okta_app_oauth.webapp.client_secret
  sensitive   = true
  description = "OAuth client secret"
}
```

View outputs:
```bash
terraform output
terraform output webapp_client_secret  # Shows sensitive
```

---

## Next Steps

- **More Examples:** See `RESOURCE_EXAMPLES.tf` in your terraform directory
- **OIG Features:** See [OIG_PREREQUISITES.md](./OIG_PREREQUISITES.md)
- **Troubleshooting:** See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Provider Docs:** [registry.terraform.io/providers/okta/okta](https://registry.terraform.io/providers/okta/okta/latest/docs)
