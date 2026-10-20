# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - Provider Requirements
# =============================================================================
# This module requires the Okta Terraform provider v7.0.0 or higher for
# OIG features (entitlement bundles, access certification campaigns).
# =============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    okta = {
      source  = "okta/okta"
      version = ">= 7.0.0, < 8.0.0"
    }
  }
}
