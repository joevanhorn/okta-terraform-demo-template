# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - Mover (Transfer) Resources
# =============================================================================
# Handles department changes, role transfers, and manager updates
# =============================================================================

# -----------------------------------------------------------------------------
# Transfer Tracking Group
# -----------------------------------------------------------------------------
# Temporary group for users undergoing role/department transfers

resource "okta_group" "in_transfer" {
  count = local.create_transfer_group ? 1 : 0

  name        = "${local.name_prefix} - In Transfer"
  description = "Users currently undergoing department/role transfer"
}

# -----------------------------------------------------------------------------
# Mover Event Hook
# -----------------------------------------------------------------------------
# Webhook to notify external systems of profile changes

resource "okta_event_hook" "mover" {
  count = local.create_mover_event_hook ? 1 : 0

  name   = "${local.name_prefix} - Transfer Notifications"
  status = "ACTIVE"
  events = local.mover.webhook_events

  channel {
    type    = "HTTP"
    version = "1.0.0"
    uri     = local.mover.webhook_url
  }
}
