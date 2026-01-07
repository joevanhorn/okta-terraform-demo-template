# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - OIG Integration
# =============================================================================
# Creates entitlement bundles and access review campaigns for lifecycle governance
# Note: OIG features require Okta Identity Governance license
# =============================================================================

# -----------------------------------------------------------------------------
# Default Employee Entitlement Bundle
# -----------------------------------------------------------------------------
# Standard access bundle for new employees

resource "okta_entitlement_bundle" "employee_default" {
  count = local.create_oig_resources && local.joiner.default_employee_bundle != "" ? 1 : 0

  name        = local.joiner.default_employee_bundle
  description = "Default entitlement bundle for new employees - includes standard organizational tools"
  status      = "ACTIVE"

  # Note: Target and entitlements configuration depends on specific apps
  # This creates the bundle DEFINITION only
  # Principal assignments are managed in Okta Admin UI per CLAUDE.md guidance
}

# -----------------------------------------------------------------------------
# Default Contractor Entitlement Bundle
# -----------------------------------------------------------------------------
# Limited access bundle for contractors

resource "okta_entitlement_bundle" "contractor_default" {
  count = (
    local.create_oig_resources &&
    var.enable_contractor_lifecycle &&
    local.joiner.default_contractor_bundle != ""
  ) ? 1 : 0

  name        = local.joiner.default_contractor_bundle
  description = "Limited access bundle for contractors - time-bounded access to essential tools"
  status      = "ACTIVE"
}

# -----------------------------------------------------------------------------
# Custom Entitlement Bundles
# -----------------------------------------------------------------------------
# User-defined bundles for specific access patterns

resource "okta_entitlement_bundle" "custom" {
  for_each = local.create_oig_resources ? {
    for bundle in var.entitlement_bundles : bundle.name => bundle
  } : {}

  name        = each.value.name
  description = each.value.description
  status      = each.value.status
}

# -----------------------------------------------------------------------------
# Department Entitlement Bundles
# -----------------------------------------------------------------------------
# Bundles for department-specific access

resource "okta_entitlement_bundle" "department" {
  for_each = local.create_oig_resources ? {
    for dept in var.departments : dept.name => dept
    if dept.entitlement_bundle != null && dept.entitlement_bundle != ""
  } : {}

  name        = each.value.entitlement_bundle
  description = "Access bundle for ${each.key} department members"
  status      = "ACTIVE"
}

# -----------------------------------------------------------------------------
# Access Review Campaigns
# -----------------------------------------------------------------------------
# Note: okta_reviews resource schema may vary by provider version
# These are placeholder definitions - adjust based on actual provider support
# -----------------------------------------------------------------------------

# Quarterly Contractor Access Review
# resource "okta_reviews" "contractor_quarterly" {
#   count = local.create_oig_resources && var.enable_contractor_lifecycle ? 1 : 0
#
#   name        = "${local.name_prefix} - Quarterly Contractor Review"
#   description = "Quarterly review of all contractor access for compliance"
#   # Additional configuration based on provider schema
# }

# New Hire 30-Day Review
# resource "okta_reviews" "new_hire" {
#   count = local.create_oig_resources && var.enable_joiner_patterns ? 1 : 0
#
#   name        = "${local.name_prefix} - New Hire 30-Day Review"
#   description = "Review access for employees in their first 30 days"
# }

# Departure Access Review
# resource "okta_reviews" "departure" {
#   count = local.create_oig_resources && var.enable_leaver_patterns ? 1 : 0
#
#   name        = "${local.name_prefix} - Departure Access Review"
#   description = "Final review of departing user's access for audit trail"
# }
