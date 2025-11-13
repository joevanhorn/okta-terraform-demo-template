# ==============================================================================
# Network Outputs
# ==============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "ID of the public subnet"
  value       = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "ID of the private subnet"
  value       = aws_subnet.private.id
}

# ==============================================================================
# Domain Controller Outputs
# ==============================================================================

output "dc_instance_id" {
  description = "EC2 instance ID of the Domain Controller"
  value       = aws_instance.domain_controller.id
}

output "dc_private_ip" {
  description = "Private IP address of the Domain Controller"
  value       = aws_instance.domain_controller.private_ip
}

output "dc_public_ip" {
  description = "Public IP address of the Domain Controller (Elastic IP)"
  value       = aws_eip.dc.public_ip
}

output "dc_public_dns" {
  description = "Public DNS name of the Domain Controller"
  value       = aws_eip.dc.public_dns
}

# ==============================================================================
# Active Directory Information
# ==============================================================================

output "ad_domain_name" {
  description = "Active Directory domain name"
  value       = var.ad_domain_name
}

output "ad_netbios_name" {
  description = "Active Directory NetBIOS name"
  value       = var.ad_netbios_name
}

output "dc_hostname" {
  description = "Domain Controller hostname"
  value       = "${var.ad_netbios_name}-DC01"
}

# ==============================================================================
# Connection Information
# ==============================================================================

output "rdp_connection_string" {
  description = "RDP connection string for the Domain Controller"
  value       = "mstsc /v:${aws_eip.dc.public_ip}"
}

output "rdp_credentials" {
  description = "Administrator credentials (password is sensitive)"
  value = {
    username = "Administrator"
    domain   = var.ad_domain_name
    note     = "Password was set during terraform apply (TF_VAR_admin_password)"
  }
  sensitive = true
}

# ==============================================================================
# Next Steps
# ==============================================================================

output "next_steps" {
  description = "Instructions for completing setup"
  value = <<-EOT
    ===== Domain Controller Deployed Successfully =====

    1. WAIT FOR SETUP TO COMPLETE (~15-20 minutes)
       - Computer rename and reboot
       - AD-Domain-Services installation
       - Domain Controller promotion
       - AD structure creation (OUs, groups, users)

    2. CONNECT VIA RDP:
       - Address: ${aws_eip.dc.public_ip}
       - Username: Administrator
       - Password: [value from TF_VAR_admin_password]

    3. VERIFY DOMAIN CONTROLLER:
       - Open "Active Directory Users and Computers"
       - Verify domain: ${var.ad_domain_name}
       - Check OUs: Users, Groups, Computers, Service Accounts
       - Verify sample users exist

    4. INSTALL OKTA AD AGENT:
       - Agent installer: C:\Terraform\OktaADAgentSetup.exe
       - Or download from: ${var.okta_org_url}/admin/access/identity/directories
       - Follow wizard to configure sync

    5. CONFIGURE OKTA AD INTEGRATION:
       - Log in to Okta Admin Console
       - Go to Directory → Directory Integrations
       - Add Active Directory integration
       - Provide Domain Controller details
       - Configure sync settings

    6. VIEW LOGS:
       - Bootstrap log: C:\Terraform\bootstrap.log
       - Check for any errors during setup

    Default User Password: Welcome123!
    Sample Users: jadmin, ssupport, ehr, mrecruiter, dfinance, laccountant, tsales, jrep

    EOT
}
