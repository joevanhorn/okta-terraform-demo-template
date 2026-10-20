# =============================================================================
# OKTA TERRAFORM PROVIDER - RESOURCE REFERENCE
# =============================================================================
# Commented, copy-paste examples for the okta/okta Terraform provider.
#
# Verified against okta/okta v7.0.0 (constraint >= 7.0.0, < 8.0.0): every
# resource/data-source name and attribute below comes from
# `terraform providers schema -json`, and the whole file passes
# `terraform validate` when uncommented. v7.0.0 ships 162 resources and
# 109 data sources; the examples cover the ones that matter for demos.
#
# Documentation: https://registry.terraform.io/providers/okta/okta/latest/docs
#
# NOTE: All examples are COMMENTED OUT. Uncomment and customize as needed.
# Examples reference each other (okta_user.example, okta_group.example,
# okta_app_oauth.example, data.okta_org_metadata.current ...), so uncomment
# the dependencies too.
#
# v7.0.0 BREAKING CHANGES (if you are upgrading from 6.x):
#   okta_trusted_origin            scopes list  -> repeated scopes {} blocks;
#                                  active bool  -> status = "ACTIVE"/"INACTIVE"
#   okta_threat_insight_settings   network_excludes -> exclude_zones
#   okta_template_sms              translations set-of-objects -> map(string)
#   okta_role_subscription         role_type -> role_ref; status removed
#   okta_captcha                   name/type/site_key/secret_key now optional
#   okta_captcha_org_wide_settings DEPRECATED -> okta_org_captcha
#                                  (enabled_for -> enabled_pages)
#   okta_email_template_settings   recipients now optional
# =============================================================================

# Org metadata is handy for building ORNs (resource owners, labels, resource sets)
# data "okta_org_metadata" "current" {}

# =============================================================================
# IDENTITY & ACCESS MANAGEMENT
# =============================================================================

# -----------------------------------------------------------------------------
# Users
# -----------------------------------------------------------------------------

# resource "okta_user" "example" {
#   first_name = "John"
#   last_name  = "Doe"
#   login      = "john.doe@example.com"
#   email      = "john.doe@example.com"
#   status     = "ACTIVE"
# }

# resource "okta_user_schema_property" "example" {
#   index       = "customAttribute"
#   title       = "Custom Attribute"
#   type        = "string"
#   description = "A custom user attribute"
#   master      = "PROFILE_MASTER"
#   scope       = "NONE"
# }

# resource "okta_user_base_schema_property" "example" {
#   index    = "email"
#   title    = "Primary email"
#   type     = "string"
#   required = true
#   master   = "PROFILE_MASTER"
# }

# resource "okta_user_type" "example" {
#   name         = "contractor"
#   display_name = "Contractor"
#   description  = "Contractor user type"
# }

# Built-in admin roles on a user
# resource "okta_user_admin_roles" "example" {
#   user_id     = okta_user.example.id
#   admin_roles = ["USER_ADMIN", "APP_ADMIN"]
# }

# Set a user's ITP risk level (demo trigger for Identity Threat Protection)
# resource "okta_user_risk" "example" {
#   user_id    = okta_user.example.id
#   risk_level = "HIGH" # HIGH or LOW
# }

# Admin notification subscription for a single user
# resource "okta_user_subscription" "example" {
#   user_id           = okta_user.example.id
#   notification_type = "OKTA_ANNOUNCEMENT"
# }

# -----------------------------------------------------------------------------
# Bulk User Management from CSV (1000+ users)
# -----------------------------------------------------------------------------
# For managing large numbers of users, use CSV-based import with for_each.
# See users_from_csv.tf.example for complete implementation.
#
# Quick example:
#
# locals {
#   csv_users = csvdecode(file("${path.module}/users.csv"))
#   users_map = { for user in local.csv_users : user.email => user }
# }
#
# resource "okta_user" "csv_users" {
#   for_each                  = local.users_map
#   email                     = each.value.email
#   first_name                = each.value.first_name
#   last_name                 = each.value.last_name
#   login                     = each.value.login
#   status                    = coalesce(each.value.status, "ACTIVE")
#   department                = try(each.value.department, null)
#   title                     = try(each.value.title, null)
#   custom_profile_attributes = try(each.value.custom_profile_attributes, null)
# }
#
# CSV Format (users.csv):
#   email,first_name,last_name,login,status,department,title,manager_email,groups,custom_profile_attributes
#   john@example.com,John,Doe,john@example.com,ACTIVE,Engineering,Developer,manager@example.com,"Engineering,Developers","{""employeeId"":""E001""}"
#
# Features:
#   - Manager relationships via manager_email column (resolved with okta_link_value)
#   - Group memberships via comma-separated groups column
#   - Custom attributes via JSON string column
#   - See users.csv.example for sample data
#
# Performance: For 1000+ users, use: terraform apply -parallelism=10

# -----------------------------------------------------------------------------
# Groups
# -----------------------------------------------------------------------------

# resource "okta_group" "example" {
#   name        = "Engineering"
#   description = "Engineering department group"
# }

# resource "okta_group_schema_property" "example" {
#   index       = "department"
#   title       = "Department"
#   type        = "string"
#   description = "Department for the group"
#   master      = "PROFILE_MASTER"
# }

# resource "okta_group_rule" "example" {
#   name              = "Auto-assign contractors"
#   status            = "ACTIVE"
#   group_assignments = [okta_group.example.id]
#   expression_type   = "urn:okta:expression:1.0"
#   expression_value  = "user.userType==\"contractor\""
# }

# Group-centric membership (attribute is `users`, not `members`)
# resource "okta_group_memberships" "example" {
#   group_id = okta_group.example.id
#   users    = [okta_user.example.id]
# }

# User-centric membership
# resource "okta_user_group_memberships" "example" {
#   user_id = okta_user.example.id
#   groups  = [okta_group.example.id]
# }

# Group owners (authoritative: owners not listed here are removed)
# resource "okta_group_owners" "example" {
#   group_id = okta_group.example.id
#   owner {
#     type = "USER"
#     id   = okta_user.example.id
#   }
# }

# Single group owner (non-authoritative alternative)
# resource "okta_group_owner" "example" {
#   group_id          = okta_group.example.id
#   id_of_group_owner = okta_user.example.id
#   type              = "USER"
# }

# Admin role on a group
# resource "okta_group_role" "example" {
#   group_id  = okta_group.example.id
#   role_type = "HELP_DESK_ADMIN"
# }

# -----------------------------------------------------------------------------
# Realms (partner / segmented user populations)
# -----------------------------------------------------------------------------

# resource "okta_realm" "partners" {
#   name       = "Partners"
#   realm_type = "PARTNER" # PARTNER or DEFAULT
# }

# resource "okta_realm_assignment" "partners" {
#   name                 = "Partner users"
#   realm_id             = okta_realm.partners.id
#   profile_source_id    = okta_idp_oidc.example.id # the profile source (IdP/app) users arrive from
#   condition_expression = "user.profile.login.contains(\"@partner.example.com\")"
#   priority             = 1
#   status               = "ACTIVE"
# }

# =============================================================================
# APPLICATIONS
# =============================================================================

# -----------------------------------------------------------------------------
# OAuth / OIDC Applications
# -----------------------------------------------------------------------------

# resource "okta_app_oauth" "example" {
#   label                      = "Example OAuth App"
#   type                       = "web"
#   grant_types                = ["authorization_code", "refresh_token"]
#   redirect_uris              = ["https://example.com/callback"]
#   post_logout_redirect_uris  = ["https://example.com/logout"]
#   response_types             = ["code"]
#   token_endpoint_auth_method = "client_secret_post"
#   consent_method             = "REQUIRED"
#
#   # Visibility settings
#   hide_ios = false
#   hide_web = false
#
#   # IMPORTANT: When apps are visible (hide_ios/hide_web = false),
#   # login_mode MUST be set to something other than DISABLED
#   # See CLAUDE.md Gotcha #5 for details
#   login_mode = "SPEC"
#   login_uri  = "https://example.com"
#
#   # Optional: bind an app sign-on (authentication) policy
#   # authentication_policy = okta_app_signon_policy.example.id
# }

# Redirect URIs can be managed on okta_app_oauth directly; these two resources
# still exist but are DEPRECATED in v7.
# resource "okta_app_oauth_redirect_uri" "example" {
#   app_id = okta_app_oauth.example.id
#   uri    = "https://example.com/another-callback"
# }

# resource "okta_app_oauth_post_logout_redirect_uri" "example" {
#   app_id = okta_app_oauth.example.id
#   uri    = "https://example.com/logout"
# }

# Grant Okta management API scopes to a service app
# resource "okta_app_oauth_api_scope" "example" {
#   app_id = okta_app_oauth.example.id
#   issuer = "https://${var.okta_org_name}.${var.okta_base_url}"
#   scopes = ["okta.users.read", "okta.groups.read"]
# }

# Assign an admin role to an OAuth service app (client credentials)
# resource "okta_app_oauth_role_assignment" "example" {
#   client_id = okta_app_oauth.example.client_id
#   type      = "READ_ONLY_ADMIN"
# }

# Same idea via the newer /oauth2/v1/clients role resources (one per role type:
# okta_oauth2_v1_clients_role_app_admin, _super_admin, _custom, ...)
# resource "okta_oauth2_v1_clients_role_app_admin" "example" {
#   client_id = okta_app_oauth.example.client_id
#   type      = "APP_ADMIN"
# }

# Custom claim added to tokens issued for this app
# resource "okta_app_federated_claim" "example" {
#   app_id     = okta_app_oauth.example.id
#   name       = "department"
#   expression = "user.department"
# }

# -----------------------------------------------------------------------------
# SAML Applications
# -----------------------------------------------------------------------------

# resource "okta_app_saml" "example" {
#   label                    = "Example SAML App"
#   sso_url                  = "https://example.com/sso/saml"
#   recipient                = "https://example.com/sso/saml"
#   destination              = "https://example.com/sso/saml"
#   audience                 = "https://example.com"
#   subject_name_id_template = "$${user.userName}"
#   subject_name_id_format   = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
#   response_signed          = true
#   signature_algorithm      = "RSA_SHA256"
#   digest_algorithm         = "SHA256"
#   honor_force_authn        = true
#   authn_context_class_ref  = "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport"
#
#   attribute_statements {
#     name   = "email"
#     values = ["user.email"]
#   }
# }

# resource "okta_app_saml_app_settings" "example" {
#   app_id = okta_app_saml.example.id
#   settings = jsonencode({
#     "app_setting_1" = "value1"
#   })
# }

# -----------------------------------------------------------------------------
# Other Application Types
# -----------------------------------------------------------------------------

# resource "okta_app_basic_auth" "example" {
#   label    = "Basic Auth App"
#   url      = "https://example.com/login"
#   auth_url = "https://example.com/auth"
# }

# resource "okta_app_bookmark" "example" {
#   label = "Bookmark App"
#   url   = "https://example.com"
# }

# resource "okta_app_swa" "example" {
#   label          = "SWA App"
#   button_field   = "btn-login"
#   password_field = "txtbox-password"
#   username_field = "txtbox-username"
#   url            = "https://example.com/login.html"
# }

# resource "okta_app_secure_password_store" "example" {
#   label                 = "Secure Password Store App"
#   username_field        = "user"
#   password_field        = "pass"
#   url                   = "https://example.com/login"
#   optional_field1       = "optional1"
#   optional_field1_value = "value1"
#   credentials_scheme    = "ADMIN_SETS_CREDENTIALS"
# }

# resource "okta_app_three_field" "example" {
#   label                = "Three Field App"
#   button_selector      = "#login-button"
#   username_selector    = "#username"
#   password_selector    = "#password"
#   extra_field_selector = "#company"
#   extra_field_value    = "company-name"
#   url                  = "https://example.com/login"
#   credentials_scheme   = "ADMIN_SETS_CREDENTIALS"
# }

# resource "okta_app_auto_login" "example" {
#   label                = "Auto Login App"
#   sign_on_url          = "https://example.com/login"
#   sign_on_redirect_url = "https://example.com/app"
#   credentials_scheme   = "ADMIN_SETS_CREDENTIALS"
# }

# resource "okta_app_shared_credentials" "example" {
#   label           = "Shared Credentials App"
#   url             = "https://example.com/login"
#   button_field    = "btn-login"
#   username_field  = "txtbox-username"
#   password_field  = "txtbox-password"
#   shared_username = "shared.user@example.com"
#   shared_password = var.shared_app_password
# }

# -----------------------------------------------------------------------------
# Application Assignments & Schema
# -----------------------------------------------------------------------------

# resource "okta_app_user" "example" {
#   app_id   = okta_app_oauth.example.id
#   user_id  = okta_user.example.id
#   username = "john.doe@example.com"
# }

# resource "okta_app_group_assignment" "example" {
#   app_id   = okta_app_oauth.example.id
#   group_id = okta_group.example.id
# }

# resource "okta_app_group_assignments" "example" {
#   app_id = okta_app_oauth.example.id
#   group {
#     id       = okta_group.example.id
#     priority = 1
#   }
# }

# resource "okta_app_user_schema_property" "example" {
#   app_id      = okta_app_oauth.example.id
#   index       = "customField"
#   title       = "Custom Field"
#   type        = "string"
#   description = "Custom field for app user profile"
#   master      = "OKTA"
# }

# resource "okta_app_user_base_schema_property" "example" {
#   app_id = okta_app_oauth.example.id
#   index  = "email"
#   title  = "Email"
#   type   = "string"
#   master = "OKTA"
# }

# -----------------------------------------------------------------------------
# Provisioning (SCIM) connection & features  (new in v6.x)
# -----------------------------------------------------------------------------
# okta_app_connection configures the app's provisioning connection (base URL +
# auth) and activates it. okta_app_features then turns on the provisioning
# capabilities. NOTE: okta_app_features only works for the subset of OIN apps
# that expose the Application Features API, and it cannot be destroyed (Okta
# owns the feature; destroy just removes it from state).

# resource "okta_app_connection" "example" {
#   id       = okta_app_oauth.example.id # the app ID (also the resource ID)
#   base_url = "https://scim.example.com/scim/v2"
#   action   = "activate" # activate or deactivate
#
#   profile {
#     auth_scheme = "TOKEN" # TOKEN or OAUTH2
#     token       = var.scim_bearer_token
#   }
# }

# resource "okta_app_features" "example" {
#   app_id = okta_app_oauth.example.id
#   name   = "USER_PROVISIONING" # or INBOUND_PROVISIONING
#   status = "ENABLED"
#
#   capabilities {
#     create {
#       lifecycle_create {
#         status = "ENABLED"
#       }
#     }
#     update {
#       lifecycle_deactivate {
#         status = "ENABLED"
#       }
#       profile {
#         status = "ENABLED"
#       }
#       password {
#         change = "CHANGE"
#         seed   = "RANDOM"
#         status = "ENABLED"
#       }
#     }
#   }
#
#   depends_on = [okta_app_connection.example]
# }

# Group push mapping (push an Okta group to the downstream app)
# resource "okta_push_group" "example" {
#   app_id            = okta_app_oauth.example.id
#   source_group_id   = okta_group.example.id
#   target_group_name = "Engineering"
#   status            = "ACTIVE"
# }

# -----------------------------------------------------------------------------
# App Sign-On (Authentication) Policies  -- OIE only
# -----------------------------------------------------------------------------

# resource "okta_app_signon_policy" "example" {
#   name        = "Example App Sign-On Policy"
#   description = "Authentication policy for the example app"
# }

# resource "okta_app_signon_policy_rule" "example" {
#   policy_id                   = okta_app_signon_policy.example.id
#   name                        = "Require 2FA"
#   access                      = "ALLOW"
#   factor_mode                 = "2FA"
#   type                        = "ASSURANCE"
#   re_authentication_frequency = "PT43800H"
#   groups_included             = [okta_group.example.id]
#   constraints = [
#     jsonencode({
#       knowledge  = { types = ["password"] }
#       possession = { deviceBound = "REQUIRED" }
#     })
#   ]
#   # Office 365 apps only (added in v6.14.0):
#   # office365_client_include = ["WEB", "MODERN_AUTH"]
# }

# Manage ALL rules of a policy in one resource (consistent priority ordering)
# resource "okta_app_signon_policy_rules" "example" {
#   policy_id = okta_app_signon_policy.example.id
#   rule {
#     name                 = "Managed devices"
#     priority             = 1
#     access               = "ALLOW"
#     factor_mode          = "1FA"
#     type                 = "ASSURANCE"
#     device_is_managed    = true
#     device_is_registered = true
#   }
# }

# =============================================================================
# AUTHORIZATION SERVERS
# =============================================================================

# resource "okta_auth_server" "example" {
#   name        = "Example Auth Server"
#   description = "Custom authorization server"
#   audiences   = ["api://example"]
#   issuer_mode = "CUSTOM_URL"
#   status      = "ACTIVE"
# }

# resource "okta_auth_server_default" "example" {
#   name        = "default"
#   description = "Default authorization server"
#   audiences   = ["api://default"]
#   status      = "ACTIVE"
# }

# resource "okta_auth_server_policy" "example" {
#   name             = "Example Policy"
#   description      = "Authorization server policy"
#   auth_server_id   = okta_auth_server.example.id
#   priority         = 1
#   client_whitelist = ["ALL_CLIENTS"]
# }

# resource "okta_auth_server_policy_rule" "example" {
#   name                 = "Example Rule"
#   auth_server_id       = okta_auth_server.example.id
#   policy_id            = okta_auth_server_policy.example.id
#   priority             = 1
#   grant_type_whitelist = ["authorization_code", "refresh_token"]
#   scope_whitelist      = ["openid", "profile", "email"]
# }

# resource "okta_auth_server_claim" "example" {
#   name                    = "custom_claim"
#   auth_server_id          = okta_auth_server.example.id
#   claim_type              = "RESOURCE"
#   value_type              = "EXPRESSION"
#   value                   = "user.customAttribute"
#   scopes                  = ["profile"]
#   status                  = "ACTIVE"
#   always_include_in_token = false
# }

# resource "okta_auth_server_claim_default" "example" {
#   name           = "sub"
#   auth_server_id = okta_auth_server_default.example.id
#   value          = "user.id"
# }

# resource "okta_auth_server_scope" "example" {
#   name             = "custom_scope"
#   auth_server_id   = okta_auth_server.example.id
#   description      = "Custom OAuth scope"
#   consent          = "REQUIRED"
#   metadata_publish = "ALL_CLIENTS"
# }

# Trust tokens from another authorization server
# resource "okta_trusted_server" "example" {
#   auth_server_id = okta_auth_server.example.id
#   trusted        = [okta_auth_server_default.example.id]
# }

# =============================================================================
# POLICIES
# =============================================================================

# -----------------------------------------------------------------------------
# MFA Policies
# -----------------------------------------------------------------------------

# resource "okta_policy_mfa" "example" {
#   name            = "Example MFA Policy"
#   status          = "ACTIVE"
#   description     = "Multi-factor authentication policy"
#   priority        = 1
#   is_oie          = true
#   groups_included = [okta_group.example.id]
#
#   okta_verify = {
#     enroll = "REQUIRED"
#   }
# }

# resource "okta_policy_mfa_default" "example" {
#   is_oie = true
#   okta_verify = {
#     enroll = "OPTIONAL"
#   }
# }

# resource "okta_policy_rule_mfa" "example" {
#   name      = "Example MFA Rule"
#   policy_id = okta_policy_mfa.example.id
#   status    = "ACTIVE"
#   priority  = 1
#   enroll    = "LOGIN"
# }

# -----------------------------------------------------------------------------
# Password Policies
# -----------------------------------------------------------------------------

# resource "okta_policy_password" "example" {
#   name            = "Example Password Policy"
#   status          = "ACTIVE"
#   description     = "Password policy"
#   priority        = 1
#   groups_included = [okta_group.example.id]
#
#   password_min_length                    = 12
#   password_min_lowercase                 = 1
#   password_min_uppercase                 = 1
#   password_min_number                    = 1
#   password_min_symbol                    = 1
#   password_exclude_username              = true
#   password_exclude_first_name            = true
#   password_exclude_last_name             = true
#   password_max_age_days                  = 90
#   password_expire_warn_days              = 15
#   password_min_age_minutes               = 0
#   password_history_count                 = 5
#   password_max_lockout_attempts          = 5
#   password_auto_unlock_minutes           = 15
#   password_show_lockout_failures         = true
#   password_lockout_notification_channels = ["EMAIL"]
# }

# resource "okta_policy_password_default" "example" {
#   password_min_length = 8
# }

# resource "okta_policy_rule_password" "example" {
#   name            = "Example Password Rule"
#   policy_id       = okta_policy_password.example.id
#   status          = "ACTIVE"
#   priority        = 1
#   password_change = "ALLOW"
#   password_reset  = "ALLOW"
#   password_unlock = "ALLOW"
# }

# -----------------------------------------------------------------------------
# Global Session (Sign-On) Policies
# -----------------------------------------------------------------------------

# resource "okta_policy_signon" "example" {
#   name            = "Example Sign-On Policy"
#   status          = "ACTIVE"
#   description     = "Sign-on policy"
#   priority        = 1
#   groups_included = [okta_group.example.id]
# }

# resource "okta_policy_rule_signon" "example" {
#   name                = "Example Sign-On Rule"
#   policy_id           = okta_policy_signon.example.id
#   status              = "ACTIVE"
#   priority            = 1
#   access              = "ALLOW"
#   authtype            = "ANY"
#   mfa_required        = true
#   mfa_prompt          = "ALWAYS"
#   mfa_remember_device = false
#   mfa_lifetime        = 60
#   session_idle        = 120
#   session_lifetime    = 240
#   session_persistent  = false
# }

# -----------------------------------------------------------------------------
# Profile Enrollment (self-service registration)
# -----------------------------------------------------------------------------

# resource "okta_policy_profile_enrollment" "example" {
#   name   = "Example Enrollment Policy"
#   status = "ACTIVE"
# }

# resource "okta_policy_rule_profile_enrollment" "example" {
#   policy_id           = okta_policy_profile_enrollment.example.id
#   unknown_user_action = "REGISTER"
#   email_verification  = true
#   access              = "ALLOW"
#   target_group_id     = okta_group.example.id
#
#   profile_attributes {
#     name     = "email"
#     label    = "Email"
#     required = true
#   }
# }

# resource "okta_policy_profile_enrollment_apps" "example" {
#   policy_id = okta_policy_profile_enrollment.example.id
#   apps      = [okta_app_oauth.example.id]
# }

# -----------------------------------------------------------------------------
# IdP Discovery (routing) rules
# -----------------------------------------------------------------------------

# data "okta_policy" "idp_discovery" {
#   name = "Idp Discovery Policy"
#   type = "IDP_DISCOVERY"
# }

# resource "okta_policy_rule_idp_discovery" "example" {
#   policy_id                 = data.okta_policy.idp_discovery.id
#   name                      = "Route partner.example.com to SAML IdP"
#   priority                  = 1
#   user_identifier_type      = "IDENTIFIER"
#   user_identifier_attribute = "login"
#
#   idp_providers {
#     type = "SAML2"
#     id   = okta_idp_saml.example.id
#   }
#
#   user_identifier_patterns {
#     match_type = "SUFFIX"
#     value      = "partner.example.com"
#   }
# }

# -----------------------------------------------------------------------------
# Device Assurance Policies
# -----------------------------------------------------------------------------

# resource "okta_policy_device_assurance_windows" "example" {
#   name                    = "Windows Device Policy"
#   os_version              = "10.0.0"
#   disk_encryption_type    = ["BITLOCKER"]
#   secure_hardware_present = true
#   screenlock_type         = ["BIOMETRIC"]
# }

# resource "okta_policy_device_assurance_macos" "example" {
#   name                    = "macOS Device Policy"
#   os_version              = "13.0.0"
#   disk_encryption_type    = ["FILEVAULT"]
#   secure_hardware_present = true
#   screenlock_type         = ["BIOMETRIC", "PASSCODE"]
# }

# resource "okta_policy_device_assurance_android" "example" {
#   name                    = "Android Device Policy"
#   os_version              = "12.0"
#   disk_encryption_type    = ["FULL"]
#   jailbreak               = false
#   secure_hardware_present = true
#   screenlock_type         = ["BIOMETRIC", "PASSCODE"]
# }

# resource "okta_policy_device_assurance_ios" "example" {
#   name            = "iOS Device Policy"
#   os_version      = "15.0"
#   jailbreak       = false
#   screenlock_type = ["BIOMETRIC", "PASSCODE"]
# }

# ChromeOS assurance is driven entirely by Chrome's third-party signal provider (tpsp_*)
# resource "okta_policy_device_assurance_chromeos" "example" {
#   name                                   = "ChromeOS Device Policy"
#   tpsp_os_version                        = "100.0"
#   tpsp_allow_screen_lock                 = true
#   tpsp_browser_version                   = "100.0.0"
#   tpsp_builtin_dns_client_enabled        = true
#   tpsp_chrome_remote_desktop_app_blocked = true
#   tpsp_site_isolation_enabled            = true
# }

# -----------------------------------------------------------------------------
# Identity Threat Protection (ITP) policies  -- requires ITP
# -----------------------------------------------------------------------------
# These system policies are created when ITP is enabled; use the data sources
# to find them and the *_rule resources to configure the one editable rule.

# data "okta_entity_risk_policy" "default" {}

# resource "okta_entity_risk_policy_rule" "high_risk" {
#   policy_id              = data.okta_entity_risk_policy.default.id
#   name                   = "High Risk - Terminate Sessions"
#   risk_level             = "HIGH" # HIGH, MEDIUM, LOW, ANY
#   terminate_all_sessions = true
#   groups_included        = [okta_group.example.id]
#   # workflow_id          = "<okta-workflow-id>"  # optionally run a Workflow
# }

# data "okta_session_violation_policy" "default" {}

# resource "okta_session_violation_policy_rule" "default" {
#   policy_id                 = data.okta_session_violation_policy.default.id
#   min_risk_level            = "MEDIUM"
#   policy_evaluation_enabled = true
# }

# data "okta_post_auth_session_policy" "default" {}

# resource "okta_post_auth_session_policy_rule" "default" {
#   policy_id         = data.okta_post_auth_session_policy.default.id
#   terminate_session = true
# }

# Shared Signals Framework receiver: ingest risk signals from a transmitter
# resource "okta_security_events_provider" "example" {
#   name       = "Example SSF transmitter"
#   type       = "okta" # application type of the transmitter
#   is_enabled = "ACTIVE"
#   settings {
#     well_known_url = "https://ssf.example.com/.well-known/ssf-configuration"
#     # or: issuer + jwks_url
#   }
# }

# =============================================================================
# SECURITY & NETWORK
# =============================================================================

# resource "okta_network_zone" "example" {
#   name     = "Example Network Zone"
#   type     = "IP"
#   status   = "ACTIVE"
#   gateways = ["1.2.3.4/24", "5.6.7.8/24"]
#   proxies  = ["9.10.11.12/24"]
# }

# v7: scopes is a repeated block (min 1), status replaces the old `active` bool
# resource "okta_trusted_origin" "example" {
#   name   = "Example Trusted Origin"
#   origin = "https://example.com"
#   status = "ACTIVE"
#   scopes {
#     type = "CORS"
#   }
#   scopes {
#     type = "REDIRECT"
#   }
# }

# resource "okta_behavior" "example" {
#   name     = "New City"
#   type     = "VELOCITY" # ANOMALOUS_LOCATION, ANOMALOUS_DEVICE, ANOMALOUS_IP, VELOCITY
#   status   = "ACTIVE"
#   velocity = 40 # km/h
# }

# v7: network_excludes renamed to exclude_zones (network zone IDs)
# resource "okta_threat_insight_settings" "example" {
#   action        = "block" # none, audit, block
#   exclude_zones = [okta_network_zone.example.id]
# }

# resource "okta_security_notification_emails" "example" {
#   report_suspicious_activity_enabled       = true
#   send_email_for_new_device_enabled        = true
#   send_email_for_factor_enrollment_enabled = true
#   send_email_for_factor_reset_enabled      = true
#   send_email_for_password_changed_enabled  = true
# }

# -----------------------------------------------------------------------------
# Rate limiting
# -----------------------------------------------------------------------------

# resource "okta_rate_limiting" "example" {
#   default_mode = "ENFORCE" # ENFORCE, PREVIEW, DISABLE
#   use_case_mode_overrides {
#     login_page       = "PREVIEW"
#     oauth2_authorize = "ENFORCE"
#     oie_app_intent   = "ENFORCE"
#   }
# }

# Per-principal rate limit budget for an API token or OAuth client
# resource "okta_principal_rate_limits" "example" {
#   principal_id                   = okta_app_oauth.example.id
#   principal_type                 = "OAUTH_CLIENT" # or SSWS_TOKEN
#   default_percentage             = 50
#   default_concurrency_percentage = 50
# }

# resource "okta_rate_limit_admin_notification_settings" "example" {
#   notifications_enabled = true
# }

# resource "okta_rate_limit_warning_threshold_percentage" "example" {
#   warning_threshold = 80
# }

# -----------------------------------------------------------------------------
# Authenticators & factors
# -----------------------------------------------------------------------------

# resource "okta_authenticator" "okta_verify" {
#   name   = "Okta Verify"
#   key    = "okta_verify"
#   status = "ACTIVE"
# }

# resource "okta_authenticator" "webauthn" {
#   name   = "FIDO2 (WebAuthn)"
#   key    = "webauthn"
#   status = "ACTIVE"
# }

# WebAuthn method settings (passkeys, user verification, AAGUID groups)
# resource "okta_authenticator_method_webauthn" "example" {
#   authenticator_id                   = okta_authenticator.webauthn.id
#   user_verification                  = "REQUIRED" # DISCOURAGED, PREFERRED, REQUIRED
#   allow_syncable_passkeys            = true
#   show_sign_in_with_a_passkey_button = true
# }

# Classic factor enablement (pre-OIE orgs)
# resource "okta_factor" "google_otp" {
#   provider_id = "google_otp"
#   active      = true
# }

# Push provider for a custom-app authenticator
# resource "okta_push_provider" "apns" {
#   name          = "Example APNs provider"
#   provider_type = "APNS" # APNS or FCM
#   configuration {
#     apns_configuration {
#       key_id            = "ABCDE12345"
#       team_id           = "FGHIJ67890"
#       token_signing_key = var.apns_signing_key
#       file_name         = "AuthKey_ABCDE12345.p8"
#     }
#   }
# }

# -----------------------------------------------------------------------------
# CAPTCHA
# -----------------------------------------------------------------------------

# resource "okta_captcha" "example" {
#   name       = "Example CAPTCHA"
#   type       = "RECAPTCHA_V2" # HCAPTCHA or RECAPTCHA_V2
#   site_key   = "recaptcha-site-key"
#   secret_key = "recaptcha-secret-key"
# }

# v7: okta_captcha_org_wide_settings is deprecated; use okta_org_captcha
# (enabled_for -> enabled_pages)
# resource "okta_org_captcha" "example" {
#   captcha_id    = okta_captcha.example.id
#   enabled_pages = ["SIGN_IN", "SSR", "SSPR"]
# }

# =============================================================================
# IDENTITY PROVIDERS
# =============================================================================

# resource "okta_idp_saml_key" "example" {
#   x5c = [file("saml.crt")]
# }

# resource "okta_idp_saml" "example" {
#   name                         = "Example SAML IdP"
#   acs_type                     = "INSTANCE"
#   sso_url                      = "https://idp.example.com/sso"
#   sso_destination              = "https://idp.example.com/sso"
#   sso_binding                  = "HTTP-POST"
#   username_template            = "idpuser.email"
#   issuer                       = "https://idp.example.com"
#   kid                          = okta_idp_saml_key.example.id # signing key is required
#   request_signature_algorithm  = "SHA-256"
#   request_signature_scope      = "REQUEST"
#   response_signature_algorithm = "SHA-256"
#   response_signature_scope     = "RESPONSE"
# }

# resource "okta_idp_oidc" "example" {
#   name                  = "Example OIDC IdP"
#   authorization_url     = "https://idp.example.com/authorize"
#   authorization_binding = "HTTP-REDIRECT"
#   token_url             = "https://idp.example.com/token"
#   token_binding         = "HTTP-POST"
#   jwks_url              = "https://idp.example.com/keys"
#   jwks_binding          = "HTTP-REDIRECT"
#   scopes                = ["openid", "profile", "email"]
#   protocol_type         = "OIDC"
#   client_id             = "client-id"
#   client_secret         = "client-secret" # or client_secret_wo (write-only, TF 1.11+)
#   issuer_url            = "https://idp.example.com"
#   username_template     = "idpuser.email"
# }

# resource "okta_idp_social" "example" {
#   name              = "Google"
#   type              = "GOOGLE"
#   protocol_type     = "OAUTH2"
#   scopes            = ["profile", "email", "openid"]
#   client_id         = "google-client-id"
#   client_secret     = "google-client-secret"
#   username_template = "idpuser.email"
# }

# =============================================================================
# BRANDS, THEMES, EMAIL & DOMAINS
# =============================================================================

# resource "okta_brand" "example" {
#   name                           = "Example Brand"
#   agree_to_custom_privacy_policy = true
#   custom_privacy_policy_url      = "https://example.com/privacy"
# }

# resource "okta_theme" "example" {
#   brand_id                               = okta_brand.example.id
#   logo                                   = "logo.png"       # local file path
#   favicon                                = "favicon.ico"    # local file path
#   background_image                       = "background.jpg" # local file path
#   primary_color_hex                      = "#1e5aa8"
#   primary_color_contrast_hex             = "#ffffff"
#   secondary_color_hex                    = "#ebebed"
#   secondary_color_contrast_hex           = "#000000"
#   sign_in_page_touch_point_variant       = "OKTA_DEFAULT"
#   end_user_dashboard_touch_point_variant = "OKTA_DEFAULT"
#   error_page_touch_point_variant         = "OKTA_DEFAULT"
#   email_template_touch_point_variant     = "OKTA_DEFAULT"
# }

# Custom sign-in page (Sign-In Widget 3rd gen)
# resource "okta_customized_signin_page" "example" {
#   brand_id       = okta_brand.example.id
#   page_content   = file("signin_page.html")
#   widget_version = "^7"
#   widget_customizations {
#     widget_generation = "G3"
#     sign_in_label     = "Sign in to Example"
#     help_label        = "Need help?"
#     help_url          = "https://example.com/help"
#   }
# }

# Okta template variables are Terraform-interpolation lookalikes: escape with $$
# resource "okta_email_customization" "example" {
#   brand_id      = okta_brand.example.id
#   template_name = "UserActivation"
#   language      = "en"
#   is_default    = true
#   subject       = "Welcome to $${org.name}!"
#   body          = file("email_templates/activation.html")
# }

# resource "okta_email_template_settings" "example" {
#   brand_id      = okta_brand.example.id
#   template_name = "UserActivation"
#   recipients    = "ALL_USERS" # ALL_USERS, ADMINS_ONLY, NO_USERS (optional in v7)
# }

# Custom email domain (DNS records come back in dns_validation_records)
# resource "okta_email_domain" "example" {
#   brand_id     = okta_brand.example.id
#   domain       = "mail.example.com"
#   display_name = "Example Notifications"
#   user_name    = "no-reply"
# }

# resource "okta_email_domain_verification" "example" {
#   email_domain_id = okta_email_domain.example.id
# }

# Route Okta notification email through your own SMTP server
# resource "okta_email_smtp_server" "example" {
#   alias    = "Example SMTP"
#   host     = "smtp.example.com"
#   port     = 587
#   username = "okta-smtp"
#   password = var.smtp_password
#   enabled  = true
# }

# Custom domain (certificate_source_type MANUAL = you upload the cert,
# OKTA_MANAGED = Okta issues one via Let's Encrypt)
# resource "okta_domain" "example" {
#   name                    = "id.example.com"
#   brand_id                = okta_brand.example.id
#   certificate_source_type = "MANUAL"
# }

# resource "okta_domain_verification" "example" {
#   domain_id = okta_domain.example.id
# }

# resource "okta_domain_certificate" "example" {
#   domain_id         = okta_domain.example.id
#   type              = "PEM"
#   certificate       = file("cert.pem")
#   private_key       = file("key.pem")
#   certificate_chain = file("chain.pem")
# }

# v7: translations is a map of language code -> text; $${code} is an Okta macro
# resource "okta_template_sms" "example" {
#   type     = "SMS_VERIFY_CODE"
#   template = "Your verification code is $${code}"
#   translations = {
#     it = "Il tuo codice di verifica è $${code}"
#     fr = "Votre code de vérification est $${code}"
#     es = "Su código de verificación es $${code}"
#   }
# }

# =============================================================================
# HOOKS & EVENT HANDLERS
# =============================================================================

# channel and auth are MAP attributes (channel = { ... }), not nested blocks
# resource "okta_inline_hook" "example" {
#   name    = "Example Inline Hook"
#   version = "1.0.0"
#   type    = "com.okta.oauth2.tokens.transform"
#   status  = "ACTIVE"
#
#   channel = {
#     type    = "HTTP"
#     version = "1.0.0"
#     uri     = "https://example.com/hook"
#     method  = "POST"
#   }
#
#   auth = {
#     type  = "HEADER"
#     key   = "Authorization"
#     value = "Bearer ${var.hook_secret}"
#   }
# }

# resource "okta_event_hook" "example" {
#   name   = "Example Event Hook"
#   status = "ACTIVE"
#   events = [
#     "user.lifecycle.create",
#     "user.lifecycle.activate"
#   ]
#
#   channel = {
#     type    = "HTTP"
#     version = "1.0.0"
#     uri     = "https://example.com/event-hook"
#   }
#
#   auth = {
#     type  = "HEADER"
#     key   = "Authorization"
#     value = "Bearer ${var.hook_secret}"
#   }
# }

# resource "okta_event_hook_verification" "example" {
#   event_hook_id = okta_event_hook.example.id
# }

# Key pair for OAuth-authenticated inline hooks
# resource "okta_hook_key" "example" {
#   name = "Example hook signing key"
# }

# resource "okta_log_stream" "example" {
#   name   = "Example Log Stream"
#   type   = "aws_eventbridge" # aws_eventbridge or splunk_cloud_logstreaming
#   status = "ACTIVE"
#   settings {
#     account_id        = "123456789012"
#     event_source_name = "oktalogstream" # alphanumeric only
#     region            = "us-east-1"
#   }
# }

# =============================================================================
# OKTA IDENTITY GOVERNANCE (OIG)
# =============================================================================
# Requires an Okta Identity Governance license. Names are SINGULAR
# (okta_request_condition, okta_request_sequence, okta_campaign). The catalog
# and principal-entitlement objects are DATA SOURCES (read-only).
#
# Now in Terraform (added v6.13.0): okta_label (label definitions) and
# okta_resource_owner (owner assignments). Still API-only, use scripts/:
# assigning labels to resources, risk rules / SOD policies, and entitlement
# bundle principal assignments (grants).

# -----------------------------------------------------------------------------
# Entitlements (resource)
# https://registry.terraform.io/providers/okta/okta/latest/docs/resources/entitlement
# -----------------------------------------------------------------------------
# Values MUST be in alphabetical order by external_value (undocumented API
# behaviour; see CLAUDE.md gotcha #11).
# resource "okta_entitlement" "roles" {
#   name           = "Roles"
#   external_value = "roles"
#   description    = "Application roles"
#   multi_value    = true
#   data_type      = "array"
#
#   parent {
#     external_id = okta_app_oauth.example.id
#     type        = "APPLICATION"
#   }
#
#   values {
#     name           = "Admin"
#     external_value = "admin"
#   }
#   values {
#     name           = "Viewer"
#     external_value = "viewer"
#   }
# }

# -----------------------------------------------------------------------------
# Entitlement bundle (resource)
# https://registry.terraform.io/providers/okta/okta/latest/docs/resources/entitlement_bundle
# -----------------------------------------------------------------------------
# The target block is REQUIRED. Bundles need Okta-generated value IDs, not
# external_value strings, so look them up with a dynamic block (this also
# creates the dependency on okta_entitlement for same-apply creation).
# resource "okta_entitlement_bundle" "standard" {
#   name        = "Standard Access Bundle"
#   description = "Standard account access"
#   status      = "ACTIVE"
#
#   target {
#     external_id = okta_app_oauth.example.id
#     type        = "APPLICATION"
#   }
#
#   entitlements {
#     id = okta_entitlement.roles.id
#     dynamic "values" {
#       for_each = [for v in okta_entitlement.roles.values : v.id if v.external_value == "admin"]
#       content {
#         id = values.value
#       }
#     }
#   }
# }
# Note: this manages the bundle DEFINITION only. Who holds the bundle (grants)
# is managed in the Admin Console / Governance API; read it back with the
# okta_principal_entitlements data source.

# -----------------------------------------------------------------------------
# Labels & resource owners (resources, added v6.13.0)
# -----------------------------------------------------------------------------
# ORN cheat sheet (orgId = data.okta_org_metadata.current.id; preview orgs use
# the orn:oktapreview: prefix):
#   app      orn:okta:idp:{orgId}:apps:{appName}:{appId}   appName = app.name, e.g. oidc_client
#   group    orn:okta:directory:{orgId}:groups:{groupId}
#   user     orn:okta:directory:{orgId}:users:{userId}
#   bundle   orn:okta:governance:{orgId}:entitlement-bundles:{bundleId}

# Label definition with its allowed values (assigning labels to resources is
# still API-only: scripts/apply_admin_labels.py)
# resource "okta_label" "data_classification" {
#   name = "Data Classification"
#   values {
#     name = "Confidential"
#   }
#   values {
#     name = "Internal"
#   }
#   values {
#     name = "Public"
#   }
# }

# Resource owners: one resource (or many) -> one or more principals
# resource "okta_resource_owner" "crm" {
#   resource_orns = [
#     "orn:okta:idp:${data.okta_org_metadata.current.id}:apps:${okta_app_oauth.example.name}:${okta_app_oauth.example.id}"
#   ]
#   principal_orns = [
#     "orn:okta:directory:${data.okta_org_metadata.current.id}:users:${okta_user.example.id}",
#     "orn:okta:directory:${data.okta_org_metadata.current.id}:groups:${okta_group.example.id}",
#   ]
# }

# -----------------------------------------------------------------------------
# Access requests (resources) -- names are SINGULAR
# -----------------------------------------------------------------------------
# okta_request_condition makes a resource requestable: who may request it,
# which approval sequence runs, and for how long access is granted.
# https://registry.terraform.io/providers/okta/okta/latest/docs/resources/request_condition
# resource "okta_request_condition" "crm_admin" {
#   name                 = "Request CRM Admin"
#   resource_id          = okta_app_oauth.example.id # the governed app/group/bundle
#   approval_sequence_id = okta_request_sequence.manager.id
#   priority             = 1
#   status               = "ACTIVE" # default is INACTIVE
#
#   requester_settings {
#     type = "EVERYONE" # EVERYONE, TEAMS, GROUPS (+ ids { id = ... })
#   }
#
#   access_scope_settings {
#     type = "RESOURCE_DEFAULT" # RESOURCE_DEFAULT, GROUPS, ENTITLEMENT_BUNDLES
#   }
#
#   access_duration_settings {
#     type     = "ADMIN_FIXED_DURATION" # or REQUESTER_SPECIFIED_DURATION
#     duration = "PT8H"
#   }
# }

# okta_request_sequence binds an EXISTING approval sequence (built in the
# Access Requests admin UI) to a resource. id + resource_id are the inputs;
# name/description/compatible_resource_types are read back.
# https://registry.terraform.io/providers/okta/okta/latest/docs/resources/request_sequence
# resource "okta_request_sequence" "manager" {
#   id          = "<approval-sequence-id>"
#   resource_id = okta_app_oauth.example.id
# }

# Per-resource request settings (e.g. allow request-on-behalf-of)
# https://registry.terraform.io/providers/okta/okta/latest/docs/resources/request_setting_resource
# resource "okta_request_setting_resource" "crm" {
#   id = okta_app_oauth.example.id
#   request_on_behalf_of_settings {
#     allowed = true
#   }
# }

# Org-wide access-request settings
# https://registry.terraform.io/providers/okta/okta/latest/docs/resources/request_setting_organization
# resource "okta_request_setting_organization" "org" {
#   id                         = "default"
#   subprocessors_acknowledged = true
# }

# Create an access request programmatically (entry_id comes from the catalog
# data sources below; requester_field_values answers the request form)
# https://registry.terraform.io/providers/okta/okta/latest/docs/resources/request_v2
# resource "okta_request_v2" "example" {
#   requested {
#     type     = "CATALOG_ENTRY"
#     entry_id = "<catalog-entry-id>"
#   }
#   requested_for {
#     type        = "OKTA_USER"
#     external_id = okta_user.example.id
#   }
# }

# -----------------------------------------------------------------------------
# Access certification (resources)
# -----------------------------------------------------------------------------
# okta_campaign: an access certification campaign. All five settings blocks are
# required. Enum values below are the real ones from the schema.
# https://registry.terraform.io/providers/okta/okta/latest/docs/resources/campaign
# resource "okta_campaign" "quarterly" {
#   name          = "Quarterly Access Review"
#   description   = "Review user access every quarter"
#   campaign_type = "RESOURCE" # RESOURCE or USER
#
#   schedule_settings {
#     type             = "RECURRING" # ONE_OFF or RECURRING
#     start_date       = "2027-01-01T08:00:00.000Z"
#     duration_in_days = 30
#     time_zone        = "America/Los_Angeles"
#     recurrence {
#       interval       = "P3M"
#       repeat_on_type = "SAME_DAY_AS_START_DATE"
#     }
#   }
#
#   resource_settings {
#     type                 = "APPLICATION" # APPLICATION, APPLICATION_AND_GROUP, GROUP
#     include_entitlements = true
#     target_resources {
#       resource_id                          = okta_app_oauth.example.id
#       resource_type                        = "APPLICATION"
#       include_all_entitlements_and_bundles = true
#     }
#   }
#
#   principal_scope_settings {
#     type                      = "GROUPS" # USERS or GROUPS
#     group_ids                 = [okta_group.example.id]
#     include_only_active_users = true
#   }
#
#   reviewer_settings {
#     type                   = "RESOURCE_OWNER" # GROUP, MULTI_LEVEL, RESOURCE_OWNER, REVIEWER_EXPRESSION, USER
#     fallback_reviewer_id   = okta_user.example.id
#     self_review_disabled   = true
#     justification_required = true
#   }
#
#   remediation_settings {
#     access_approved = "NO_ACTION"
#     access_revoked  = "DENY"
#     no_response     = "DENY"
#   }
#
#   notification_settings {
#     notify_reviewer_when_review_assigned      = true
#     notify_reviewer_during_midpoint_of_review = true
#     notify_reviewer_when_overdue              = true
#     notify_review_period_end                  = true
#     notify_reviewer_at_campaign_end           = true
#   }
# }

# okta_review reassigns existing review items to a different reviewer.
# https://registry.terraform.io/providers/okta/okta/latest/docs/resources/review
# resource "okta_review" "example" {
#   campaign_id    = okta_campaign.quarterly.id
#   reviewer_id    = okta_user.example.id
#   review_ids     = ["<review-item-id>"]
#   reviewer_level = "FIRST"
#   note           = "Original reviewer is on leave"
# }

# -----------------------------------------------------------------------------
# Catalog, grants & end-user views -- DATA SOURCES (read-only)
# -----------------------------------------------------------------------------
# data "okta_catalog_entry_default" "crm" {
#   entry_id = "<catalog-entry-id>"
# }
#
# data "okta_catalog_entry_user_access_request_fields" "crm" {
#   entry_id = "<catalog-entry-id>"
#   user_id  = okta_user.example.id
# }
#
# # Entitlement grants a principal holds on an app (bundle principal assignments)
# data "okta_principal_entitlements" "example" {
#   parent {
#     external_id = okta_app_oauth.example.id
#     type        = "APPLICATION"
#   }
#   target_principal {
#     external_id = okta_user.example.id
#     type        = "OKTA_USER"
#   }
# }
#
# # Resources under an app that have no owner yet
# data "okta_resource_owners_catalog_resource" "unowned" {
#   parent_resource_orn = "orn:okta:idp:${data.okta_org_metadata.current.id}:apps:${okta_app_oauth.example.name}:${okta_app_oauth.example.id}"
# }
#
# # Others: okta_label, okta_resource_label (labelled resources), okta_campaign,
# # okta_request_condition, okta_request_sequence, okta_request_v2,
# # okta_request_setting_organization, okta_request_setting_resource,
# # okta_entitlement, okta_entitlement_bundle, okta_review, okta_end_user_my_requests

# =============================================================================
# ADMIN ROLES, RESOURCE SETS & API
# =============================================================================

# resource "okta_feature" "example" {
#   feature_id = "<feature-id>" # from data.okta_features
#   life_cycle = "ENABLE"       # ENABLE or DISABLE
# }

# resource "okta_admin_role_custom" "example" {
#   label       = "Custom Admin Role"
#   description = "Custom administrator role with specific permissions"
#   permissions = [
#     "okta.users.read",
#     "okta.users.userprofile.manage",
#     "okta.groups.read"
#   ]
# }

# Resource set: endpoints (resources) or ORNs (resources_orn)
# resource "okta_resource_set" "example" {
#   label       = "Example Resource Set"
#   description = "Resource set for delegated administration"
#   resources = [
#     "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/groups/${okta_group.example.id}"
#   ]
# }

# resource "okta_admin_role_custom_assignments" "example" {
#   resource_set_id = okta_resource_set.example.id
#   custom_role_id  = okta_admin_role_custom.example.id
#   members = [
#     "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/users/${okta_user.example.id}",
#     "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/groups/${okta_group.example.id}"
#   ]
# }

# Scope a built-in role to specific groups or apps (role_id is computed)
# resource "okta_admin_role_targets" "example" {
#   user_id   = okta_user.example.id
#   role_type = "GROUP_MEMBERSHIP_ADMIN"
#   groups    = [okta_group.example.id]
# }

# Admin email notification subscription for a role (v7: role_ref, no status)
# resource "okta_role_subscription" "example" {
#   role_ref          = "SUPER_ADMIN"
#   notification_type = "APP_IMPORT"
# }

# API service integration (OIN "API service" app) with granted scopes
# resource "okta_api_service_integration" "example" {
#   type = "<integration-type>" # underscore-concatenated OIN integration name
#   granted_scopes {
#     scope = "okta.users.read"
#   }
# }

# =============================================================================
# ORG SETTINGS
# =============================================================================

# resource "okta_org_configuration" "example" {
#   company_name = "Example Corp"
#   website      = "https://example.com"
#   phone_number = "+1-555-555-5555"
#   address_1    = "123 Main St"
#   city         = "San Francisco"
#   state        = "CA"
#   country      = "US"
#   postal_code  = "94105"
# }

# Temporarily grant Okta Support admin access (8h by default)
# resource "okta_org_support" "example" {
#   extend_by = 1 # extra days
# }

# =============================================================================
# LINKING & PROFILE MAPPINGS
# =============================================================================

# resource "okta_link_definition" "example" {
#   primary_name           = "manager"
#   primary_title          = "Manager"
#   primary_description    = "Manager relationship"
#   associated_name        = "subordinate"
#   associated_title       = "Subordinate"
#   associated_description = "Subordinate relationship"
# }

# resource "okta_link_value" "example" {
#   primary_user_id     = okta_user.example.id
#   primary_name        = okta_link_definition.example.primary_name
#   associated_user_ids = [okta_user.another_user.id]
# }

# data "okta_user_profile_mapping_source" "example" {}

# resource "okta_profile_mapping" "example" {
#   source_id = okta_idp_oidc.example.id
#   target_id = data.okta_user_profile_mapping_source.example.id
#
#   mappings {
#     id         = "firstName"
#     expression = "appuser.firstName"
#   }
#
#   mappings {
#     id         = "lastName"
#     expression = "appuser.lastName"
#   }
# }

# =============================================================================
# IDENTITY SOURCES (custom identity source apps / anything-as-a-source)
# =============================================================================
# identity_source_id is the ID of the Custom Identity Source app instance.

# resource "okta_identity_source_group" "example" {
#   identity_source_id = "<identity-source-app-id>"
#   external_id        = "hr-group-123"
#   profile {
#     display_name = "HR Managers"
#     description  = "Imported from HR"
#   }
# }

# One-shot import job: stage users/groups/memberships then trigger the import
# resource "okta_identity_source_import" "example" {
#   identity_source_id = "<identity-source-app-id>"
#   upsert_users {
#     entity_type = "USERS"
#     profiles {
#       external_id = "emp-1001"
#       profile {
#         user_name  = "jane.doe@example.com"
#         email      = "jane.doe@example.com"
#         first_name = "Jane"
#         last_name  = "Doe"
#       }
#     }
#   }
# }

# =============================================================================
# COMMON DATA SOURCES (v7.0.0 has 109; the most useful ones)
# =============================================================================
# data "okta_user" "admin" {
#   search {
#     name  = "profile.email"
#     value = "admin@example.com"
#   }
# }
# data "okta_group" "everyone" { name = "Everyone" }
# data "okta_everyone_group" "everyone" {}
# data "okta_app" "existing" { label = "Salesforce" }
# data "okta_app_oauth" "existing" { label = "My OIDC App" }
# data "okta_app_saml" "existing" { label = "My SAML App" }
# data "okta_app_metadata_saml" "meta" { app_id = okta_app_saml.example.id }
# data "okta_auth_server" "default" { name = "default" }
# data "okta_authenticator" "verify" { key = "okta_verify" }
# data "okta_policy" "default_mfa" {
#   name = "Default Policy"
#   type = "MFA_ENROLL"
# }
# data "okta_default_policy" "access" { type = "ACCESS_POLICY" }
# data "okta_network_zone" "corp" { name = "Corporate" }
# data "okta_brands" "all" {}
# data "okta_features" "all" {}
# (okta_org_metadata "current" is declared at the top of this file)
# data "okta_idp_metadata_saml" "idp" { idp_id = okta_idp_saml.example.id }
# data "okta_device_assurance_policy" "mac" { name = "macOS Device Policy" }
# data "okta_iam_resource_set" "set" { id = okta_resource_set.example.id }
# data "okta_trusted_origins" "all" {}
# data "okta_threat_insight_settings" "current" {}
# data "okta_org_captcha" "current" {}

# =============================================================================
# RESOURCE COVERAGE (okta/okta v7.0.0)
# =============================================================================
#
# Provider totals: 162 resources, 109 data sources.
#
# By area (resources with examples above / total in provider):
# - Users, groups, realms, schema ............ 16 / 19
# - Applications, assignments, provisioning .. 24 / 34  (incl. okta_app_connection, okta_app_features, okta_push_group)
# - App sign-on policies ..................... 3 / 4    (okta_app_access_policy_assignment is discouraged by the provider)
# - Authorization servers .................... 8 / 8
# - Global policies & rules .................. 14 / 15  (+ 5 device assurance, 3 ITP policy rules)
# - Security, network, rate limiting ......... 10 / 10
# - Authenticators, factors, push ............ 5 / 8
# - Identity providers ....................... 4 / 4
# - Brands, themes, email, domains ........... 13 / 16
# - Hooks, keys, log streams ................. 5 / 5
# - OIG (entitlements, bundles, labels, owners,
#   requests, campaigns) ..................... 11 / 12  (+ 15 OIG data sources)
# - Admin roles, resource sets, subscriptions  10 / 24  (13 okta_oauth2_v1_clients_role_* variants)
# - Org settings, support, CAPTCHA ........... 5 / 5
# - Identity sources, devices, UI schema ..... 2 / 7
#
# Still API-only (see scripts/): label-to-resource assignment, risk rules /
# SOD policies, entitlement bundle grants, entitlement management enablement.
#
# =============================================================================
