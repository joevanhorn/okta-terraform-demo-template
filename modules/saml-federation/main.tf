# =============================================================================
# SAML Federation Module - Main Resources
# =============================================================================
# This module creates SAML federation resources based on the federation_mode:
#
# SP Mode (federation_mode = "sp"):
#   - okta_idp_saml_key: X.509 certificate for the external IdP
#   - okta_idp_saml: External SAML IdP configuration
#   - okta_policy_rule_idp_discovery: Optional routing rule
#
# IdP Mode (federation_mode = "idp"):
#   - okta_app_saml: SAML application for federation
#   - okta_app_group_assignments: Group assignments for the app
# =============================================================================

# =============================================================================
# SP MODE RESOURCES
# =============================================================================
# Created when federation_mode = "sp"
# Configures this Okta org to receive SAML assertions from an external IdP
# =============================================================================

# -----------------------------------------------------------------------------
# SAML IdP Signing Key
# -----------------------------------------------------------------------------
# Stores the X.509 certificate from the external IdP
# Required for validating SAML assertions
# -----------------------------------------------------------------------------

resource "okta_idp_saml_key" "federation" {
  count = local.create_idp_saml && local.idp_certificate != "" ? 1 : 0

  x5c = [local.idp_certificate]
}

# -----------------------------------------------------------------------------
# External SAML IdP Configuration
# -----------------------------------------------------------------------------
# Creates an external IdP that can authenticate users via SAML
# Supports JIT provisioning and account linking
# -----------------------------------------------------------------------------

resource "okta_idp_saml" "federation" {
  count = local.create_idp_saml ? 1 : 0

  name                     = local.idp_name
  acs_type                 = "INSTANCE"
  sso_url                  = local.idp_sso_url
  sso_destination          = local.idp_sso_url
  sso_binding              = "HTTP-POST"
  issuer                   = local.idp_issuer
  issuer_mode              = "ORG_URL"
  kid                      = local.idp_certificate != "" ? okta_idp_saml_key.federation[0].id : null
  status                   = var.status
  request_signature_scope  = var.request_signature_scope
  request_signature_algorithm = var.request_signature_algorithm

  # User provisioning settings
  provisioning_action = var.provisioning_action
  deprovisioned_action = "NONE"
  suspended_action     = "NONE"
  profile_master       = var.profile_master

  # Account linking
  account_link_action      = var.account_link_action
  account_link_group_include = []

  # Subject matching
  subject_match_type      = var.subject_match_type
  subject_match_attribute = var.subject_match_attribute != "" ? var.subject_match_attribute : null

  # Username template
  username_template = var.username_template

  # Group settings
  groups_action     = var.groups_action
  groups_attribute  = var.groups_attribute != "" ? var.groups_attribute : null
  groups_assignment = var.groups_assignment

  # Max clock skew for SAML assertion validation (5 minutes)
  max_clock_skew = 300000

  lifecycle {
    # Prevent accidental destruction
    prevent_destroy = false
  }
}

# -----------------------------------------------------------------------------
# IdP Discovery Routing Rule (Optional)
# -----------------------------------------------------------------------------
# Routes users to this IdP based on email domain
# Requires an existing IdP discovery policy
# -----------------------------------------------------------------------------

resource "okta_policy_rule_idp_discovery" "federation" {
  count = local.create_routing_rule && var.routing_policy_id != "" ? 1 : 0

  name                  = "${var.federation_name} Routing"
  policy_id             = var.routing_policy_id
  priority              = var.routing_rule_priority
  status                = var.status
  idp_type              = "SAML2"
  idp_id                = okta_idp_saml.federation[0].id
  user_identifier_type  = "IDENTIFIER"
  user_identifier_attribute = "login"

  user_identifier_patterns {
    match_type = "SUFFIX"
    value      = var.routing_domain_suffix
  }
}

# =============================================================================
# IDP MODE RESOURCES
# =============================================================================
# Created when federation_mode = "idp"
# Configures this Okta org to send SAML assertions to an external SP
# =============================================================================

# -----------------------------------------------------------------------------
# SAML Federation Application
# -----------------------------------------------------------------------------
# Creates a SAML app that sends assertions to the partner SP
# For Okta-to-Okta: Uses partner's ACS URL and audience
# For External SP: Uses provided sp_acs_url and sp_audience
# -----------------------------------------------------------------------------

resource "okta_app_saml" "federation" {
  count = local.create_app_saml ? 1 : 0

  label             = local.app_label
  status            = var.status
  preconfigured_app = null

  # SAML Endpoints
  sso_url     = local.sp_acs_url
  recipient   = local.sp_acs_url
  destination = local.sp_acs_url
  audience    = local.sp_audience_url

  # Subject/NameID
  subject_name_id_template = "$${user.userName}"
  subject_name_id_format   = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"

  # Signature settings
  response_signed          = true
  assertion_signed         = var.assertion_signed
  signature_algorithm      = var.response_signature_algorithm
  digest_algorithm         = var.digest_algorithm
  honor_force_authn        = var.honor_force_authn

  # Attribute statements
  dynamic "attribute_statements" {
    for_each = local.attribute_statements
    content {
      name         = attribute_statements.value.name
      namespace    = attribute_statements.value.namespace
      type         = attribute_statements.value.type
      values       = attribute_statements.value.values
      filter_type  = attribute_statements.value.filter_type
      filter_value = attribute_statements.value.filter_value
    }
  }

  # App visibility (hide from user dashboard - this is a backend federation app)
  hide_ios = true
  hide_web = true

  # Feature settings
  auto_submit_toolbar        = false
  user_name_template         = "$${source.login}"
  user_name_template_suffix  = ""
  user_name_template_type    = "BUILT_IN"
  app_settings_json          = null
  implicit_assignment        = false
  accessibility_self_service = false

  lifecycle {
    # Ignore changes to client-side settings
    ignore_changes = [
      logo,
      logo_url,
    ]
  }
}

# -----------------------------------------------------------------------------
# Group Assignments for Federation App
# -----------------------------------------------------------------------------
# Assigns groups to the SAML app, controlling who can federate
# -----------------------------------------------------------------------------

resource "okta_app_group_assignments" "federation" {
  count = local.create_app_saml && length(var.assigned_group_ids) > 0 ? 1 : 0

  app_id = okta_app_saml.federation[0].id

  dynamic "group" {
    for_each = var.assigned_group_ids
    content {
      id = group.value
    }
  }
}
