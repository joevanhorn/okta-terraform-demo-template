# =============================================================================
# OKTA TERRAFORM PROVIDER - COMPLETE RESOURCE REFERENCE
# =============================================================================
# This file provides commented examples for ALL Okta Terraform resources
# available in provider v6.1.0+. Use these examples as templates when creating
# new resources.
#
# Documentation: https://registry.terraform.io/providers/okta/okta/latest/docs
#
# NOTE: All examples are COMMENTED OUT. Uncomment and customize as needed.
# =============================================================================

# =============================================================================
# IDENTITY & ACCESS MANAGEMENT (9 resources)
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

# resource "okta_user_schema" "example" {
#   index       = "customAttribute"
#   title       = "Custom Attribute"
#   type        = "string"
#   description = "A custom user attribute"
#   master      = "PROFILE_MASTER"
#   scope       = "NONE"
# }

# resource "okta_user_base_schema" "example" {
#   index  = "email"
#   title  = "Primary email"
#   type   = "string"
#   required = true
#   master = "PROFILE_MASTER"
# }

# resource "okta_user_type" "example" {
#   name         = "contractor"
#   display_name = "Contractor"
#   description  = "Contractor user type"
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
#   for_each   = local.users_map
#   email      = each.value.email
#   first_name = each.value.first_name
#   last_name  = each.value.last_name
#   login      = each.value.login
#   status     = coalesce(each.value.status, "ACTIVE")
#   department = try(each.value.department, null)
#   title      = try(each.value.title, null)
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

# resource "okta_group_schema" "example" {
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

# resource "okta_group_memberships" "example" {
#   group_id = okta_group.example.id
#   users    = [okta_user.example.id]
# }

# resource "okta_user_group_memberships" "example" {
#   user_id = okta_user.example.id
#   groups  = [okta_group.example.id]
# }

# =============================================================================
# APPLICATIONS (14+ resources)
# =============================================================================

# -----------------------------------------------------------------------------
# OAuth / OIDC Applications
# -----------------------------------------------------------------------------

# resource "okta_app_oauth" "example" {
#   label                      = "Example OAuth App"
#   type                       = "web"
#   grant_types                = ["authorization_code", "refresh_token"]
#   redirect_uris              = ["https://example.com/callback"]
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
# }

# resource "okta_app_oauth_redirect_uri" "example" {
#   app_id = okta_app_oauth.example.id
#   uri    = "https://example.com/another-callback"
# }

# resource "okta_app_oauth_post_logout_redirect_uri" "example" {
#   app_id = okta_app_oauth.example.id
#   uri    = "https://example.com/logout"
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
# }

# resource "okta_app_saml_app_settings" "example" {
#   app_id   = okta_app_saml.example.id
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

# resource "okta_app_secure_password_store" "example" {
#   label              = "SWA App"
#   username_field     = "user"
#   password_field     = "pass"
#   url                = "https://example.com/login"
#   optional_field1    = "optional1"
#   optional_field1_value = "value1"
# }

# resource "okta_app_three_field" "example" {
#   label                    = "Three Field App"
#   button_selector          = "#login-button"
#   username_selector        = "#username"
#   password_selector        = "#password"
#   extra_field_selector     = "#company"
#   extra_field_value        = "company-name"
#   url                      = "https://example.com/login"
#   credential_type          = "ADMIN_SETS_CREDENTIALS"
# }

# resource "okta_app_auto_login" "example" {
#   label                 = "Auto Login App"
#   sign_on_url           = "https://example.com/login"
#   sign_on_redirect_url  = "https://example.com/app"
#   credential_type       = "ADMIN_SETS_CREDENTIALS"
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

# resource "okta_app_user_schema" "example" {
#   app_id      = okta_app_oauth.example.id
#   index       = "customField"
#   title       = "Custom Field"
#   type        = "string"
#   description = "Custom field for app user profile"
#   master      = "OKTA"
# }

# resource "okta_app_user_base_schema" "example" {
#   app_id = okta_app_oauth.example.id
#   index  = "email"
#   title  = "Email"
#   type   = "string"
#   master = "OKTA"
# }

# =============================================================================
# AUTHORIZATION SERVERS (7 resources)
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
#   name           = "Example Rule"
#   auth_server_id = okta_auth_server.example.id
#   policy_id      = okta_auth_server_policy.example.id
#   priority       = 1
#   grant_type_whitelist = ["authorization_code", "refresh_token"]
#   scope_whitelist      = ["openid", "profile", "email"]
# }

# resource "okta_auth_server_claim" "example" {
#   name                = "custom_claim"
#   auth_server_id      = okta_auth_server.example.id
#   claim_type          = "RESOURCE"
#   value_type          = "EXPRESSION"
#   value               = "user.customAttribute"
#   scopes              = ["profile"]
#   status              = "ACTIVE"
#   always_include_in_token = false
# }

# resource "okta_auth_server_claim_default" "example" {
#   name           = "sub"
#   auth_server_id = okta_auth_server_default.example.id
#   value          = "user.id"
# }

# resource "okta_auth_server_scope" "example" {
#   name           = "custom_scope"
#   auth_server_id = okta_auth_server.example.id
#   description    = "Custom OAuth scope"
#   consent        = "REQUIRED"
#   metadata_publish = "ALL_CLIENTS"
# }

# =============================================================================
# POLICIES (18+ resources)
# =============================================================================

# -----------------------------------------------------------------------------
# MFA Policies
# -----------------------------------------------------------------------------

# resource "okta_policy_mfa" "example" {
#   name        = "Example MFA Policy"
#   status      = "ACTIVE"
#   description = "Multi-factor authentication policy"
#   priority    = 1
#   groups_included = [okta_group.example.id]
#
#   okta_verify = {
#     enroll = "REQUIRED"
#   }
# }

# resource "okta_policy_mfa_default" "example" {
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
#   name        = "Example Password Policy"
#   status      = "ACTIVE"
#   description = "Password policy"
#   priority    = 1
#   groups_included = [okta_group.example.id]
#
#   password_min_length          = 12
#   password_min_lowercase       = 1
#   password_min_uppercase       = 1
#   password_min_number          = 1
#   password_min_symbol          = 1
#   password_exclude_username    = true
#   password_exclude_first_name  = true
#   password_exclude_last_name   = true
#   password_max_age_days        = 90
#   password_expire_warn_days    = 15
#   password_min_age_minutes     = 0
#   password_history_count       = 5
#   password_max_lockout_attempts = 5
#   password_auto_unlock_minutes = 15
#   password_show_lockout_failures = true
#   password_lockout_notification_channels = ["EMAIL"]
# }

# resource "okta_policy_password_default" "example" {
#   password_min_length = 8
# }

# resource "okta_policy_rule_password" "example" {
#   name                  = "Example Password Rule"
#   policy_id             = okta_policy_password.example.id
#   status                = "ACTIVE"
#   priority              = 1
#   password_change       = "KEEP_EXISTING"
#   password_reset        = "KEEP_EXISTING"
#   password_unlock       = "KEEP_EXISTING"
# }

# -----------------------------------------------------------------------------
# Sign-On Policies
# -----------------------------------------------------------------------------

# resource "okta_policy_signon" "example" {
#   name        = "Example Sign-On Policy"
#   status      = "ACTIVE"
#   description = "Sign-on policy"
#   priority    = 1
#   groups_included = [okta_group.example.id]
# }

# resource "okta_policy_rule_signon" "example" {
#   name                       = "Example Sign-On Rule"
#   policy_id                  = okta_policy_signon.example.id
#   status                     = "ACTIVE"
#   priority                   = 1
#   access                     = "ALLOW"
#   authtype                   = "ANY"
#   mfa_required               = true
#   mfa_prompt                 = "ALWAYS"
#   mfa_remember_device        = false
#   mfa_lifetime               = 60
#   session_idle               = 120
#   session_lifetime           = 240
#   session_persistent         = false
# }

# -----------------------------------------------------------------------------
# Profile Enrollment
# -----------------------------------------------------------------------------

# resource "okta_policy_profile_enrollment" "example" {
#   name   = "Example Enrollment Policy"
#   status = "ACTIVE"
# }

# resource "okta_policy_profile_enrollment_apps" "example" {
#   policy_id = okta_policy_profile_enrollment.example.id
#   apps      = [okta_app_oauth.example.id]
# }

# -----------------------------------------------------------------------------
# Device Assurance Policies
# -----------------------------------------------------------------------------

# resource "okta_policy_device_assurance_windows" "example" {
#   name                       = "Windows Device Policy"
#   os_version                 = "10.0.0"
#   disk_encryption_type       = ["BITLOCKER"]
#   secure_hardware_present    = true
#   screenlock_type            = ["BIOMETRIC"]
# }

# resource "okta_policy_device_assurance_macos" "example" {
#   name                       = "macOS Device Policy"
#   os_version                 = "13.0.0"
#   disk_encryption_type       = ["FILEVAULT"]
#   secure_hardware_present    = true
#   screenlock_type            = ["BIOMETRIC", "PASSCODE"]
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
#   name                = "iOS Device Policy"
#   os_version          = "15.0"
#   jailbreak           = false
#   screenlock_type     = ["BIOMETRIC", "PASSCODE"]
# }

# resource "okta_policy_device_assurance_chromeos" "example" {
#   name        = "ChromeOS Device Policy"
#   os_version  = "100.0"
#   tpsp_allow_screen_lock           = true
#   tpsp_browser_version             = "100.0.0"
#   tpsp_builtin_dns_client_enabled  = true
#   tpsp_chrome_remote_desktop_app_blocked = true
#   tpsp_site_isolation_enabled      = true
# }

# =============================================================================
# SECURITY (6+ resources)
# =============================================================================

# resource "okta_network_zone" "example" {
#   name     = "Example Network Zone"
#   type     = "IP"
#   status   = "ACTIVE"
#   gateways = ["1.2.3.4/24", "5.6.7.8/24"]
#   proxies  = ["9.10.11.12/24"]
# }

# resource "okta_trusted_origin" "example" {
#   name   = "Example Trusted Origin"
#   origin = "https://example.com"
#   scopes = ["CORS", "REDIRECT"]
# }

# resource "okta_behavior" "example" {
#   name            = "New City"
#   type            = "VELOCITY"
#   status          = "ACTIVE"
#   settings = {
#     velocity_kph = "40"
#   }
# }

# resource "okta_threat_insight_settings" "example" {
#   action    = "block"
#   network_excludes = ["192.168.1.0/24"]
# }

# resource "okta_rate_limiting" "example" {
#   login                 = 50
#   authorize             = 100
#   communications_enabled = true
# }

# resource "okta_authenticator" "example" {
#   name   = "Okta Verify"
#   key    = "okta_verify"
#   status = "ACTIVE"
# }

# =============================================================================
# IDENTITY PROVIDERS (4 resources)
# =============================================================================

# resource "okta_idp_saml" "example" {
#   name                     = "Example SAML IdP"
#   acs_type                 = "INSTANCE"
#   sso_url                  = "https://idp.example.com/sso"
#   sso_destination          = "https://idp.example.com/sso"
#   sso_binding              = "HTTP-POST"
#   username_template        = "idpuser.email"
#   issuer                   = "https://idp.example.com"
#   request_signature_algorithm = "SHA-256"
#   request_signature_scope  = "REQUEST"
#   response_signature_algorithm = "SHA-256"
#   response_signature_scope = "RESPONSE"
# }

# resource "okta_idp_saml_key" "example" {
#   x5c = [file("saml.crt")]
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
#   client_secret         = "client-secret"
#   issuer_url            = "https://idp.example.com"
#   username_template     = "idpuser.email"
# }

# resource "okta_idp_social" "example" {
#   name          = "Google"
#   type          = "GOOGLE"
#   protocol_type = "OAUTH2"
#   scopes        = ["profile", "email", "openid"]
#   client_id     = "google-client-id"
#   client_secret = "google-client-secret"
#   username_template = "idpuser.email"
# }

# =============================================================================
# BRANDS & THEMES (5 resources)
# =============================================================================

# resource "okta_brand" "example" {
#   name                          = "Example Brand"
#   agree_to_custom_privacy_policy = true
#   custom_privacy_policy_url     = "https://example.com/privacy"
# }

# resource "okta_theme" "example" {
#   brand_id                      = okta_brand.example.id
#   logo                          = filebase64("logo.png")
#   favicon                       = filebase64("favicon.ico")
#   background_image              = filebase64("background.jpg")
#   primary_color_hex             = "#1e5aa8"
#   primary_color_contrast_hex    = "#ffffff"
#   secondary_color_hex           = "#ebebed"
#   secondary_color_contrast_hex  = "#000000"
#   sign_in_page_touch_point_variant = "OKTA_DEFAULT"
#   end_user_dashboard_touch_point_variant = "OKTA_DEFAULT"
#   error_page_touch_point_variant = "OKTA_DEFAULT"
#   email_template_touch_point_variant = "OKTA_DEFAULT"
# }

# resource "okta_email_customization" "example" {
#   brand_id      = okta_brand.example.id
#   template_name = "UserActivation"
#   language      = "en"
#   subject       = "Welcome to ${org.name}!"
#   body          = file("email_templates/activation.html")
# }

# resource "okta_domain" "example" {
#   domain = "id.example.com"
# }

# resource "okta_domain_certificate" "example" {
#   domain_id   = okta_domain.example.id
#   certificate = file("cert.pem")
#   certificate_key = file("key.pem")  # Certificate's private key file
#   certificate_chain = file("chain.pem")
# }

# =============================================================================
# HOOKS & EVENT HANDLERS (3 resources)
# =============================================================================

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
#   name = "Example Event Hook"
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

# =============================================================================
# OKTA IDENTITY GOVERNANCE (OIG) - v6.1.0+ (9 resources)
# =============================================================================

# -----------------------------------------------------------------------------
# Access Reviews (Campaigns)
# -----------------------------------------------------------------------------

# resource "okta_reviews" "example" {
#   name        = "Quarterly Access Review"
#   description = "Review user access every quarter"
#   start_date  = "2025-01-01"
#   end_date    = "2025-03-31"
#
#   # Note: Exact schema may vary - check official docs
#   # This is the new OIG access certification campaign resource
# }

# -----------------------------------------------------------------------------
# Entitlement Bundles
# -----------------------------------------------------------------------------

# Entitlement bundles define collections of access rights
# Documentation: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/entitlement_bundle
#
# IMPORTANT: Bundles require Okta-generated value IDs, not external_value strings.
# Use dynamic blocks with for expressions to look up IDs by external_value.

# Example: Define account groupings in locals for reusability
# locals {
#   standard_accounts = ["DEMO38", "26DEMO26", "26DEMO14", "DEMO42"]
#   limited_accounts  = ["DEMO38", "DEMO42"]
#   all_accounts      = ["DEMO38", "26DEMO26", "26DEMO14", "DEMO2", "149259"]
# }

# Example: Basic bundle (hardcoded IDs - not recommended)
# resource "okta_entitlement_bundle" "basic_example" {
#   name        = "Sales Team Access"
#   description = "Standard access for sales team members"
#   status      = "ACTIVE"
#
#   target {
#     external_id = okta_app_oauth.my_app.id
#     type        = "APPLICATION"
#   }
#
#   entitlements {
#     id = okta_entitlement.my_entitlement.id
#     values {
#       id = "val..."  # Hardcoded Okta-generated ID
#     }
#   }
# }

# Example: Bundle with dynamic value lookups (RECOMMENDED)
# resource "okta_entitlement_bundle" "dynamic_example" {
#   name        = "Standard Access Bundle"
#   description = "Standard 4-account access"
#   status      = "ACTIVE"
#
#   target {
#     external_id = okta_app_oauth.my_app.id
#     type        = "APPLICATION"
#   }
#
#   entitlements {
#     id = okta_entitlement.app_accounts.id
#     dynamic "values" {
#       for_each = [
#         for v in okta_entitlement.app_accounts.values : v.id
#         if contains(local.standard_accounts, v.external_value)
#       ]
#       content {
#         id = values.value
#       }
#     }
#   }
#
#   # This approach:
#   # - Uses dynamic blocks (values is a block type, not an argument)
#   # - Filters values by external_value string
#   # - Returns the Okta-generated value ID
#   # - Creates proper resource dependencies for same-apply creation
# }

# Note: This resource manages the BUNDLE DEFINITION only
# Principal assignments (which users/groups have this bundle) should be
# managed via Okta Admin UI or direct API calls, not in Terraform

# -----------------------------------------------------------------------------
# Principal Entitlements (Assignments)
# -----------------------------------------------------------------------------

# resource "okta_principal_entitlements" "example" {
#   # WARNING: This resource manages principal ASSIGNMENTS to entitlement bundles
#   # It is NOT recommended to manage assignments in Terraform due to complexity
#   # and drift issues. Manage assignments in Okta Admin UI or via API instead.
#   #
#   # This resource is for assigning specific users/groups to entitlement bundles
#   # Only use if you have a strong requirement for IaC-managed assignments
#   #
#   # Documentation: https://registry.terraform.io/providers/okta/okta/latest/docs/resources/principal_entitlements
#
#   # Note: Schema TBD - this is a NEW resource in v6.1.0
# }

# -----------------------------------------------------------------------------
# Access Request Management
# -----------------------------------------------------------------------------

# resource "okta_request_conditions" "example" {
#   # Conditions for access requests (e.g., manager approval required)
#   # Part of the access request workflow system
#
#   # Note: Exact schema TBD - NEW in v6.1.0
# }

# resource "okta_request_sequences" "example" {
#   # Multi-stage approval workflows for access requests
#   # Define who approves requests and in what order
#
#   # Note: Exact schema TBD - NEW in v6.1.0
# }

# resource "okta_request_settings" "example" {
#   # Global settings for access request system
#   # Configure request expiration, notifications, etc.
#
#   # Note: Exact schema TBD - NEW in v6.1.0
# }

# resource "okta_request_v2" "example" {
#   # Programmatic access requests
#   # Request access to resources on behalf of users
#
#   # Note: Exact schema TBD - NEW in v6.1.0
# }

# -----------------------------------------------------------------------------
# Resource Catalog
# -----------------------------------------------------------------------------

# resource "okta_catalog_entry_default" "example" {
#   # Make resources (apps, groups, entitlements) requestable
#   # Users can request access through self-service portal
#
#   # Note: Exact schema TBD - NEW in v6.1.0
# }

# resource "okta_catalog_entry_user_access_request_fields" "example" {
#   # Custom fields shown when users request access
#   # Collect additional information during request (e.g., business justification)
#
#   # Note: Exact schema TBD - NEW in v6.1.0
# }

# -----------------------------------------------------------------------------
# End User Views
# -----------------------------------------------------------------------------

# data "okta_end_user_my_requests" "example" {
#   # Data source to query user's access requests
#   # Used for building custom dashboards/UIs
#
#   # Note: This is a DATA SOURCE, not a resource
# }

# =============================================================================
# FEATURES & ADMIN (5 resources)
# =============================================================================

# resource "okta_feature" "example" {
#   name   = "EXAMPLE_FEATURE"
#   status = "ENABLED"
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

# resource "okta_admin_role_targets" "example" {
#   user_id  = okta_user.example.id
#   role_type = "CUSTOM"
#   role_id   = okta_admin_role_custom.example.id
#   groups    = [okta_group.example.id]
#   apps      = [okta_app_oauth.example.id]
# }

# resource "okta_resource_set" "example" {
#   label       = "Example Resource Set"
#   description = "Resource set for delegated administration"
#   resources   = [
#     "https://${var.okta_org_name}.${var.okta_base_url}/api/v1/groups/${okta_group.example.id}"
#   ]
# }

# resource "okta_user_admin_roles" "example" {
#   user_id = okta_user.example.id
#   admin_roles = [
#     "USER_ADMIN",
#     "APP_ADMIN"
#   ]
# }

#locals {
#  org_url = "https://mycompany.okta.com"
#}
#
#resource "okta_admin_role_custom" "test" {
#  label       = "SomeUsersAndApps"
#  description = "Manage apps assignments and users"
#  permissions = ["okta.apps.assignment.manage", "okta.users.manage", "okta.apps.manage"]
#}
#
#resource "okta_resource_set" "test" {
#  label       = "UsersWithApp"
#  description = "All the users and SWA app"
#  resources = [
#    format("%s/api/v1/users", local.org_url),
#    format("%s/api/v1/apps/%s", local.org_url, okta_app_swa.test.id)
#  ]
#}
#
#// this user and group will manage the set of resources based on the permissions specified in the custom role
#resource "okta_admin_role_custom_assignments" "test" {
#  resource_set_id = okta_resource_set.test.id
#  custom_role_id  = okta_admin_role_custom.test.id
#  members = [
#    format("%s/api/v1/users/%s", local.org_url, okta_user.test.id),
#    format("%s/api/v1/groups/%s", local.org_url, okta_group.test.id)
#  ]
#}
#
#// this user will have `CUSTOM` role assigned, but it won't appear in the `admin_roles` for that user,
#// since direct assignment of custom roles is not allowed
#resource "okta_user" "test" {
#  first_name = "Paul"
#  last_name  = "Atreides"
#  login      = "no-reply@caladan.planet"
#  email      = "no-reply@caladan.planet"
#}
#
#resource "okta_app_swa" "test" {
#  label          = "My SWA App"
#  button_field   = "btn-login"
#  password_field = "txtbox-password"
#  username_field = "txtbox-username"
#  url            = "https://example.com/login.html"
#}
#
#resource "okta_group" "test" {
#  name        = "General"
#  description = "General Group"
#}

# =============================================================================
# ORG SETTINGS (4 resources)
# =============================================================================

# resource "okta_org_configuration" "example" {
#   company_name  = "Example Corp"
#   website       = "https://example.com"
#   phone_number  = "+1-555-555-5555"
#   address_1     = "123 Main St"
#   city          = "San Francisco"
#   state         = "CA"
#   country       = "US"
#   postal_code   = "94105"
# }

# resource "okta_org_support" "example" {
#   phone_number = "+1-555-555-5555"
#   extend_by    = 0  # Days to extend support phone number expiration
# }

# resource "okta_captcha" "example" {
#   name       = "Example CAPTCHA"
#   type       = "RECAPTCHA_V2"
#   site_key   = "recaptcha-site-key"
#   secret_key = "recaptcha-secret-key"
# }

# resource "okta_captcha_org_wide_settings" "example" {
#   enabled_for = ["SSPR", "REGISTRATION"]
#   captcha_id  = okta_captcha.example.id
# }

# =============================================================================
# LINKING & ASSOCIATIONS (3 resources)
# =============================================================================

# resource "okta_link_definition" "example" {
#   primary_name        = "manager"
#   primary_title       = "Manager"
#   primary_description = "Manager relationship"
#   associated_name     = "subordinate"
#   associated_title    = "Subordinate"
#   associated_description = "Subordinate relationship"
# }

# resource "okta_link_value" "example" {
#   primary_user_id   = okta_user.example.id
#   primary_name      = okta_link_definition.example.primary_name
#   associated_user_ids = [okta_user.another_user.id]
# }

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
# TEMPLATES & LOGS (2 resources)
# =============================================================================

# resource "okta_template_sms" "example" {
#   type        = "SMS_VERIFY_CODE"
#   template    = "Your verification code is ${code}"
#   translations = {
#     it = "Il tuo codice di verifica è ${code}"
#     fr = "Votre code de vérification est ${code}"
#     es = "Su código de verificación es ${code}"
#   }
# }

# resource "okta_log_stream" "example" {
#   name   = "Example Log Stream"
#   type   = "aws_eventbridge"
#   status = "ACTIVE"
#   settings = {
#     accountId = "123456789012"
#     eventSourceName = "okta-log-stream"
#     region = "us-east-1"
#   }
# }

# =============================================================================
# RESOURCE COUNT SUMMARY
# =============================================================================
#
# Total Resources: ~100+
#
# By Category:
# - Identity & Access: 9 resources
# - Applications: 14+ resources
# - Authorization Servers: 7 resources
# - Policies: 18+ resources
# - Security: 6+ resources
# - Identity Providers: 4 resources
# - Brands & Themes: 5 resources
# - Hooks & Events: 3 resources
# - OIG (v6.1.0+): 9 resources
# - Features & Admin: 5 resources
# - Org Settings: 4 resources
# - Linking: 3 resources
# - Templates & Logs: 2 resources
#
# =============================================================================
