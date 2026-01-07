# =============================================================================
# LIFECYCLE MANAGEMENT MODULE - Provider Requirements
# =============================================================================
# This module requires the Okta Terraform provider v6.4.0 or higher for
# OIG features (entitlement bundles, access reviews).
# =============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    okta = {
      source  = "okta/okta"
      version = ">= 6.4.0, < 7.0.0"
    }
  }
}
