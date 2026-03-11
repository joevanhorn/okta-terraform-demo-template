# Outputs for SCIM Server Infrastructure

# ===========================
# Infrastructure Outputs
# ===========================

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.scim_server.id
}

output "public_ip" {
  description = "Public IP address of the server"
  value       = aws_eip.scim_server.public_ip
}

output "domain_name" {
  description = "Domain name for the SCIM server"
  value       = var.domain_name
}

output "aws_region" {
  description = "AWS region where the server is deployed"
  value       = var.aws_region
}

output "vpc_id" {
  description = "VPC ID where the server is deployed"
  value       = var.vpc_id != "" ? var.vpc_id : "default VPC"
}

output "subnet_id" {
  description = "Subnet ID where the server is deployed"
  value       = var.subnet_id != "" ? var.subnet_id : "default subnet"
}

output "security_group_id" {
  description = "Security group ID for the SCIM server (created or existing)"
  value       = var.use_existing_security_group ? var.security_group_id : aws_security_group.scim_server[0].id
}

output "security_group_created" {
  description = "Whether a new security group was created (false = using existing)"
  value       = !var.use_existing_security_group
}

# ===========================
# Access URLs
# ===========================

output "dashboard_url" {
  description = "URL for the web dashboard"
  value       = "https://${var.domain_name}"
}

output "scim_base_url" {
  description = "SCIM Base URL to configure in Okta"
  value       = "https://${var.domain_name}/scim/v2"
}

output "scim_health_url" {
  description = "Health check endpoint"
  value       = "https://${var.domain_name}/health"
}

# ===========================
# Connection Commands
# ===========================

output "ssh_command" {
  description = "SSH command to connect to the server (if SSH key is configured)"
  value       = var.ssh_key_name != "" ? "ssh ubuntu@${aws_eip.scim_server.public_ip}" : "SSH not configured (no key pair specified)"
}

output "ssm_command" {
  description = "AWS Systems Manager command to connect"
  value       = "aws ssm start-session --target ${aws_instance.scim_server.id} --region ${var.aws_region}"
}

output "log_command" {
  description = "Command to view server setup logs (via SSH)"
  value       = var.ssh_key_name != "" ? "ssh ubuntu@${aws_eip.scim_server.public_ip} 'tail -f /var/log/user-data.log'" : "Use SSM Session Manager to view logs: /var/log/user-data.log"
}

# ===========================
# CloudWatch (Optional)
# ===========================

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group name (if enabled)"
  value       = var.enable_cloudwatch_logs ? aws_cloudwatch_log_group.scim_server[0].name : "CloudWatch logs disabled"
}

output "cloudwatch_console_url" {
  description = "CloudWatch console URL for logs (if enabled)"
  value       = var.enable_cloudwatch_logs ? "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#logsV2:log-groups/log-group/${replace(aws_cloudwatch_log_group.scim_server[0].name, "/", "$252F")}" : "CloudWatch logs disabled"
}

# ===========================
# Okta Configuration
# ===========================

output "okta_configuration" {
  description = "Okta SCIM configuration values (both Bearer and Basic auth options)"
  value = {
    scim_base_url            = "https://${var.domain_name}/scim/v2"
    authentication_type      = var.scim_basic_pass != "" ? "Basic Auth and Bearer Token" : "Bearer Token Only"
    header_auth_token        = var.scim_auth_token
    basic_auth_username      = var.scim_basic_user
    basic_auth_password      = var.scim_basic_pass
    unique_identifier_field  = "userName"
    supported_scim_version   = "2.0"
    push_new_users           = true
    push_profile_updates     = true
    push_groups              = true
    import_groups            = true
    reactivate_users         = true
  }
  sensitive = true
}

# ===========================
# Setup Instructions
# ===========================

output "setup_instructions" {
  description = "Next steps after deployment"
  value = <<-EOT
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                   SCIM Server Deployment Complete!                         ║
    ╚════════════════════════════════════════════════════════════════════════════╝

    📍 Server: https://${var.domain_name}

    ⏱️  WAIT: Server initialization takes ~5-10 minutes
       - Caddy installs and provisions SSL certificate
       - Python dependencies install
       - SCIM server starts

    🔍 Check Status:
       1. Health Check: curl https://${var.domain_name}/health
       2. Dashboard: Open https://${var.domain_name} in browser
       3. Server Logs: ${var.ssh_key_name != "" ? "ssh ubuntu@${aws_eip.scim_server.public_ip} 'tail -f /var/log/user-data.log'" : "Use SSM Session Manager"}

    🔗 Okta Setup:
       1. In Okta Admin Console: Applications → Applications
       2. Click "Browse App Catalog"
       3. Search for "SCIM 2.0 Test App (Header Auth)" or "SCIM 2.0 Test App (Basic Auth)"
       4. Add application
       5. Configure SCIM:
          - SCIM Base URL: https://${var.domain_name}/scim/v2
          - Unique Identifier: userName
          ${var.scim_basic_pass != "" ? "- Auth: HTTP Basic (user: ${var.scim_basic_user})" : "- Auth: Bearer Token"}
          - (Use sensitive okta_configuration output for credentials)

    📊 Test Connection:
       terraform output okta_configuration  # View SCIM credentials

    📝 See README.md for complete setup guide

    ════════════════════════════════════════════════════════════════════════════
  EOT
}
