# Lifecycle Management Guide

Comprehensive guide for implementing Joiner/Mover/Leaver (JML) patterns using the `lifecycle-management` Terraform module.

## Table of Contents

- [Overview](#overview)
- [JML Concepts](#jml-concepts)
- [Module Architecture](#module-architecture)
- [Joiner Patterns](#joiner-patterns)
- [Mover Patterns](#mover-patterns)
- [Leaver Patterns](#leaver-patterns)
- [Contractor Lifecycle](#contractor-lifecycle)
- [OIG Integration](#oig-integration)
- [Implementation Guide](#implementation-guide)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

Lifecycle management automates user access throughout their employment journey:

- **Joiner**: New employee onboarding and initial access provisioning
- **Mover**: Role/department changes and access adjustments
- **Leaver**: Offboarding and access revocation

The `lifecycle-management` module provides Terraform resources for implementing these patterns in Okta.

---

## JML Concepts

### Joiner (Onboarding)

When a new user joins the organization:

1. User created in Okta (often via HR integration)
2. User type assigned (Employee, Contractor)
3. Department attribute set
4. **Automatic group assignment** via group rules
5. Access granted based on group membership
6. Manager relationship established

### Mover (Transfer)

When an existing user changes roles:

1. Department/title updated in Okta
2. Group rules **automatically adjust** membership
3. Old department group removes user
4. New department group adds user
5. Manager relationship may update
6. Access review may be triggered

### Leaver (Offboarding)

When a user leaves the organization:

1. User status changed to DEPROVISIONED or SUSPENDED
2. Group rules **automatically assign** to offboarding groups
3. Event hooks notify external systems
4. Access revoked based on status
5. Historical record preserved for audit

---

## Module Architecture

### Resource Types Created

| Resource | Purpose |
|----------|---------|
| `okta_user_type` | Employee, Contractor distinction |
| `okta_user_schema_property` | Custom attributes (lifecycleStatus, contractEndDate) |
| `okta_group` | Groups for each lifecycle state |
| `okta_group_rule` | Automatic group assignment |
| `okta_link_definition` | Manager relationships |
| `okta_event_hook` | External notifications |
| `okta_entitlement_bundle` | OIG access bundles |

### Group Structure

```
Base Groups
├── All Employees (userType=employee OR null)
├── All Contractors (userType=contractor)
└── [Department] Department (department="[name]")

Joiner Groups
├── Staged Users (status=STAGED)
└── New Hires (manual assignment)

Mover Groups
└── In Transfer (manual assignment)

Leaver Groups
├── Pending Offboard (manual assignment)
├── Deprovisioned (status=DEPROVISIONED)
├── Suspended (status=SUSPENDED)
└── Former Employees (manual assignment)

Contractor Groups
├── Contractor Limited Access
├── Contractor Standard Access
├── Contractors With End Date
├── Contractors Expiring Soon
├── Contractors Final Notice
├── Contractors Expired
└── Contractors Without Manager
```

---

## Joiner Patterns

### Automatic Group Assignment

Group rules automatically assign users based on attributes:

```hcl
# Employee auto-assignment (in module)
expression_value = "user.userType==\"employee\" OR user.userType==null"

# Department auto-assignment (in module)
expression_value = "user.department==\"Engineering\""
```

### Staged User Support

For users created before their start date:

1. Create user with `status = "STAGED"`
2. User auto-assigned to "Staged Users" group
3. Activate user on start date
4. User moves to appropriate groups

### Custom Auto-Assign Rules

Add custom rules for special cases:

```hcl
joiner_config = {
  auto_assign_rules = [
    {
      name          = "VPN Required"
      expression    = "user.city != \"San Francisco\""
      target_groups = [okta_group.vpn_users.id]
    },
    {
      name          = "Senior Staff"
      expression    = "String.stringContains(user.title, \"Senior\")"
      target_groups = [okta_group.senior_staff.id]
    }
  ]
}
```

### Manager Relationships

The module creates a manager link definition:

```hcl
# Primary: "manager"
# Associated: "directReport"
```

Establish relationships using `okta_link_value`:

```hcl
resource "okta_link_value" "manager" {
  primary_user_id     = okta_user.manager.id
  primary_name        = "manager"
  associated_user_ids = [okta_user.employee.id]
}
```

---

## Mover Patterns

### Department Change Handling

When `user.department` changes:

1. Old department rule no longer matches → user removed
2. New department rule matches → user added
3. No manual intervention needed

### Transfer Tracking

Use the "In Transfer" group to track users during transitions:

```hcl
# Manually add user to transfer group during role change
resource "okta_group_memberships" "transfer" {
  group_id = module.lifecycle.mover_groups.in_transfer
  users    = [okta_user.transferring_employee.id]
}
```

### Event Notifications

Configure webhooks for transfer events:

```hcl
mover_config = {
  webhook_url = "https://hr-system.example.com/api/transfers"
  webhook_events = [
    "user.account.update_profile",
    "group.user_membership.add",
    "group.user_membership.remove"
  ]
}
```

---

## Leaver Patterns

### Deprovisioning Workflow

Recommended offboarding process:

1. **Mark for offboarding**: Add to "Pending Offboard" group
2. **Revoke access**: Change status to `DEPROVISIONED`
3. **Group rules trigger**: User added to "Deprovisioned" group
4. **Webhooks fire**: External systems notified
5. **Preserve history**: User moved to "Former Employees"

### Status-Based Assignment

Group rules automatically track user status:

```hcl
# Deprovisioned users (in module)
expression_value = "user.status==\"DEPROVISIONED\""

# Suspended users (in module)
expression_value = "user.status==\"SUSPENDED\""
```

### Retention and Audit

The "Former Employees" group preserves records:

- Keeps historical record of departed users
- Supports compliance and audit requirements
- Allows recovery if user returns

---

## Contractor Lifecycle

### End Date Tracking

The module creates a custom attribute for contract end dates:

```hcl
contractor_config = {
  end_date_attribute = "contractEndDate"  # YYYY-MM-DD format
}
```

Set the attribute when creating contractors:

```hcl
resource "okta_user" "contractor" {
  first_name = "Jane"
  last_name  = "Contractor"
  login      = "jane.contractor@example.com"
  email      = "jane.contractor@example.com"
  user_type  = "contractor"

  custom_profile_attributes = jsonencode({
    contractEndDate = "2025-12-31"
  })
}
```

### Expiration Warning Groups

The module creates groups for tracking expiration stages:

| Group | Purpose |
|-------|---------|
| Contractors With End Date | All contractors with dates set |
| Contractors Expiring Soon | Within 30 days of end |
| Contractors Final Notice | Within 7 days of end |
| Contractors Expired | Past end date |

### Date-Based Automation

**Important:** Okta expressions cannot compare dates directly. You need external automation:

**Option 1: Okta Workflows**

Create a flow that:
1. Runs daily
2. Queries contractors with `contractEndDate`
3. Calculates days until expiration
4. Moves users to appropriate groups
5. Triggers deprovisioning for expired

**Option 2: External Script**

```python
# Example Python script (run daily via cron/scheduler)
from datetime import datetime, timedelta
import requests

def check_contractor_expiration(org, token):
    # Get all contractors with end dates
    contractors = get_contractors_with_end_date(org, token)

    today = datetime.now().date()

    for contractor in contractors:
        end_date = parse_date(contractor['profile']['contractEndDate'])
        days_remaining = (end_date - today).days

        if days_remaining <= 0:
            move_to_group(contractor, 'contractors_expired')
            deprovision_user(contractor)
        elif days_remaining <= 7:
            move_to_group(contractor, 'contractors_final_notice')
        elif days_remaining <= 30:
            move_to_group(contractor, 'contractors_expiring_soon')
```

### Manager Requirement

Flag contractors without managers for compliance:

```hcl
contractor_config = {
  require_manager         = true
  create_no_manager_group = true
}
```

Group rule expression:

```
user.userType=="contractor" AND user.managerId==null
```

---

## OIG Integration

### Entitlement Bundles

When `enable_oig_integration = true`, the module creates bundle definitions:

```hcl
# Default bundles
joiner_config = {
  default_employee_bundle   = "Standard Employee Access"
  default_contractor_bundle = "Contractor Limited Access"
}

# Department bundles
departments = [
  {
    name               = "Engineering"
    entitlement_bundle = "Engineering Tools"
  }
]

# Custom bundles
entitlement_bundles = [
  {
    name        = "IT Admin Access"
    description = "Administrative access for IT team"
  }
]
```

**Important:** Bundle definitions only. Assign principals via Okta Admin UI.

### Access Reviews

Access review campaigns are commented in the module. Enable based on provider support:

```hcl
# Example: Quarterly contractor review
resource "okta_reviews" "contractor_quarterly" {
  name        = "Quarterly Contractor Review"
  description = "Review all contractor access"
  # Configure based on provider schema
}
```

---

## Implementation Guide

### Step 1: Basic Setup

```hcl
module "lifecycle" {
  source = "../../modules/lifecycle-management"

  organization_name = "Your Company"

  enable_joiner_patterns      = true
  enable_mover_patterns       = true
  enable_leaver_patterns      = true
  enable_contractor_lifecycle = true
}
```

### Step 2: Configure Departments

```hcl
departments = [
  { name = "Engineering" },
  { name = "Sales" },
  { name = "Marketing" },
  { name = "Finance" },
  { name = "HR" },
  { name = "Legal" },
  { name = "Operations" }
]
```

### Step 3: Configure Contractors

```hcl
contractor_config = {
  end_date_attribute        = "contractEndDate"
  warning_days              = 30
  final_notice_days         = 7
  require_manager           = true
  create_expiration_groups  = true
}
```

### Step 4: Configure Webhooks (Optional)

```hcl
leaver_config = {
  webhook_url = "https://automation.company.com/okta/offboarding"
}

mover_config = {
  webhook_url = "https://automation.company.com/okta/transfers"
}
```

### Step 5: Apply and Verify

```bash
terraform init
terraform plan
terraform apply

# Verify groups in Okta Admin Console
```

### Step 6: Set Up Date Automation

Create Okta Workflow or external script for contractor expiration.

---

## Best Practices

### Group Rule Design

1. **Use simple expressions** - Complex expressions are harder to debug
2. **Test rules individually** - Verify each rule before enabling
3. **Allow processing time** - Rules can take 5-10 minutes to evaluate
4. **Document expressions** - Keep record of what each rule does

### Onboarding

1. **Use staged users** for future start dates
2. **Set department early** for correct initial access
3. **Assign manager** for approval workflows
4. **Verify group membership** before granting sensitive access

### Offboarding

1. **Deprovision, don't delete** - Preserve audit trail
2. **Use webhooks** for external system coordination
3. **Track former employees** for compliance
4. **Review shared accounts** during offboarding

### Contractors

1. **Always set end date** - Enforce via validation
2. **Require manager** - For accountability
3. **Limit access tier** - Start with minimum access
4. **Automate expiration** - Don't rely on manual tracking

---

## Troubleshooting

### Group Rules Not Triggering

1. **Check expression syntax**
   ```bash
   # Test expression in Okta Admin Console
   Directory → Groups → Rules → Test Expression
   ```

2. **Verify attribute values**
   ```bash
   # Check user profile
   curl -s "https://${ORG}.okta.com/api/v1/users/${USER_ID}" \
     -H "Authorization: SSWS ${TOKEN}" | jq '.profile'
   ```

3. **Allow processing time** - Rules evaluate periodically, not instantly

4. **Check rule status** - Ensure rule is ACTIVE

### Users Not in Expected Groups

1. **Check all matching rules** - User might match multiple rules
2. **Verify attribute spelling** - `department` vs `Department`
3. **Check user type** - `userType` must match expression

### Contractor Expiration Not Working

1. **Verify custom attribute** exists in schema
2. **Check date format** - Must be YYYY-MM-DD
3. **Set up automation** - Okta can't compare dates natively

### Webhooks Not Firing

1. **Verify URL accessibility** - Must be publicly reachable
2. **Check event types** - Events must match subscribed types
3. **Review event hook logs** in Okta Admin Console

---

## Related Documentation

- [Module README](../modules/lifecycle-management/README.md)
- [AI Prompt Template](../ai-assisted/prompts/setup_lifecycle_management.md)
- [OIG Prerequisites](../OIG_PREREQUISITES.md)
- [Okta Group Rules API](https://developer.okta.com/docs/reference/api/groups/#group-rule-operations)

---

**Last Updated:** 2026-01-06
