terraform {
  required_version = ">= 1.9.0"

  required_providers {
    okta = {
      source  = "okta/okta"
      version = ">= 6.4.0, < 7.0.0" # Auto-update to latest 6.x
    }

    # Okta Privileged Access (OPA) Provider - Optional
    # Uncomment to enable OPA resource management
    # See docs/OPA_SETUP.md for configuration details
    # oktapam = {
    #   source  = "okta/oktapam"
    #   version = ">= 0.6.0"  # Latest with security_policy_v2 support
    # }
  }

  # S3 Backend for State Storage
  # State is stored in S3 with DynamoDB locking
  # See aws-backend/README.md for setup instructions
  backend "s3" {
    bucket         = "okta-terraform-demo"
    key            = "Okta-GitOps/myorg/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }
}

provider "okta" {
  org_name  = var.okta_org_name
  base_url  = var.okta_base_url
  api_token = var.okta_api_token
}

# ==============================================================================
# OKTA PRIVILEGED ACCESS (OPA) PROVIDER - OPTIONAL
# ==============================================================================
# Uncomment to enable OPA resource management for:
# - Server access projects
# - Secret folders and secrets
# - Security policies
# - Gateway setup tokens
# - Resource groups
#
# Prerequisites:
# 1. Okta Privileged Access license
# 2. OPA Team configured in Okta
# 3. Service user with administrator role
#
# Environment variables or GitHub Secrets required:
# - OKTAPAM_KEY (service user key/ID)
# - OKTAPAM_SECRET (service user secret)
# - OKTAPAM_TEAM (OPA team name)
#
# See docs/OPA_SETUP.md for setup instructions
# ==============================================================================

# provider "oktapam" {
#   oktapam_key    = var.oktapam_key    # Service user key
#   oktapam_secret = var.oktapam_secret # Service user secret
#   oktapam_team   = var.oktapam_team   # OPA team name
# }
