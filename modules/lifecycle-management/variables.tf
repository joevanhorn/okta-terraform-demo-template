# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - Variables
# =============================================================================
# This module supports comprehensive lifecycle management including:
# - Joiner (Onboarding): Auto-assignment, default entitlements, manager setup
# - Mover (Transfer): Department change handling, role reassignment
# - Leaver (Offboarding): Deprovisioning workflows, access revocation
# - Contractor Lifecycle: End-date expiration, limited access tiers
# =============================================================================

# -----------------------------------------------------------------------------
# Module Enable Flags
# -----------------------------------------------------------------------------

variable "enable_joiner_patterns" {
  description = "Enable Joiner (onboarding) lifecycle patterns"
  type        = bool
  default     = true
}

variable "enable_mover_patterns" {
  description = "Enable Mover (transfer) lifecycle patterns"
  type        = bool
  default     = true
}

variable "enable_leaver_patterns" {
  description = "Enable Leaver (offboarding) lifecycle patterns"
  type        = bool
  default     = true
}

variable "enable_contractor_lifecycle" {
  description = "Enable contractor-specific lifecycle management"
  type        = bool
  default     = true
}

variable "enable_oig_integration" {
  description = "Enable OIG integration (entitlement bundles, access reviews)"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Organization Configuration
# -----------------------------------------------------------------------------

variable "organization_name" {
  description = "Organization name for resource naming and descriptions"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names (defaults to organization_name)"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# User Types Configuration
# -----------------------------------------------------------------------------

variable "create_user_types" {
  description = "Create custom user types for lifecycle management"
  type        = bool
  default     = true
}

variable "user_types" {
  description = "User types to create for lifecycle management"
  type = list(object({
    name         = string
    display_name = string
    description  = string
  }))
  default = [
    {
      name         = "employee"
      display_name = "Employee"
      description  = "Full-time and part-time employees"
    },
    {
      name         = "contractor"
      display_name = "Contractor"
      description  = "External contractors with time-limited access"
    }
  ]
}

# -----------------------------------------------------------------------------
# Department Configuration
# -----------------------------------------------------------------------------

variable "departments" {
  description = "Departments for group rule auto-assignment"
  type = list(object({
    name               = string
    group_name         = optional(string)
    group_description  = optional(string)
    entitlement_bundle = optional(string)
  }))
  default = []
}

# -----------------------------------------------------------------------------
# Joiner Configuration
# -----------------------------------------------------------------------------

variable "joiner_config" {
  description = "Configuration for Joiner (onboarding) patterns"
  type = object({
    # Auto-assign rules based on user attributes
    auto_assign_rules = optional(list(object({
      name          = string
      expression    = string
      target_groups = list(string)
      status        = optional(string, "ACTIVE")
    })), [])

    # Default entitlement bundle for new employees
    default_employee_bundle = optional(string, "")

    # Default entitlement bundle for new contractors
    default_contractor_bundle = optional(string, "")

    # Enable staged user support (users created in STAGED status)
    enable_staged_users = optional(bool, true)

    # Create new hires tracking group
    create_new_hires_group = optional(bool, true)

    # Manager link definition name
    manager_link_name = optional(string, "manager")
  })
  default = {}
}

# -----------------------------------------------------------------------------
# Mover Configuration
# -----------------------------------------------------------------------------

variable "mover_config" {
  description = "Configuration for Mover (transfer) patterns"
  type = object({
    # Create transfer tracking group
    create_transfer_group = optional(bool, true)

    # Webhook URL for transfer notifications
    webhook_url = optional(string, "")

    # Events to trigger webhook
    webhook_events = optional(list(string), [
      "user.account.update_profile",
      "group.user_membership.add",
      "group.user_membership.remove"
    ])
  })
  default = {}
}

# -----------------------------------------------------------------------------
# Leaver Configuration
# -----------------------------------------------------------------------------

variable "leaver_config" {
  description = "Configuration for Leaver (offboarding) patterns"
  type = object({
    # Webhook URL for offboarding notifications
    webhook_url = optional(string, "")

    # Events to trigger webhook
    webhook_events = optional(list(string), [
      "user.lifecycle.deactivate",
      "user.lifecycle.suspend"
    ])

    # Create "Former Employees" group for deprovisioned users
    create_former_group = optional(bool, true)

    # Create suspended users group
    create_suspended_group = optional(bool, true)

    # Create pending offboard group
    create_pending_offboard_group = optional(bool, true)
  })
  default = {}
}

# -----------------------------------------------------------------------------
# Contractor Configuration
# -----------------------------------------------------------------------------

variable "contractor_config" {
  description = "Configuration for contractor lifecycle management"
  type = object({
    # Custom attribute for contract end date
    end_date_attribute = optional(string, "contractEndDate")

    # Create custom schema property for end date
    create_end_date_attribute = optional(bool, true)

    # Days before expiration to trigger warning
    warning_days = optional(number, 30)

    # Days before expiration to trigger final notice
    final_notice_days = optional(number, 7)

    # Separate contractor user type name
    user_type_name = optional(string, "contractor")

    # Create expiration warning groups
    create_expiration_groups = optional(bool, true)

    # Create access tier groups
    create_access_tier_groups = optional(bool, true)

    # Require manager assignment for contractors
    require_manager = optional(bool, true)

    # Create no-manager compliance group
    create_no_manager_group = optional(bool, true)
  })
  default = {}
}

# -----------------------------------------------------------------------------
# OIG Entitlement Bundles Configuration
# -----------------------------------------------------------------------------

variable "entitlement_bundles" {
  description = "Entitlement bundles to create for lifecycle management"
  type = list(object({
    name        = string
    description = string
    status      = optional(string, "ACTIVE")
  }))
  default = []
}

# -----------------------------------------------------------------------------
# Event Hook Configuration
# -----------------------------------------------------------------------------

variable "event_hooks" {
  description = "Custom event hooks for lifecycle notifications"
  type = list(object({
    name   = string
    url    = string
    events = list(string)
    status = optional(string, "ACTIVE")
  }))
  default = []
}

# -----------------------------------------------------------------------------
# Schema Properties Configuration
# -----------------------------------------------------------------------------

variable "create_lifecycle_status_attribute" {
  description = "Create lifecycleStatus custom attribute"
  type        = bool
  default     = true
}

variable "lifecycle_status_values" {
  description = "Valid values for lifecycleStatus attribute"
  type        = list(string)
  default     = ["ONBOARDING", "ACTIVE", "TRANSFERRING", "OFFBOARDING"]
}

# -----------------------------------------------------------------------------
# Tags and Metadata
# -----------------------------------------------------------------------------

variable "tags" {
  description = "Tags to apply to resources for organization"
  type        = map(string)
  default     = {}
}
