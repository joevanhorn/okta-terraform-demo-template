# ==============================================================================
# OPC AGENT MODULE OUTPUTS
# ==============================================================================

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.opc_agent.id
}

output "private_ip" {
  description = "Private IP address"
  value       = aws_instance.opc_agent.private_ip
}

output "public_ip" {
  description = "Public IP address (Elastic IP)"
  value       = aws_eip.opc_agent.public_ip
}

output "eip_allocation_id" {
  description = "Elastic IP allocation ID"
  value       = aws_eip.opc_agent.id
}

output "instance_name" {
  description = "Instance name tag"
  value       = local.agent_name
}

output "iam_role_arn" {
  description = "IAM role ARN"
  value       = aws_iam_role.opc_agent.arn
}

output "ssm_session_command" {
  description = "AWS SSM Session Manager connection command"
  value       = "aws ssm start-session --target ${aws_instance.opc_agent.id} --region ${var.region_short == "use2" ? "us-east-2" : var.region_short}"
}

output "connector_info" {
  description = "Connector configuration information"
  value = {
    type            = var.connector_type
    instance_number = var.instance_number
    database_host   = var.database_host
    okta_org_url    = var.okta_org_url
  }
}

output "ssm_parameters" {
  description = "SSM parameter paths for this agent"
  value = {
    instance_id = aws_ssm_parameter.instance_id.name
    private_ip  = aws_ssm_parameter.private_ip.name
  }
}
