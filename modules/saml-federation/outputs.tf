# =============================================================================
# SAML Federation Module - Outputs
# =============================================================================
# These outputs enable cross-org coordination via terraform_remote_state
# Partner organizations can reference these values to configure their side
# =============================================================================

# -----------------------------------------------------------------------------
# Organization Identity (Both Modes)
# -----------------------------------------------------------------------------
# Basic org info that partner orgs need for URL construction
# -----------------------------------------------------------------------------

output "okta_org_name" {
  description = "This organization's Okta subdomain"
  value       = var.okta_org_name
}

output "okta_base_url" {
  description = "This organization's Okta base URL domain"
  value       = var.okta_base_url
}

output "federation_mode" {
  description = "Federation mode this module was configured with"
  value       = var.federation_mode
}

output "federation_name" {
  description = "Name used for federation resources"
  value       = var.federation_name
}

# -----------------------------------------------------------------------------
# SP Mode Outputs
# -----------------------------------------------------------------------------
# When federation_mode = "sp", these outputs provide information the
# IdP organization needs to configure their SAML app
# -----------------------------------------------------------------------------

output "idp_id" {
  description = "IdP resource ID (SP mode) - used by IdP to construct ACS URL"
  value       = local.create_idp_saml ? okta_idp_saml.federation[0].id : null
}

output "idp_acs_url" {
  description = "Assertion Consumer Service URL (SP mode) - where IdP sends assertions"
  value       = local.create_idp_saml ? "${local.this_org_acs_base}/${okta_idp_saml.federation[0].id}" : null
}

output "idp_audience" {
  description = "Audience restriction / Entity ID (SP mode)"
  value       = local.create_sp_resources ? local.this_org_audience : null
}

output "idp_metadata_url" {
  description = "IdP metadata URL (SP mode)"
  value       = local.create_idp_saml ? "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/idps/${okta_idp_saml.federation[0].id}/metadata.xml" : null
}

output "idp_status" {
  description = "IdP status (SP mode)"
  value       = local.create_idp_saml ? okta_idp_saml.federation[0].status : null
}

# -----------------------------------------------------------------------------
# IdP Mode Outputs
# -----------------------------------------------------------------------------
# When federation_mode = "idp", these outputs provide information the
# SP organization needs to configure their external IdP
# -----------------------------------------------------------------------------

output "app_id" {
  description = "SAML app ID (IdP mode)"
  value       = local.create_app_saml ? okta_app_saml.federation[0].id : null
}

output "federation_issuer" {
  description = "SAML issuer / Entity ID (IdP mode) - SP needs this for IdP config"
  value       = local.create_app_saml ? "http://www.okta.com/${okta_app_saml.federation[0].id}" : null
}

output "federation_sso_url" {
  description = "SSO URL (IdP mode) - where SP sends AuthnRequests"
  value       = local.create_app_saml ? "https://${var.okta_org_name}.${var.okta_base_url}/app/${okta_app_saml.federation[0].name}/${okta_app_saml.federation[0].id}/sso/saml" : null
}

output "federation_metadata_url" {
  description = "SAML metadata URL (IdP mode)"
  value       = local.create_app_saml ? "https://${var.okta_org_name}.${var.okta_base_url}/app/${okta_app_saml.federation[0].id}/sso/saml/metadata" : null
}

output "federation_certificate" {
  description = "X.509 signing certificate (IdP mode) - SP needs this to validate assertions"
  value       = local.create_app_saml ? okta_app_saml.federation[0].certificate : null
  sensitive   = true
}

output "app_status" {
  description = "App status (IdP mode)"
  value       = local.create_app_saml ? okta_app_saml.federation[0].status : null
}

# -----------------------------------------------------------------------------
# Composite Outputs
# -----------------------------------------------------------------------------
# Structured outputs for easier consumption
# -----------------------------------------------------------------------------

output "federation_config" {
  description = "Complete federation configuration object"
  value = {
    mode     = var.federation_mode
    name     = var.federation_name
    org_name = var.okta_org_name
    base_url = var.okta_base_url

    # SP mode values (null if IdP mode)
    sp = var.federation_mode == "sp" ? {
      idp_id       = local.create_idp_saml ? okta_idp_saml.federation[0].id : null
      acs_url      = local.create_idp_saml ? "${local.this_org_acs_base}/${okta_idp_saml.federation[0].id}" : null
      audience     = local.this_org_audience
      metadata_url = local.create_idp_saml ? "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/idps/${okta_idp_saml.federation[0].id}/metadata.xml" : null
    } : null

    # IdP mode values (null if SP mode)
    idp = var.federation_mode == "idp" ? {
      app_id       = local.create_app_saml ? okta_app_saml.federation[0].id : null
      issuer       = local.create_app_saml ? "http://www.okta.com/${okta_app_saml.federation[0].id}" : null
      sso_url      = local.create_app_saml ? "https://${var.okta_org_name}.${var.okta_base_url}/app/${okta_app_saml.federation[0].name}/${okta_app_saml.federation[0].id}/sso/saml" : null
      metadata_url = local.create_app_saml ? "https://${var.okta_org_name}.${var.okta_base_url}/app/${okta_app_saml.federation[0].id}/sso/saml/metadata" : null
    } : null
  }
}

# -----------------------------------------------------------------------------
# Routing Rule Outputs (SP Mode)
# -----------------------------------------------------------------------------

output "routing_rule_id" {
  description = "IdP discovery routing rule ID (SP mode)"
  value       = local.create_routing_rule && var.routing_policy_id != "" ? okta_policy_rule_idp_discovery.federation[0].id : null
}

# -----------------------------------------------------------------------------
# Status Summary
# -----------------------------------------------------------------------------

output "status" {
  description = "Summary of created resources"
  value = {
    mode               = var.federation_mode
    resources_created  = var.federation_mode == "sp" ? local.create_idp_saml : local.create_app_saml
    idp_configured     = local.create_idp_saml
    app_configured     = local.create_app_saml
    routing_configured = local.create_routing_rule && var.routing_policy_id != ""
    remote_state_used  = var.use_remote_state
  }
}
