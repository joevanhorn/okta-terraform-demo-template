# =============================================================================
# SAML Federation Module - Variables
# =============================================================================
# This module supports two federation modes:
# - "sp" (Service Provider): Receive SAML assertions from external IdP
# - "idp" (Identity Provider): Send SAML assertions to external SP
# =============================================================================

# -----------------------------------------------------------------------------
# Required Variables
# -----------------------------------------------------------------------------

variable "federation_mode" {
  description = "Federation mode: 'sp' to receive assertions, 'idp' to send assertions"
  type        = string

  validation {
    condition     = contains(["sp", "idp"], var.federation_mode)
    error_message = "federation_mode must be 'sp' or 'idp'"
  }
}

variable "federation_name" {
  description = "Name for federation resources (used in resource naming)"
  type        = string
}

variable "okta_org_name" {
  description = "This Okta organization's subdomain (e.g., 'dev-12345')"
  type        = string
}

variable "okta_base_url" {
  description = "Okta base URL domain (e.g., 'oktapreview.com', 'okta.com')"
  type        = string
  default     = "okta.com"
}

# -----------------------------------------------------------------------------
# Remote State Configuration (Cross-Org Coordination)
# -----------------------------------------------------------------------------

variable "use_remote_state" {
  description = "Enable terraform_remote_state to read partner org outputs"
  type        = bool
  default     = false
}

variable "remote_state_backend" {
  description = "Remote state backend type ('s3' or 'local')"
  type        = string
  default     = "s3"

  validation {
    condition     = contains(["s3", "local"], var.remote_state_backend)
    error_message = "remote_state_backend must be 's3' or 'local'"
  }
}

variable "remote_state_config" {
  description = "Remote state backend configuration (bucket, key, region for S3; path for local)"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# SP Mode Variables (Receive Assertions from External IdP)
# -----------------------------------------------------------------------------
# Use these when federation_mode = "sp"
# Values can come from remote_state or be provided directly
# -----------------------------------------------------------------------------

variable "idp_name" {
  description = "Display name for the external IdP in Okta (SP mode)"
  type        = string
  default     = ""
}

variable "idp_issuer" {
  description = "SAML issuer/entity ID of the external IdP (SP mode, manual config)"
  type        = string
  default     = ""
}

variable "idp_sso_url" {
  description = "SSO URL of the external IdP (SP mode, manual config)"
  type        = string
  default     = ""
}

variable "idp_certificate" {
  description = "X.509 certificate (PEM format) of the external IdP (SP mode, manual config)"
  type        = string
  default     = ""
  sensitive   = true
}

# -----------------------------------------------------------------------------
# IdP Mode Variables (Send Assertions to External SP)
# -----------------------------------------------------------------------------
# Use these when federation_mode = "idp"
# Values can come from remote_state or be provided directly
# -----------------------------------------------------------------------------

variable "app_label" {
  description = "Label for the SAML federation app (IdP mode)"
  type        = string
  default     = ""
}

variable "sp_org_name" {
  description = "SP organization's Okta subdomain (IdP mode, manual config)"
  type        = string
  default     = ""
}

variable "sp_base_url" {
  description = "SP organization's Okta base URL domain (IdP mode, manual config)"
  type        = string
  default     = ""
}

variable "sp_idp_id" {
  description = "SP organization's IdP resource ID for ACS URL (IdP mode, manual config)"
  type        = string
  default     = ""
}

variable "sp_acs_url" {
  description = "SP's Assertion Consumer Service URL (IdP mode, for non-Okta SPs)"
  type        = string
  default     = ""
}

variable "sp_audience" {
  description = "SP's audience restriction/entity ID (IdP mode, for non-Okta SPs)"
  type        = string
  default     = ""
}

variable "attribute_statements" {
  description = "SAML attribute statements to include in assertions (IdP mode)"
  type = list(object({
    name         = string
    namespace    = optional(string, "urn:oasis:names:tc:SAML:2.0:attrname-format:unspecified")
    type         = optional(string, "EXPRESSION")
    values       = list(string)
    filter_type  = optional(string)
    filter_value = optional(string)
  }))
  default = []
}

variable "assigned_group_ids" {
  description = "Group IDs to assign to the federation app (IdP mode)"
  type        = list(string)
  default     = []
}

# -----------------------------------------------------------------------------
# JIT Provisioning Configuration (SP Mode)
# -----------------------------------------------------------------------------
# Controls how federated users are created/linked in the SP organization
# -----------------------------------------------------------------------------

variable "provisioning_action" {
  description = "User provisioning action: AUTO (JIT), DISABLED, CALL_OUT"
  type        = string
  default     = "AUTO"

  validation {
    condition     = contains(["AUTO", "DISABLED", "CALL_OUT"], var.provisioning_action)
    error_message = "provisioning_action must be 'AUTO', 'DISABLED', or 'CALL_OUT'"
  }
}

variable "account_link_action" {
  description = "Account linking action: AUTO (match by email), DISABLED, CALL_OUT"
  type        = string
  default     = "AUTO"

  validation {
    condition     = contains(["AUTO", "DISABLED", "CALL_OUT"], var.account_link_action)
    error_message = "account_link_action must be 'AUTO', 'DISABLED', or 'CALL_OUT'"
  }
}

variable "groups_action" {
  description = "Group sync action: NONE, SYNC, APPEND, ASSIGN"
  type        = string
  default     = "NONE"

  validation {
    condition     = contains(["NONE", "SYNC", "APPEND", "ASSIGN"], var.groups_action)
    error_message = "groups_action must be 'NONE', 'SYNC', 'APPEND', or 'ASSIGN'"
  }
}

variable "groups_attribute" {
  description = "SAML attribute name containing group information"
  type        = string
  default     = ""
}

variable "groups_assignment" {
  description = "Default group IDs to assign to federated users"
  type        = list(string)
  default     = []
}

variable "profile_master" {
  description = "Whether federated IdP should be the profile master"
  type        = bool
  default     = false
}

variable "subject_match_type" {
  description = "Subject match type: USERNAME, EMAIL, USERNAME_OR_EMAIL, CUSTOM_ATTRIBUTE"
  type        = string
  default     = "EMAIL"

  validation {
    condition     = contains(["USERNAME", "EMAIL", "USERNAME_OR_EMAIL", "CUSTOM_ATTRIBUTE"], var.subject_match_type)
    error_message = "subject_match_type must be 'USERNAME', 'EMAIL', 'USERNAME_OR_EMAIL', or 'CUSTOM_ATTRIBUTE'"
  }
}

variable "subject_match_attribute" {
  description = "Custom attribute for subject matching (when subject_match_type = CUSTOM_ATTRIBUTE)"
  type        = string
  default     = ""
}

variable "username_template" {
  description = "Okta EL template for username (SP mode)"
  type        = string
  default     = "idpuser.email"
}

# -----------------------------------------------------------------------------
# SAML Signature Configuration
# -----------------------------------------------------------------------------

variable "request_signature_algorithm" {
  description = "Algorithm for signing SAML requests: SHA-256 or SHA-1"
  type        = string
  default     = "SHA-256"

  validation {
    condition     = contains(["SHA-256", "SHA-1"], var.request_signature_algorithm)
    error_message = "request_signature_algorithm must be 'SHA-256' or 'SHA-1'"
  }
}

variable "request_signature_scope" {
  description = "Scope of request signing: REQUEST (AuthnRequest only), NONE"
  type        = string
  default     = "REQUEST"

  validation {
    condition     = contains(["REQUEST", "NONE"], var.request_signature_scope)
    error_message = "request_signature_scope must be 'REQUEST' or 'NONE'"
  }
}

variable "response_signature_algorithm" {
  description = "Algorithm for response signatures (IdP mode): RSA_SHA256 or RSA_SHA1"
  type        = string
  default     = "RSA_SHA256"

  validation {
    condition     = contains(["RSA_SHA256", "RSA_SHA1"], var.response_signature_algorithm)
    error_message = "response_signature_algorithm must be 'RSA_SHA256' or 'RSA_SHA1'"
  }
}

variable "response_signature_scope" {
  description = "What to sign in response (IdP mode): RESPONSE, ASSERTION, or ANY"
  type        = string
  default     = "ANY"

  validation {
    condition     = contains(["RESPONSE", "ASSERTION", "ANY"], var.response_signature_scope)
    error_message = "response_signature_scope must be 'RESPONSE', 'ASSERTION', or 'ANY'"
  }
}

variable "assertion_signed" {
  description = "Sign SAML assertions (IdP mode)"
  type        = bool
  default     = true
}

variable "digest_algorithm" {
  description = "Digest algorithm for assertions (IdP mode): SHA256 or SHA1"
  type        = string
  default     = "SHA256"

  validation {
    condition     = contains(["SHA256", "SHA1"], var.digest_algorithm)
    error_message = "digest_algorithm must be 'SHA256' or 'SHA1'"
  }
}

variable "honor_force_authn" {
  description = "Honor ForceAuthn in SAML request (IdP mode)"
  type        = bool
  default     = true
}

# -----------------------------------------------------------------------------
# IdP Discovery / Routing Rules (SP Mode)
# -----------------------------------------------------------------------------
# Optional: Route users to this IdP based on email domain
# -----------------------------------------------------------------------------

variable "enable_routing_rule" {
  description = "Enable IdP discovery routing rule (SP mode)"
  type        = bool
  default     = false
}

variable "routing_policy_id" {
  description = "IdP discovery policy ID for routing rule (SP mode)"
  type        = string
  default     = ""
}

variable "routing_domain_suffix" {
  description = "Email domain suffix for routing (e.g., '@partner.com')"
  type        = string
  default     = ""
}

variable "routing_rule_priority" {
  description = "Priority for the routing rule (lower = higher priority)"
  type        = number
  default     = 1
}

# -----------------------------------------------------------------------------
# Status and Lifecycle
# -----------------------------------------------------------------------------

variable "status" {
  description = "IdP or App status: ACTIVE or INACTIVE"
  type        = string
  default     = "ACTIVE"

  validation {
    condition     = contains(["ACTIVE", "INACTIVE"], var.status)
    error_message = "status must be 'ACTIVE' or 'INACTIVE'"
  }
}

# -----------------------------------------------------------------------------
# Tags and Metadata
# -----------------------------------------------------------------------------

variable "tags" {
  description = "Tags to apply to resources (for organization)"
  type        = map(string)
  default     = {}
}
