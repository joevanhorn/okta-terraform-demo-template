# Lifecycle Management Module

Terraform module for comprehensive Joiner/Mover/Leaver (JML) lifecycle management in Okta with OIG integration.

## Features

- **Joiner (Onboarding)**: Automatic group assignment, staged user support, manager relationships
- **Mover (Transfer)**: Transfer tracking, department change handling, event notifications
- **Leaver (Offboarding)**: Deprovisioning groups, status tracking, audit trail preservation
- **Contractor Lifecycle**: End-date tracking, expiration warnings, access tiers, compliance flags
- **OIG Integration**: Entitlement bundles, access review campaign definitions

## Quick Start

### Basic Usage

```hcl
module "lifecycle" {
  source = "../../modules/lifecycle-management"

  organization_name = "Acme Corp"

  # Enable all lifecycle patterns
  enable_joiner_patterns      = true
  enable_mover_patterns       = true
  enable_leaver_patterns      = true
  enable_contractor_lifecycle = true
}
```

### Full Configuration

```hcl
module "lifecycle" {
  source = "../../modules/lifecycle-management"

  organization_name = "Acme Corp"

  # Enable all patterns
  enable_joiner_patterns      = true
  enable_mover_patterns       = true
  enable_leaver_patterns      = true
  enable_contractor_lifecycle = true
  enable_oig_integration      = true  # Requires OIG license

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
      description  = "External contractors"
    }
  ]

  # Departments with auto-assignment
  departments = [
    {
      name               = "Engineering"
      entitlement_bundle = "Engineering Tools"
    },
    {
      name               = "Sales"
      entitlement_bundle = "Sales Tools"
    },
    {
      name               = "Finance"
      entitlement_bundle = "Finance Tools"
    }
  ]

  # Joiner configuration
  joiner_config = {
    enable_staged_users       = true
    create_new_hires_group    = true
    default_employee_bundle   = "Standard Employee Access"
    default_contractor_bundle = "Contractor Limited Access"

    auto_assign_rules = [
      {
        name          = "Senior Staff Access"
        expression    = "String.stringContains(user.title, \"Senior\")"
        target_groups = ["Leadership Group ID"]
      }
    ]
  }

  # Contractor configuration
  contractor_config = {
    end_date_attribute        = "contractEndDate"
    create_end_date_attribute = true
    warning_days              = 30
    final_notice_days         = 7
    require_manager           = true
    create_expiration_groups  = true
    create_access_tier_groups = true
  }

  # Leaver configuration
  leaver_config = {
    webhook_url               = "https://automation.example.com/lifecycle"
    create_former_group       = true
    create_suspended_group    = true
    create_pending_offboard_group = true
  }

  # Mover configuration
  mover_config = {
    create_transfer_group = true
    webhook_url           = "https://automation.example.com/transfers"
  }
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.9.0 |
| okta | >= 6.4.0, < 7.0.0 |

## Inputs

### Module Enable Flags

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `enable_joiner_patterns` | Enable onboarding patterns | `bool` | `true` |
| `enable_mover_patterns` | Enable transfer patterns | `bool` | `true` |
| `enable_leaver_patterns` | Enable offboarding patterns | `bool` | `true` |
| `enable_contractor_lifecycle` | Enable contractor patterns | `bool` | `true` |
| `enable_oig_integration` | Enable OIG features | `bool` | `false` |

### Core Configuration

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `organization_name` | Organization name for resource naming | `string` | Required |
| `name_prefix` | Prefix for resource names | `string` | `""` |
| `departments` | Departments for auto-assignment | `list(object)` | `[]` |
| `user_types` | User types to create | `list(object)` | Employee, Contractor |

### Joiner Configuration

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `joiner_config.auto_assign_rules` | Custom group assignment rules | `list(object)` | `[]` |
| `joiner_config.default_employee_bundle` | Default bundle for employees | `string` | `""` |
| `joiner_config.default_contractor_bundle` | Default bundle for contractors | `string` | `""` |
| `joiner_config.enable_staged_users` | Track staged users | `bool` | `true` |
| `joiner_config.create_new_hires_group` | Create new hires group | `bool` | `true` |

### Contractor Configuration

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `contractor_config.end_date_attribute` | Custom attribute for end date | `string` | `"contractEndDate"` |
| `contractor_config.warning_days` | Days before expiration warning | `number` | `30` |
| `contractor_config.final_notice_days` | Days before final notice | `number` | `7` |
| `contractor_config.require_manager` | Flag contractors without manager | `bool` | `true` |
| `contractor_config.create_expiration_groups` | Create expiration tracking groups | `bool` | `true` |

### Leaver Configuration

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `leaver_config.webhook_url` | URL for offboarding notifications | `string` | `""` |
| `leaver_config.create_former_group` | Create former employees group | `bool` | `true` |
| `leaver_config.create_suspended_group` | Create suspended users group | `bool` | `true` |

## Outputs

### Groups

| Name | Description |
|------|-------------|
| `base_groups` | All Employees, All Contractors group IDs |
| `department_groups` | Department group IDs |
| `joiner_groups` | Staged Users, New Hires group IDs |
| `mover_groups` | In Transfer group ID |
| `leaver_groups` | Deprovisioned, Suspended, Former Employees group IDs |
| `contractor_groups` | Contractor-specific group IDs |
| `all_groups` | All group IDs in a flat map |

### Other Resources

| Name | Description |
|------|-------------|
| `user_types` | Created user type IDs |
| `group_rules` | Created group rule IDs |
| `entitlement_bundles` | Created OIG bundle IDs |
| `event_hooks` | Created event hook IDs |
| `schema_properties` | Created schema property indexes |
| `configuration` | Module configuration summary |

## Use Cases

### 1. New Employee Onboarding

When a new employee is created:
1. `okta_group_rule` auto-assigns to "All Employees" based on userType
2. Department rule auto-assigns to department group
3. User appears in "Staged Users" group until activated
4. After activation, tracked in "New Hires" for 30-day review

### 2. Contractor Onboarding

When a contractor is created:
1. Auto-assigned to "All Contractors" group
2. `contractEndDate` attribute set with expiration
3. Auto-assigned to "Contractors With End Date" group
4. As expiration approaches:
   - Moved to "Contractors Expiring Soon" (30 days)
   - Moved to "Contractors Final Notice" (7 days)
   - Moved to "Contractors Expired" (past date)

### 3. Department Transfer

When user's department changes:
1. Old department group rule removes user
2. New department group rule adds user
3. User can be placed in "In Transfer" group for review
4. Event hook notifies external systems

### 4. Employee Offboarding

When user is deactivated:
1. Auto-assigned to "Deprovisioned" group
2. Event hook notifies HR/IT systems
3. User tracked in "Former Employees" for audit

## Contractor Expiration Workflow

The module creates groups for tracking contractor expiration stages:

```
Active Contractor
    │
    ▼ (30 days before end date)
Contractors Expiring Soon ──── Notification
    │
    ▼ (7 days before end date)
Contractors Final Notice ───── Urgent Notification
    │
    ▼ (end date reached)
Contractors Expired ─────────── Deprovisioning Trigger
```

**Note:** Actual date-based group membership requires external automation (Okta Workflows or scripts) since Okta expression language has limited date comparison capabilities.

## Group Rule Expressions

The module uses these Okta expressions:

| Purpose | Expression |
|---------|------------|
| All Employees | `user.userType=="employee" OR user.userType==null` |
| All Contractors | `user.userType=="contractor"` |
| Department | `user.department=="Engineering"` |
| Staged Users | `user.status=="STAGED"` |
| Deprovisioned | `user.status=="DEPROVISIONED"` |
| Suspended | `user.status=="SUSPENDED"` |
| Contractor No Manager | `user.userType=="contractor" AND user.managerId==null` |

## OIG Integration Notes

When `enable_oig_integration = true`:

1. **Entitlement bundles** are created as definitions only
2. **Principal assignments** must be managed in Okta Admin UI
3. **Access reviews** are commented out (uncomment based on provider support)

## Related Documentation

- [Lifecycle Management Guide](../../docs/LIFECYCLE_MANAGEMENT.md)
- [AI Prompt Template](../../ai-assisted/prompts/setup_lifecycle_management.md)
- [OIG Prerequisites](../../OIG_PREREQUISITES.md)

## Authors

Okta Terraform Demo Template Contributors

## License

MIT License
