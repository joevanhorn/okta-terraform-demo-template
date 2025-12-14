variable "okta_org_name" {
  description = "Okta organization name (e.g., dev-123456)"
  type        = string
  sensitive   = true
}

variable "okta_base_url" {
  description = "Okta base URL (e.g., okta.com, oktapreview.com)"
  type        = string
  default     = "okta.com"
}

variable "okta_api_token" {
  description = "Okta API token with appropriate permissions"
  type        = string
  sensitive   = true
}

# ==============================================================================
# SCIM Application Variables
# ==============================================================================

variable "scim_environment" {
  description = "Environment name for SCIM server state lookup (must match infrastructure/scim-server deployment)"
  type        = string
  default     = "myorg"
}

variable "scim_aws_region" {
  description = "AWS region where SCIM server state is stored"
  type        = string
  default     = "us-east-1"
}

variable "scim_app_label" {
  description = "Label for SCIM application in Okta"
  type        = string
  default     = "Custom SCIM Demo App"
}

variable "scim_app_group_id" {
  description = "Optional: Group ID to automatically assign to SCIM app"
  type        = string
  default     = ""
}

# ==============================================================================
# OKTA PRIVILEGED ACCESS (OPA) VARIABLES - OPTIONAL
# ==============================================================================
# Uncomment these variables when enabling the oktapam provider
# See docs/OPA_SETUP.md for configuration details

# variable "oktapam_key" {
#   description = "OPA service user key (ID) - from service user creation"
#   type        = string
#   sensitive   = true
# }

# variable "oktapam_secret" {
#   description = "OPA service user secret - from service user creation"
#   type        = string
#   sensitive   = true
# }

# variable "oktapam_team" {
#   description = "OPA team name (the team the service account belongs to)"
#   type        = string
# }
