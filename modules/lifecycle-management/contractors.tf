# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - Contractor Lifecycle Resources
# =============================================================================
# Handles contractor-specific patterns: end-date tracking, access tiers
# =============================================================================

# -----------------------------------------------------------------------------
# Contract End Date Schema Property
# -----------------------------------------------------------------------------
# Custom attribute to track contractor end dates

resource "okta_user_schema_property" "contract_end_date" {
  count = local.create_end_date_attribute ? 1 : 0

  index       = local.contractor.end_date_attribute
  title       = "Contract End Date"
  type        = "string"
  description = "End date for contractor access (YYYY-MM-DD format)"
  master      = "PROFILE_MASTER"
  scope       = "NONE"

  # Pattern for date validation (YYYY-MM-DD)
  pattern = "^\\d{4}-\\d{2}-\\d{2}$"
}

# -----------------------------------------------------------------------------
# Contractor Access Tier Groups
# -----------------------------------------------------------------------------
# Different access levels for contractors

resource "okta_group" "contractor_limited" {
  count = local.create_access_tier_groups ? 1 : 0

  name        = "${local.name_prefix} - Contractor Limited Access"
  description = "Limited access tier for contractors (basic tools only)"
}

resource "okta_group" "contractor_standard" {
  count = local.create_access_tier_groups ? 1 : 0

  name        = "${local.name_prefix} - Contractor Standard Access"
  description = "Standard access tier for contractors (department-specific tools)"
}

# -----------------------------------------------------------------------------
# Contractor Expiration Warning Groups
# -----------------------------------------------------------------------------
# Track contractors approaching their end date

resource "okta_group" "contractor_expiring_soon" {
  count = local.create_expiration_groups ? 1 : 0

  name        = "${local.name_prefix} - Contractors Expiring Soon"
  description = "Contractors with end date within ${local.contractor.warning_days} days"
}

resource "okta_group" "contractor_final_notice" {
  count = local.create_expiration_groups ? 1 : 0

  name        = "${local.name_prefix} - Contractors Final Notice"
  description = "Contractors with end date within ${local.contractor.final_notice_days} days"
}

resource "okta_group" "contractor_expired" {
  count = local.create_expiration_groups ? 1 : 0

  name        = "${local.name_prefix} - Contractors Expired"
  description = "Contractors past their end date (pending deprovisioning)"
}

# -----------------------------------------------------------------------------
# Contractors with End Date Group
# -----------------------------------------------------------------------------
# Track all contractors that have an end date set

resource "okta_group" "contractors_with_end_date" {
  count = local.create_contractor_resources ? 1 : 0

  name        = "${local.name_prefix} - Contractors With End Date"
  description = "Contractors with contract end date configured"
}

resource "okta_group_rule" "contractors_with_end_date" {
  count = local.create_contractor_resources ? 1 : 0

  name              = "Contractors with End Date Set"
  status            = "ACTIVE"
  group_assignments = [okta_group.contractors_with_end_date[0].id]
  expression_type   = "urn:okta:expression:1.0"
  expression_value  = local.contractor_with_end_date_expression
}

# -----------------------------------------------------------------------------
# Contractor No Manager Group (Compliance)
# -----------------------------------------------------------------------------
# Track contractors without manager assignment (compliance violation)

resource "okta_group" "contractor_no_manager" {
  count = local.create_no_manager_group ? 1 : 0

  name        = "${local.name_prefix} - Contractors Without Manager"
  description = "Contractors missing required manager assignment (compliance)"
}

resource "okta_group_rule" "contractor_no_manager" {
  count = local.create_no_manager_group ? 1 : 0

  name              = "Flag Contractors Without Manager"
  status            = "ACTIVE"
  group_assignments = [okta_group.contractor_no_manager[0].id]
  expression_type   = "urn:okta:expression:1.0"
  expression_value  = local.contractor_no_manager_expression
}
