# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - Joiner (Onboarding) Resources
# =============================================================================
# Handles new employee and contractor onboarding patterns
# =============================================================================

# -----------------------------------------------------------------------------
# Staged Users Group
# -----------------------------------------------------------------------------
# Track users created in STAGED status (pre-activation)

resource "okta_group" "staged_users" {
  count = local.create_staged_group ? 1 : 0

  name        = "${local.name_prefix} - Staged Users"
  description = "Users awaiting activation (STAGED status)"
}

resource "okta_group_rule" "staged_users" {
  count = local.create_staged_group ? 1 : 0

  name              = "Auto-assign Staged Users"
  status            = "ACTIVE"
  group_assignments = [okta_group.staged_users[0].id]
  expression_type   = "urn:okta:expression:1.0"
  expression_value  = local.staged_expression
}

# -----------------------------------------------------------------------------
# New Hires Group
# -----------------------------------------------------------------------------
# Track recently onboarded users (for 30-day reviews, etc.)

resource "okta_group" "new_hires" {
  count = local.create_new_hires_group ? 1 : 0

  name        = "${local.name_prefix} - New Hires"
  description = "Recently onboarded users (for tracking and reviews)"
}

# -----------------------------------------------------------------------------
# Custom Onboarding Rules
# -----------------------------------------------------------------------------
# User-defined rules for specific onboarding scenarios

resource "okta_group_rule" "custom_joiner" {
  for_each = var.enable_joiner_patterns ? {
    for rule in local.joiner.auto_assign_rules : rule.name => rule
  } : {}

  name              = each.value.name
  status            = try(each.value.status, "ACTIVE")
  group_assignments = each.value.target_groups
  expression_type   = "urn:okta:expression:1.0"
  expression_value  = each.value.expression
}

# -----------------------------------------------------------------------------
# Manager Link Definition
# -----------------------------------------------------------------------------
# Ensure manager relationship link type exists

resource "okta_link_definition" "manager" {
  count = var.enable_joiner_patterns ? 1 : 0

  primary_name           = local.joiner.manager_link_name
  primary_title          = "Manager"
  primary_description    = "User's direct manager"
  associated_name        = "directReport"
  associated_title       = "Direct Report"
  associated_description = "User's direct reports"
}
