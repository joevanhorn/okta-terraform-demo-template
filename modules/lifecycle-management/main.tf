# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - Core Resources
# =============================================================================
# Creates foundational resources: user types, schema properties, base groups
# =============================================================================

# -----------------------------------------------------------------------------
# User Types
# -----------------------------------------------------------------------------
# Create custom user types for lifecycle differentiation

resource "okta_user_type" "lifecycle_types" {
  for_each = var.create_user_types ? local.user_type_map : {}

  name         = each.value.name
  display_name = each.value.display_name
  description  = each.value.description
}

# -----------------------------------------------------------------------------
# Custom Schema Properties
# -----------------------------------------------------------------------------
# Add custom attributes needed for lifecycle tracking

resource "okta_user_schema_property" "lifecycle_status" {
  count = var.create_lifecycle_status_attribute ? 1 : 0

  index       = "lifecycleStatus"
  title       = "Lifecycle Status"
  type        = "string"
  description = "Current lifecycle status for tracking user state"
  master      = "PROFILE_MASTER"
  scope       = "NONE"

  enum = var.lifecycle_status_values

  one_of {
    const = "ONBOARDING"
    title = "Onboarding"
  }
  one_of {
    const = "ACTIVE"
    title = "Active"
  }
  one_of {
    const = "TRANSFERRING"
    title = "Transferring"
  }
  one_of {
    const = "OFFBOARDING"
    title = "Offboarding"
  }
}

# -----------------------------------------------------------------------------
# Base Groups - All Employees
# -----------------------------------------------------------------------------

resource "okta_group" "all_employees" {
  count = var.enable_joiner_patterns ? 1 : 0

  name        = "${local.name_prefix} - All Employees"
  description = "All active employees (managed by lifecycle module)"
}

resource "okta_group_rule" "all_employees" {
  count = var.enable_joiner_patterns ? 1 : 0

  name              = "Auto-assign All Employees"
  status            = "ACTIVE"
  group_assignments = [okta_group.all_employees[0].id]
  expression_type   = "urn:okta:expression:1.0"
  expression_value  = local.employee_expression
}

# -----------------------------------------------------------------------------
# Base Groups - All Contractors
# -----------------------------------------------------------------------------

resource "okta_group" "all_contractors" {
  count = var.enable_contractor_lifecycle ? 1 : 0

  name        = "${local.name_prefix} - All Contractors"
  description = "All active contractors (managed by lifecycle module)"
}

resource "okta_group_rule" "all_contractors" {
  count = var.enable_contractor_lifecycle ? 1 : 0

  name              = "Auto-assign All Contractors"
  status            = "ACTIVE"
  group_assignments = [okta_group.all_contractors[0].id]
  expression_type   = "urn:okta:expression:1.0"
  expression_value  = local.contractor_expression
}

# -----------------------------------------------------------------------------
# Department Groups
# -----------------------------------------------------------------------------
# Create groups for each configured department

resource "okta_group" "departments" {
  for_each = local.department_groups

  name        = each.value.name
  description = each.value.description
}

# Department-based auto-assignment rules
resource "okta_group_rule" "departments" {
  for_each = var.enable_joiner_patterns ? local.department_rules : {}

  name              = each.value.name
  status            = "ACTIVE"
  group_assignments = [okta_group.departments[each.value.target_group_key].id]
  expression_type   = "urn:okta:expression:1.0"
  expression_value  = each.value.expression
}
