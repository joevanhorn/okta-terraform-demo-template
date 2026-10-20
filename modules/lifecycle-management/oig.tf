# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - OIG Integration
# =============================================================================
# Creates entitlement bundles and access certification campaigns for lifecycle
# governance. OIG features require an Okta Identity Governance license.
#
# Every okta_entitlement_bundle must target an application that has
# Entitlement Management enabled. Set var.oig_target_app_id (or a per-bundle
# target_app_id) or the bundle is skipped.
# =============================================================================

# -----------------------------------------------------------------------------
# Default Employee Entitlement Bundle
# -----------------------------------------------------------------------------
# Standard access bundle for new employees

resource "okta_entitlement_bundle" "employee_default" {
  count = local.create_employee_bundle ? 1 : 0

  name        = local.joiner.default_employee_bundle
  description = "Default entitlement bundle for new employees - includes standard organizational tools"
  status      = "ACTIVE"

  target {
    external_id = local.joiner.default_employee_bundle_app_id
    type        = "APPLICATION"
  }

  # This creates the bundle DEFINITION only (no entitlement values yet).
  # Principal assignments are managed in Okta Admin UI per CLAUDE.md guidance.
}

# -----------------------------------------------------------------------------
# Default Contractor Entitlement Bundle
# -----------------------------------------------------------------------------
# Limited access bundle for contractors

resource "okta_entitlement_bundle" "contractor_default" {
  count = local.create_contractor_bundle ? 1 : 0

  name        = local.joiner.default_contractor_bundle
  description = "Limited access bundle for contractors - time-bounded access to essential tools"
  status      = "ACTIVE"

  target {
    external_id = local.joiner.default_contractor_bundle_app_id
    type        = "APPLICATION"
  }
}

# -----------------------------------------------------------------------------
# Custom Entitlement Bundles
# -----------------------------------------------------------------------------
# User-defined bundles for specific access patterns

resource "okta_entitlement_bundle" "custom" {
  for_each = local.custom_bundles

  name        = each.value.name
  description = each.value.description
  status      = each.value.status

  target {
    external_id = each.value.target_app_id
    type        = "APPLICATION"
  }
}

# -----------------------------------------------------------------------------
# Department Entitlement Bundles
# -----------------------------------------------------------------------------
# Bundles for department-specific access

resource "okta_entitlement_bundle" "department" {
  for_each = local.department_bundles

  name        = each.value.name
  description = "Access bundle for ${each.key} department members"
  status      = "ACTIVE"

  target {
    external_id = each.value.target_app_id
    type        = "APPLICATION"
  }
}

# -----------------------------------------------------------------------------
# Access Certification Campaigns (okta_campaign)
# -----------------------------------------------------------------------------
# Campaigns need a reviewer and concrete target resources, which this module
# does not know about. The example below shows the real okta_campaign schema;
# copy it into your environment and fill in the IDs.
# -----------------------------------------------------------------------------

# resource "okta_campaign" "contractor_quarterly" {
#   count = local.create_oig_resources && var.enable_contractor_lifecycle ? 1 : 0
#
#   name          = "${local.name_prefix} - Quarterly Contractor Review"
#   description   = "Quarterly review of all contractor access for compliance"
#   campaign_type = "RESOURCE"
#
#   schedule_settings {
#     type             = "RECURRING"
#     start_date       = "2027-01-01T08:00:00.000Z"
#     duration_in_days = 14
#     time_zone        = "America/Los_Angeles"
#     recurrence {
#       interval       = "P3M"
#       repeat_on_type = "SAME_DAY_AS_START_DATE"
#     }
#   }
#
#   resource_settings {
#     type = "GROUP"
#     target_resources {
#       resource_id   = okta_group.all_contractors[0].id
#       resource_type = "GROUP"
#     }
#   }
#
#   principal_scope_settings {
#     type      = "GROUPS"
#     group_ids = [okta_group.all_contractors[0].id]
#   }
#
#   reviewer_settings {
#     type                   = "RESOURCE_OWNER"
#     fallback_reviewer_id   = "<okta-user-id-of-fallback-reviewer>"
#     self_review_disabled   = true
#     justification_required = true
#   }
#
#   remediation_settings {
#     access_approved = "NO_ACTION"
#     access_revoked  = "DENY"
#     no_response     = "DENY"
#   }
#
#   notification_settings {
#     notify_reviewer_when_review_assigned      = true
#     notify_reviewer_during_midpoint_of_review = true
#     notify_reviewer_when_overdue              = true
#     notify_review_period_end                  = true
#     notify_reviewer_at_campaign_end           = true
#   }
# }
