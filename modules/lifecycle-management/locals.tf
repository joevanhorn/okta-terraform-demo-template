# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - Local Values
# =============================================================================
# Computes derived values, builds expressions, and handles defaults
# =============================================================================

locals {
  # ---------------------------------------------------------------------------
  # Naming Convention
  # ---------------------------------------------------------------------------
  name_prefix = coalesce(var.name_prefix, var.organization_name)

  # ---------------------------------------------------------------------------
  # User Type Processing
  # ---------------------------------------------------------------------------
  user_type_map = {
    for ut in var.user_types : ut.name => ut
  }

  # Check if contractor user type is defined
  has_contractor_type = contains(keys(local.user_type_map), var.contractor_config.user_type_name)

  # ---------------------------------------------------------------------------
  # Department Group Processing
  # ---------------------------------------------------------------------------
  department_groups = {
    for dept in var.departments : dept.name => {
      name        = coalesce(dept.group_name, "${dept.name} Department")
      description = coalesce(dept.group_description, "Auto-managed group for ${dept.name} department members")
    }
  }

  # Department-based auto-assignment rules
  department_rules = {
    for dept_name, dept in local.department_groups : "dept_${lower(replace(replace(dept_name, " ", "_"), "-", "_"))}" => {
      name             = "Auto-assign ${dept_name}"
      expression       = "user.department==\"${dept_name}\""
      target_group_key = dept_name
    }
  }

  # ---------------------------------------------------------------------------
  # Expression Builders
  # ---------------------------------------------------------------------------

  # Expression to identify employees (default user type or explicit employee type)
  employee_expression = "user.userType==\"employee\" OR user.userType==null"

  # Expression to identify contractors
  contractor_expression = "user.userType==\"${var.contractor_config.user_type_name}\""

  # Expression to identify staged users
  staged_expression = "user.status==\"STAGED\""

  # Expression to identify deprovisioned users
  deprovisioned_expression = "user.status==\"DEPROVISIONED\""

  # Expression to identify suspended users
  suspended_expression = "user.status==\"SUSPENDED\""

  # Expression to identify contractors with end date set
  contractor_with_end_date_expression = "${local.contractor_expression} AND user.${var.contractor_config.end_date_attribute}!=null"

  # Expression to identify contractors without manager
  contractor_no_manager_expression = "${local.contractor_expression} AND user.managerId==null"

  # ---------------------------------------------------------------------------
  # Joiner Configuration Processing
  # ---------------------------------------------------------------------------

  # Merge default joiner config with provided config
  joiner = {
    auto_assign_rules         = try(var.joiner_config.auto_assign_rules, [])
    default_employee_bundle   = try(var.joiner_config.default_employee_bundle, "")
    default_contractor_bundle = try(var.joiner_config.default_contractor_bundle, "")
    enable_staged_users       = try(var.joiner_config.enable_staged_users, true)
    create_new_hires_group    = try(var.joiner_config.create_new_hires_group, true)
    manager_link_name         = try(var.joiner_config.manager_link_name, "manager")
  }

  # ---------------------------------------------------------------------------
  # Mover Configuration Processing
  # ---------------------------------------------------------------------------

  mover = {
    create_transfer_group = try(var.mover_config.create_transfer_group, true)
    webhook_url           = try(var.mover_config.webhook_url, "")
    webhook_events = try(var.mover_config.webhook_events, [
      "user.account.update_profile",
      "group.user_membership.add",
      "group.user_membership.remove"
    ])
  }

  # ---------------------------------------------------------------------------
  # Leaver Configuration Processing
  # ---------------------------------------------------------------------------

  leaver = {
    webhook_url = try(var.leaver_config.webhook_url, "")
    webhook_events = try(var.leaver_config.webhook_events, [
      "user.lifecycle.deactivate",
      "user.lifecycle.suspend"
    ])
    create_former_group           = try(var.leaver_config.create_former_group, true)
    create_suspended_group        = try(var.leaver_config.create_suspended_group, true)
    create_pending_offboard_group = try(var.leaver_config.create_pending_offboard_group, true)
  }

  # ---------------------------------------------------------------------------
  # Contractor Configuration Processing
  # ---------------------------------------------------------------------------

  contractor = {
    end_date_attribute         = try(var.contractor_config.end_date_attribute, "contractEndDate")
    create_end_date_attribute  = try(var.contractor_config.create_end_date_attribute, true)
    warning_days               = try(var.contractor_config.warning_days, 30)
    final_notice_days          = try(var.contractor_config.final_notice_days, 7)
    user_type_name             = try(var.contractor_config.user_type_name, "contractor")
    create_expiration_groups   = try(var.contractor_config.create_expiration_groups, true)
    create_access_tier_groups  = try(var.contractor_config.create_access_tier_groups, true)
    require_manager            = try(var.contractor_config.require_manager, true)
    create_no_manager_group    = try(var.contractor_config.create_no_manager_group, true)
  }

  # ---------------------------------------------------------------------------
  # Lifecycle Event Categories
  # ---------------------------------------------------------------------------

  joiner_events = [
    "user.lifecycle.create",
    "user.lifecycle.activate",
    "user.account.update_profile"
  ]

  mover_events = [
    "user.account.update_profile",
    "group.user_membership.add",
    "group.user_membership.remove"
  ]

  leaver_events = [
    "user.lifecycle.deactivate",
    "user.lifecycle.suspend",
    "user.lifecycle.delete.initiated"
  ]

  # ---------------------------------------------------------------------------
  # Resource Creation Conditions
  # ---------------------------------------------------------------------------

  # Joiner conditions
  create_joiner_resources = var.enable_joiner_patterns
  create_staged_group     = local.create_joiner_resources && local.joiner.enable_staged_users
  create_new_hires_group  = local.create_joiner_resources && local.joiner.create_new_hires_group

  # Mover conditions
  create_mover_resources  = var.enable_mover_patterns
  create_transfer_group   = local.create_mover_resources && local.mover.create_transfer_group
  create_mover_event_hook = local.create_mover_resources && local.mover.webhook_url != ""

  # Leaver conditions
  create_leaver_resources       = var.enable_leaver_patterns
  create_former_group           = local.create_leaver_resources && local.leaver.create_former_group
  create_suspended_group        = local.create_leaver_resources && local.leaver.create_suspended_group
  create_pending_offboard_group = local.create_leaver_resources && local.leaver.create_pending_offboard_group
  create_leaver_event_hook      = local.create_leaver_resources && local.leaver.webhook_url != ""

  # Contractor conditions
  create_contractor_resources   = var.enable_contractor_lifecycle
  create_expiration_groups      = local.create_contractor_resources && local.contractor.create_expiration_groups
  create_access_tier_groups     = local.create_contractor_resources && local.contractor.create_access_tier_groups
  create_no_manager_group       = local.create_contractor_resources && local.contractor.require_manager && local.contractor.create_no_manager_group
  create_end_date_attribute     = local.create_contractor_resources && local.contractor.create_end_date_attribute

  # OIG conditions
  create_oig_resources = var.enable_oig_integration

  # ---------------------------------------------------------------------------
  # Common Tags
  # ---------------------------------------------------------------------------
  common_tags = merge(var.tags, {
    Module  = "lifecycle-management"
    Version = "1.0.0"
  })
}
