# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - Outputs
# =============================================================================
# Exports resource IDs and configuration for use by calling modules
# =============================================================================

# -----------------------------------------------------------------------------
# User Types
# -----------------------------------------------------------------------------

output "user_types" {
  description = "Created user type IDs"
  value = var.create_user_types ? {
    for name, ut in okta_user_type.lifecycle_types : name => ut.id
  } : {}
}

# -----------------------------------------------------------------------------
# Base Groups
# -----------------------------------------------------------------------------

output "base_groups" {
  description = "Base lifecycle group IDs"
  value = {
    all_employees   = var.enable_joiner_patterns ? okta_group.all_employees[0].id : null
    all_contractors = var.enable_contractor_lifecycle ? okta_group.all_contractors[0].id : null
  }
}

# -----------------------------------------------------------------------------
# Department Groups
# -----------------------------------------------------------------------------

output "department_groups" {
  description = "Department group IDs"
  value = {
    for name, group in okta_group.departments : name => group.id
  }
}

# -----------------------------------------------------------------------------
# Joiner Groups
# -----------------------------------------------------------------------------

output "joiner_groups" {
  description = "Joiner (onboarding) group IDs"
  value = var.enable_joiner_patterns ? {
    staged_users = local.create_staged_group ? okta_group.staged_users[0].id : null
    new_hires    = local.create_new_hires_group ? okta_group.new_hires[0].id : null
  } : null
}

# -----------------------------------------------------------------------------
# Mover Groups
# -----------------------------------------------------------------------------

output "mover_groups" {
  description = "Mover (transfer) group IDs"
  value = var.enable_mover_patterns ? {
    in_transfer = local.create_transfer_group ? okta_group.in_transfer[0].id : null
  } : null
}

# -----------------------------------------------------------------------------
# Leaver Groups
# -----------------------------------------------------------------------------

output "leaver_groups" {
  description = "Leaver (offboarding) group IDs"
  value = var.enable_leaver_patterns ? {
    pending_offboard  = local.create_pending_offboard_group ? okta_group.pending_offboard[0].id : null
    deprovisioned     = local.create_former_group ? okta_group.deprovisioned[0].id : null
    suspended         = local.create_suspended_group ? okta_group.suspended[0].id : null
    former_employees  = local.create_former_group ? okta_group.former_employees[0].id : null
  } : null
}

# -----------------------------------------------------------------------------
# Contractor Groups
# -----------------------------------------------------------------------------

output "contractor_groups" {
  description = "Contractor lifecycle group IDs"
  value = var.enable_contractor_lifecycle ? {
    all_contractors       = okta_group.all_contractors[0].id
    limited_access        = local.create_access_tier_groups ? okta_group.contractor_limited[0].id : null
    standard_access       = local.create_access_tier_groups ? okta_group.contractor_standard[0].id : null
    with_end_date         = okta_group.contractors_with_end_date[0].id
    expiring_soon         = local.create_expiration_groups ? okta_group.contractor_expiring_soon[0].id : null
    final_notice          = local.create_expiration_groups ? okta_group.contractor_final_notice[0].id : null
    expired               = local.create_expiration_groups ? okta_group.contractor_expired[0].id : null
    no_manager            = local.create_no_manager_group ? okta_group.contractor_no_manager[0].id : null
  } : null
}

# -----------------------------------------------------------------------------
# Group Rules
# -----------------------------------------------------------------------------

output "group_rules" {
  description = "Created group rule IDs"
  value = {
    employees = var.enable_joiner_patterns ? okta_group_rule.all_employees[0].id : null
    contractors = var.enable_contractor_lifecycle ? okta_group_rule.all_contractors[0].id : null
    departments = { for k, v in okta_group_rule.departments : k => v.id }
    staged = local.create_staged_group ? okta_group_rule.staged_users[0].id : null
    deprovisioned = local.create_former_group ? okta_group_rule.deprovisioned[0].id : null
    suspended = local.create_suspended_group ? okta_group_rule.suspended[0].id : null
    contractors_with_end_date = var.enable_contractor_lifecycle ? okta_group_rule.contractors_with_end_date[0].id : null
    contractor_no_manager = local.create_no_manager_group ? okta_group_rule.contractor_no_manager[0].id : null
  }
}

# -----------------------------------------------------------------------------
# OIG Resources
# -----------------------------------------------------------------------------

output "entitlement_bundles" {
  description = "Created entitlement bundle IDs"
  value = var.enable_oig_integration ? {
    employee_default   = local.joiner.default_employee_bundle != "" ? okta_entitlement_bundle.employee_default[0].id : null
    contractor_default = (var.enable_contractor_lifecycle && local.joiner.default_contractor_bundle != "") ? okta_entitlement_bundle.contractor_default[0].id : null
    custom             = { for k, v in okta_entitlement_bundle.custom : k => v.id }
    department         = { for k, v in okta_entitlement_bundle.department : k => v.id }
  } : null
}

# -----------------------------------------------------------------------------
# Event Hooks
# -----------------------------------------------------------------------------

output "event_hooks" {
  description = "Created event hook IDs"
  value = {
    mover  = local.create_mover_event_hook ? okta_event_hook.mover[0].id : null
    leaver = local.create_leaver_event_hook ? okta_event_hook.leaver[0].id : null
  }
}

# -----------------------------------------------------------------------------
# Schema Properties
# -----------------------------------------------------------------------------

output "schema_properties" {
  description = "Created user schema property indexes"
  value = {
    lifecycle_status  = var.create_lifecycle_status_attribute ? okta_user_schema_property.lifecycle_status[0].index : null
    contract_end_date = local.create_end_date_attribute ? okta_user_schema_property.contract_end_date[0].index : null
  }
}

# -----------------------------------------------------------------------------
# Manager Link
# -----------------------------------------------------------------------------

output "manager_link" {
  description = "Manager link definition"
  value = var.enable_joiner_patterns ? {
    primary_name    = okta_link_definition.manager[0].primary_name
    associated_name = okta_link_definition.manager[0].associated_name
  } : null
}

# -----------------------------------------------------------------------------
# Configuration Summary
# -----------------------------------------------------------------------------

output "configuration" {
  description = "Module configuration summary"
  value = {
    organization_name       = var.organization_name
    joiner_enabled          = var.enable_joiner_patterns
    mover_enabled           = var.enable_mover_patterns
    leaver_enabled          = var.enable_leaver_patterns
    contractor_enabled      = var.enable_contractor_lifecycle
    oig_enabled             = var.enable_oig_integration
    departments_configured  = length(var.departments)
    user_types_created      = var.create_user_types ? length(var.user_types) : 0
  }
}

# -----------------------------------------------------------------------------
# All Groups (Convenience Output)
# -----------------------------------------------------------------------------

output "all_groups" {
  description = "All created group IDs in a flat map"
  value = merge(
    var.enable_joiner_patterns ? { all_employees = okta_group.all_employees[0].id } : {},
    var.enable_contractor_lifecycle ? { all_contractors = okta_group.all_contractors[0].id } : {},
    { for k, v in okta_group.departments : "dept_${k}" => v.id },
    local.create_staged_group ? { staged_users = okta_group.staged_users[0].id } : {},
    local.create_new_hires_group ? { new_hires = okta_group.new_hires[0].id } : {},
    local.create_transfer_group ? { in_transfer = okta_group.in_transfer[0].id } : {},
    local.create_pending_offboard_group ? { pending_offboard = okta_group.pending_offboard[0].id } : {},
    local.create_former_group ? { deprovisioned = okta_group.deprovisioned[0].id } : {},
    local.create_suspended_group ? { suspended = okta_group.suspended[0].id } : {},
    local.create_former_group ? { former_employees = okta_group.former_employees[0].id } : {},
    local.create_access_tier_groups ? { contractor_limited = okta_group.contractor_limited[0].id } : {},
    local.create_access_tier_groups ? { contractor_standard = okta_group.contractor_standard[0].id } : {},
    local.create_expiration_groups ? { contractor_expiring_soon = okta_group.contractor_expiring_soon[0].id } : {},
    local.create_expiration_groups ? { contractor_final_notice = okta_group.contractor_final_notice[0].id } : {},
    local.create_expiration_groups ? { contractor_expired = okta_group.contractor_expired[0].id } : {},
    var.enable_contractor_lifecycle ? { contractors_with_end_date = okta_group.contractors_with_end_date[0].id } : {},
    local.create_no_manager_group ? { contractor_no_manager = okta_group.contractor_no_manager[0].id } : {},
  )
}
