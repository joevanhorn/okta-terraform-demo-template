# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - Leaver (Offboarding) Resources
# =============================================================================
# Handles user deprovisioning, access revocation, and audit trail preservation
# =============================================================================

# -----------------------------------------------------------------------------
# Pending Offboard Group
# -----------------------------------------------------------------------------
# Users marked for offboarding (access being revoked)

resource "okta_group" "pending_offboard" {
  count = local.create_pending_offboard_group ? 1 : 0

  name        = "${local.name_prefix} - Pending Offboard"
  description = "Users marked for offboarding (access being revoked)"
}

# -----------------------------------------------------------------------------
# Deprovisioned Users Group
# -----------------------------------------------------------------------------
# Track deprovisioned users for audit purposes

resource "okta_group" "deprovisioned" {
  count = local.create_former_group ? 1 : 0

  name        = "${local.name_prefix} - Deprovisioned"
  description = "Deprovisioned users (DEPROVISIONED status)"
}

resource "okta_group_rule" "deprovisioned" {
  count = local.create_former_group ? 1 : 0

  name              = "Auto-assign Deprovisioned Users"
  status            = "ACTIVE"
  group_assignments = [okta_group.deprovisioned[0].id]
  expression_type   = "urn:okta:expression:1.0"
  expression_value  = local.deprovisioned_expression
}

# -----------------------------------------------------------------------------
# Suspended Users Group
# -----------------------------------------------------------------------------
# Track suspended users

resource "okta_group" "suspended" {
  count = local.create_suspended_group ? 1 : 0

  name        = "${local.name_prefix} - Suspended Users"
  description = "Users with suspended accounts"
}

resource "okta_group_rule" "suspended" {
  count = local.create_suspended_group ? 1 : 0

  name              = "Auto-assign Suspended Users"
  status            = "ACTIVE"
  group_assignments = [okta_group.suspended[0].id]
  expression_type   = "urn:okta:expression:1.0"
  expression_value  = local.suspended_expression
}

# -----------------------------------------------------------------------------
# Former Employees Group
# -----------------------------------------------------------------------------
# Historical record of former employees (for audit)

resource "okta_group" "former_employees" {
  count = local.create_former_group ? 1 : 0

  name        = "${local.name_prefix} - Former Employees"
  description = "Historical record of former employees"
}

# -----------------------------------------------------------------------------
# Leaver Event Hook
# -----------------------------------------------------------------------------
# Webhook to notify external systems of offboarding events

resource "okta_event_hook" "leaver" {
  count = local.create_leaver_event_hook ? 1 : 0

  name   = "${local.name_prefix} - Offboarding Notifications"
  status = "ACTIVE"
  events = local.leaver.webhook_events

  channel {
    type    = "HTTP"
    version = "1.0.0"
    uri     = local.leaver.webhook_url
  }
}
