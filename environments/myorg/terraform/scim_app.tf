# ==============================================================================
# SCIM Application - Okta Integration with Custom SCIM Server
# ==============================================================================
#
# This file creates an Okta application configured to provision users to a
# custom SCIM 2.0 server deployed via the infrastructure/scim-server module.
#
# IMPORTANT: Terraform Provider Limitations
# -----------------------------------------
# The Okta Terraform provider does NOT yet support:
#   - SCIM connection configuration (base URL, authentication)
#   - Testing SCIM connections
#   - Enabling specific provisioning features
#   - Configuring attribute mappings
#
# These must be configured using the Okta Admin API via Python script.
#
# Two-Step Process:
# -----------------
# 1. Terraform: Creates the Okta app (this file)
# 2. Python: Configures SCIM connection (scripts/configure_scim_app.py)
#
# ==============================================================================

# Read SCIM server infrastructure outputs
data "terraform_remote_state" "scim_server" {
  backend = "s3"

  config = {
    bucket = "okta-terraform-demo"
    key    = "Okta-GitOps/${var.scim_environment}/scim-server/terraform.tfstate"
    region = var.scim_aws_region
  }
}

# ==============================================================================
# SCIM Application Resource
# ==============================================================================

# Note: We use okta_app_auto_login as it's the closest match for a custom SCIM app
# The actual SCIM configuration must be done via API (see scripts/configure_scim_app.py)
resource "okta_app_auto_login" "scim_demo" {
  label = var.scim_app_label

  # Visibility settings
  hide_ios = true
  hide_web = true

  # Credentials
  credentials_scheme = "SHARED_USERNAME_AND_PASSWORD"

  # Sign-on URL (SCIM server dashboard)
  sign_on_url = data.terraform_remote_state.scim_server.outputs.dashboard_url

  # Optional redirect URL
  sign_on_redirect_url = data.terraform_remote_state.scim_server.outputs.dashboard_url
}

# ==============================================================================
# App Group Assignments (Optional)
# ==============================================================================

# Uncomment to automatically assign groups to the SCIM app
# resource "okta_app_group_assignments" "scim_demo" {
#   app_id = okta_app_auto_login.scim_demo.id
#
#   group {
#     id = var.scim_app_group_id
#     priority = 1
#   }
# }

# ==============================================================================
# Outputs
# ==============================================================================

output "scim_app_id" {
  description = "Okta application ID for SCIM demo app"
  value       = okta_app_auto_login.scim_demo.id
}

output "scim_app_name" {
  description = "Okta application name"
  value       = okta_app_auto_login.scim_demo.name
}

output "scim_app_label" {
  description = "Okta application label"
  value       = okta_app_auto_login.scim_demo.label
}

output "scim_app_admin_url" {
  description = "Direct link to app in Okta Admin Console"
  sensitive   = true
  value       = "https://${var.okta_org_name}.${var.okta_base_url}/admin/app/${okta_app_auto_login.scim_demo.name}/instance/${okta_app_auto_login.scim_demo.id}/"
}

output "scim_server_url" {
  description = "SCIM server base URL (from infrastructure)"
  value       = data.terraform_remote_state.scim_server.outputs.scim_base_url
}

output "scim_server_dashboard" {
  description = "SCIM server dashboard URL (from infrastructure)"
  value       = data.terraform_remote_state.scim_server.outputs.dashboard_url
}

output "scim_configuration_command" {
  description = "Command to configure SCIM connection via Python script"
  value       = <<-EOT
    python3 scripts/configure_scim_app.py \
      --app-id ${okta_app_auto_login.scim_demo.id} \
      --scim-url ${data.terraform_remote_state.scim_server.outputs.scim_base_url} \
      --test-connection
  EOT
}

output "scim_setup_instructions" {
  description = "Next steps after Terraform apply"
  sensitive   = true
  value       = <<-EOT
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║              SCIM App Created - Configuration Required                     ║
    ╚════════════════════════════════════════════════════════════════════════════╝

    ✅ Okta App Created: ${okta_app_auto_login.scim_demo.label}
    🔗 App ID: ${okta_app_auto_login.scim_demo.id}
    🌐 SCIM Server: ${data.terraform_remote_state.scim_server.outputs.scim_base_url}

    ⚠️  SCIM Connection NOT Configured Yet!

    The Okta Terraform provider cannot configure SCIM connection settings.
    Complete configuration using ONE of these methods:

    ════════════════════════════════════════════════════════════════════════════
    OPTION 1: Automated (Python Script) - Recommended
    ════════════════════════════════════════════════════════════════════════════

    cd environments/${var.scim_environment}
    python3 ../../scripts/configure_scim_app.py \
      --app-id ${okta_app_auto_login.scim_demo.id} \
      --scim-url ${data.terraform_remote_state.scim_server.outputs.scim_base_url} \
      --test-connection

    ════════════════════════════════════════════════════════════════════════════
    OPTION 2: Manual (Okta Admin Console)
    ════════════════════════════════════════════════════════════════════════════

    1. Open app in Admin Console:
       ${var.okta_org_name}.${var.okta_base_url}/admin/app/${okta_app_auto_login.scim_demo.name}/instance/${okta_app_auto_login.scim_demo.id}/

    2. Go to "Provisioning" tab
    3. Click "Configure API Integration"
    4. Enable "Enable API integration"
    5. Enter SCIM connection details:
       - SCIM Base URL: ${data.terraform_remote_state.scim_server.outputs.scim_base_url}
       - Unique Identifier: userName
       - Auth: Use credentials from SCIM server terraform.tfstate

    6. Test connection
    7. Save
    8. Enable provisioning features (Create, Update, Deactivate users)

    ════════════════════════════════════════════════════════════════════════════

    📖 See: environments/myorg/infrastructure/scim-server/README.md for details

  EOT
}
