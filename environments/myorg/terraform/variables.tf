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
