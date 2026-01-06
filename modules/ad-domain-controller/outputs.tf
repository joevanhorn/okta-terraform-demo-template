# ==============================================================================
# ACTIVE DIRECTORY DOMAIN CONTROLLER MODULE - OUTPUTS
# ==============================================================================

# ==============================================================================
# INSTANCE INFORMATION
# ==============================================================================

output "instance_id" {
  description = "EC2 instance ID of the domain controller"
  value       = aws_instance.ad_dc.id
}

output "private_ip" {
  description = "Private IP address of the domain controller"
  value       = aws_instance.ad_dc.private_ip
}

output "public_ip" {
  description = "Public IP address of the domain controller"
  value       = var.assign_elastic_ip ? aws_eip.ad_dc[0].public_ip : aws_instance.ad_dc.public_ip
}

output "private_dns" {
  description = "Private DNS name of the domain controller"
  value       = aws_instance.ad_dc.private_dns
}

# ==============================================================================
# NETWORK INFORMATION
# ==============================================================================

output "vpc_id" {
  description = "VPC ID where the domain controller is deployed"
  value       = local.vpc_id
}

output "subnet_id" {
  description = "Subnet ID where the domain controller is deployed"
  value       = local.subnet_id
}

output "security_group_id" {
  description = "Security group ID for the domain controller"
  value       = aws_security_group.ad.id
}

# ==============================================================================
# IAM INFORMATION
# ==============================================================================

output "instance_role_arn" {
  description = "IAM role ARN for the EC2 instance"
  value       = aws_iam_role.ad_instance.arn
}

output "instance_profile_name" {
  description = "IAM instance profile name"
  value       = aws_iam_instance_profile.ad_instance.name
}

# ==============================================================================
# SECRETS MANAGER
# ==============================================================================

output "credentials_secret_arn" {
  description = "ARN of the Secrets Manager secret containing AD credentials"
  value       = aws_secretsmanager_secret.ad_credentials.arn
}

output "credentials_secret_name" {
  description = "Name of the Secrets Manager secret containing AD credentials"
  value       = aws_secretsmanager_secret.ad_credentials.name
}

# ==============================================================================
# AD CONFIGURATION
# ==============================================================================

output "domain_name" {
  description = "Active Directory domain name"
  value       = var.ad_domain_name
}

output "netbios_name" {
  description = "Active Directory NetBIOS name"
  value       = var.ad_netbios_name
}

# ==============================================================================
# SSM CONNECTION
# ==============================================================================

output "ssm_start_session_command" {
  description = "AWS CLI command to start an SSM session"
  value       = "aws ssm start-session --target ${aws_instance.ad_dc.id} --region ${var.aws_region}"
}

output "ssm_parameter_instance_id" {
  description = "SSM Parameter Store path for instance ID"
  value       = aws_ssm_parameter.ad_instance_id.name
}

output "ssm_parameter_private_ip" {
  description = "SSM Parameter Store path for private IP"
  value       = aws_ssm_parameter.ad_private_ip.name
}

# ==============================================================================
# CONNECTION INFORMATION
# ==============================================================================

output "connection_info" {
  description = "Connection information for the domain controller"
  value = {
    instance_id         = aws_instance.ad_dc.id
    private_ip          = aws_instance.ad_dc.private_ip
    public_ip           = var.assign_elastic_ip ? aws_eip.ad_dc[0].public_ip : aws_instance.ad_dc.public_ip
    domain_name         = var.ad_domain_name
    ssm_session_command = "aws ssm start-session --target ${aws_instance.ad_dc.id} --region ${var.aws_region}"
    credentials_secret  = aws_secretsmanager_secret.ad_credentials.name
  }
}
