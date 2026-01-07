# AI Prompt: Setup Lifecycle Management

Use this prompt to configure the Lifecycle Management module for comprehensive Joiner/Mover/Leaver patterns.

---

## Instructions for AI

You are a Terraform expert helping configure lifecycle management for Okta. Generate complete, working Terraform code using the `lifecycle-management` module.

### Context Files to Include

Before using this prompt, provide these context files to the AI:

1. `ai-assisted/context/repository_structure.md` - Project structure
2. `ai-assisted/context/okta_resource_guide.md` - Okta resources reference
3. `modules/lifecycle-management/README.md` - Module documentation

---

## Prompt Template

```
I need to set up lifecycle management for my Okta organization.

## Environment Details
- Environment directory: [e.g., environments/myorg]
- Organization name: [e.g., Acme Corp]

## Lifecycle Requirements

### User Types
- [ ] Employees (full-time, part-time)
- [ ] Contractors (time-limited)
- [ ] Other: [specify]

### Departments (for auto-assignment)
List your departments:
- [Department 1]
- [Department 2]
- [Department 3]

### Joiner (Onboarding) Requirements
- Track staged users: [yes/no]
- Track new hires: [yes/no]
- Custom auto-assign rules:
  - [Rule description and criteria]
- Default employee entitlement bundle: [name or skip]
- Default contractor entitlement bundle: [name or skip]

### Mover (Transfer) Requirements
- Track users in transfer: [yes/no]
- Webhook for transfer notifications: [URL or skip]

### Leaver (Offboarding) Requirements
- Track deprovisioned users: [yes/no]
- Track suspended users: [yes/no]
- Track former employees: [yes/no]
- Webhook for offboarding notifications: [URL or skip]

### Contractor Requirements
- Enable contractor lifecycle: [yes/no]
- Contract end date attribute name: [contractEndDate]
- Warning period before expiration: [30] days
- Final notice period: [7] days
- Require manager for contractors: [yes/no]
- Create expiration warning groups: [yes/no]
- Create access tier groups (limited/standard): [yes/no]

### OIG Integration (Optional)
- Enable entitlement bundles: [yes/no]
- Bundle names to create:
  - [Bundle 1]
  - [Bundle 2]

## Output Requirements
1. Generate module call in lifecycle.tf
2. Include all necessary variable values
3. Add comments explaining each section
4. Follow repository patterns exactly

Please generate the Terraform configuration.
```

---

## Example Output

### Basic Configuration

```hcl
# =============================================================================
# LIFECYCLE MANAGEMENT CONFIGURATION
# =============================================================================
# Configures JML (Joiner/Mover/Leaver) patterns for the organization
# =============================================================================

module "lifecycle" {
  source = "../../modules/lifecycle-management"

  organization_name = "Acme Corp"

  # Enable all lifecycle patterns
  enable_joiner_patterns      = true
  enable_mover_patterns       = true
  enable_leaver_patterns      = true
  enable_contractor_lifecycle = true
  enable_oig_integration      = false  # Set true if OIG licensed

  # User types
  user_types = [
    {
      name         = "employee"
      display_name = "Employee"
      description  = "Full-time and part-time employees"
    },
    {
      name         = "contractor"
      display_name = "Contractor"
      description  = "External contractors with time-limited access"
    }
  ]

  # Departments for auto-assignment
  departments = [
    { name = "Engineering" },
    { name = "Sales" },
    { name = "Marketing" },
    { name = "Finance" },
    { name = "HR" }
  ]

  # Joiner configuration
  joiner_config = {
    enable_staged_users    = true
    create_new_hires_group = true
  }

  # Contractor configuration
  contractor_config = {
    end_date_attribute        = "contractEndDate"
    warning_days              = 30
    final_notice_days         = 7
    require_manager           = true
    create_expiration_groups  = true
    create_access_tier_groups = true
  }

  # Leaver configuration
  leaver_config = {
    create_former_group           = true
    create_suspended_group        = true
    create_pending_offboard_group = true
  }
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "lifecycle_groups" {
  description = "All lifecycle management groups"
  value       = module.lifecycle.all_groups
}

output "lifecycle_config" {
  description = "Lifecycle configuration summary"
  value       = module.lifecycle.configuration
}
```

### Advanced Configuration with OIG

```hcl
module "lifecycle" {
  source = "../../modules/lifecycle-management"

  organization_name = "Enterprise Corp"

  # Enable all patterns including OIG
  enable_joiner_patterns      = true
  enable_mover_patterns       = true
  enable_leaver_patterns      = true
  enable_contractor_lifecycle = true
  enable_oig_integration      = true

  # Departments with entitlement bundles
  departments = [
    {
      name               = "Engineering"
      entitlement_bundle = "Engineering Tools Bundle"
    },
    {
      name               = "Sales"
      entitlement_bundle = "Sales Tools Bundle"
    },
    {
      name               = "Finance"
      entitlement_bundle = "Finance Tools Bundle"
    }
  ]

  # Joiner configuration with bundles
  joiner_config = {
    enable_staged_users       = true
    create_new_hires_group    = true
    default_employee_bundle   = "Standard Employee Access"
    default_contractor_bundle = "Contractor Limited Access"

    # Custom rules for special cases
    auto_assign_rules = [
      {
        name          = "Executive Access"
        expression    = "String.stringContains(user.title, \"VP\") OR String.stringContains(user.title, \"Director\")"
        target_groups = [okta_group.executives.id]
      },
      {
        name          = "Remote Workers"
        expression    = "user.city != \"San Francisco\" AND user.city != \"New York\""
        target_groups = [okta_group.remote.id]
      }
    ]
  }

  # Contractor configuration
  contractor_config = {
    end_date_attribute        = "contractEndDate"
    warning_days              = 30
    final_notice_days         = 7
    require_manager           = true
    create_expiration_groups  = true
    create_access_tier_groups = true
  }

  # Leaver configuration with webhooks
  leaver_config = {
    webhook_url = "https://automation.enterprise.com/okta/offboarding"
    webhook_events = [
      "user.lifecycle.deactivate",
      "user.lifecycle.suspend"
    ]
    create_former_group           = true
    create_suspended_group        = true
    create_pending_offboard_group = true
  }

  # Mover configuration with webhooks
  mover_config = {
    create_transfer_group = true
    webhook_url           = "https://automation.enterprise.com/okta/transfers"
  }

  # Additional entitlement bundles
  entitlement_bundles = [
    {
      name        = "IT Admin Bundle"
      description = "Access for IT administrators"
    },
    {
      name        = "Security Team Bundle"
      description = "Access for security team members"
    }
  ]
}

# Supporting groups for custom rules
resource "okta_group" "executives" {
  name        = "Enterprise Corp - Executives"
  description = "Executive leadership team"
}

resource "okta_group" "remote" {
  name        = "Enterprise Corp - Remote Workers"
  description = "Employees working remotely"
}
```

---

## Post-Configuration Steps

### 1. Apply Terraform

```bash
cd environments/myorg/terraform
terraform init
terraform plan
terraform apply
```

### 2. Verify Groups Created

Check Okta Admin Console → Directory → Groups for:
- All Employees
- All Contractors
- Department groups
- Staged Users
- New Hires
- Deprovisioned
- Contractor expiration groups

### 3. Configure Contractor Expiration Automation

Since Okta expressions have limited date comparison, set up Okta Workflows:

1. Create a flow that runs daily
2. Query contractors with `contractEndDate` set
3. Compare dates and move to appropriate groups:
   - 30 days out → "Contractors Expiring Soon"
   - 7 days out → "Contractors Final Notice"
   - Past date → "Contractors Expired"
4. Trigger deprovisioning for expired contractors

### 4. Assign Entitlement Bundles (OIG)

If OIG enabled:
1. Navigate to: Identity Governance → Entitlements
2. Add applications to each bundle
3. Configure bundle access policies
4. Assign bundles via Access Requests or direct assignment

### 5. Test Lifecycle Flows

**Test Joiner:**
```bash
# Create a staged user
curl -X POST "https://${OKTA_ORG}.okta.com/api/v1/users?activate=false" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"profile":{"firstName":"Test","lastName":"User","email":"test@example.com","login":"test@example.com","department":"Engineering"}}'
```

**Test Leaver:**
```bash
# Deactivate a user
curl -X POST "https://${OKTA_ORG}.okta.com/api/v1/users/${USER_ID}/lifecycle/deactivate" \
  -H "Authorization: SSWS ${OKTA_API_TOKEN}"
```

---

## Common Customizations

### Custom Department Group Names

```hcl
departments = [
  {
    name              = "Engineering"
    group_name        = "Tech Team"
    group_description = "Software engineering department"
  }
]
```

### Disable Specific Features

```hcl
# Only enable what you need
enable_joiner_patterns      = true
enable_mover_patterns       = false  # Skip transfer tracking
enable_leaver_patterns      = true
enable_contractor_lifecycle = false  # No contractors
```

### Custom Lifecycle Status Values

```hcl
lifecycle_status_values = [
  "ONBOARDING",
  "ACTIVE",
  "ON_LEAVE",
  "TRANSFERRING",
  "OFFBOARDING"
]
```

---

## Troubleshooting

### Group Rules Not Working

1. Check expression syntax in Okta Admin Console
2. Verify user attributes are populated
3. Check rule status is ACTIVE
4. Allow 5-10 minutes for rule processing

### Contractor End Date Not Detected

1. Verify custom attribute exists in user schema
2. Check date format is YYYY-MM-DD
3. Set up external automation for date comparison

### OIG Bundles Not Available

1. Verify OIG license is active
2. Check `enable_oig_integration = true`
3. Bundles are definitions only - assign via Admin UI

---

## Related Documentation

- [Module README](../../modules/lifecycle-management/README.md)
- [Lifecycle Management Guide](../../docs/LIFECYCLE_MANAGEMENT.md)
- [OIG Prerequisites](../../OIG_PREREQUISITES.md)
