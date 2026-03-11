# OAG Infrastructure Outputs

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.oag.id
}

output "public_subnets" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnets" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.oag.dns_name
}

output "alb_zone_id" {
  description = "ALB zone ID"
  value       = aws_lb.oag.zone_id
}

output "oag_instance_id" {
  description = "OAG EC2 instance ID"
  value       = aws_instance.oag.id
}

output "oag_private_ip" {
  description = "OAG private IP address"
  value       = aws_instance.oag.private_ip
}

output "oag_security_group_id" {
  description = "OAG security group ID"
  value       = aws_security_group.oag.id
}

output "oag_admin_url" {
  description = "OAG Admin Console URL"
  value       = "https://${aws_instance.oag.private_ip}:8443"
}

output "oag_public_url" {
  description = "OAG public URL (via ALB)"
  value       = "https://${var.oag_domain}"
}

output "certificate_arn" {
  description = "ACM certificate ARN"
  value       = aws_acm_certificate.oag.arn
}

output "target_group_arn" {
  description = "Target group ARN for additional backend apps"
  value       = aws_lb_target_group.oag.arn
}

# Values needed for OAG configuration
output "oag_configuration" {
  description = "Configuration values for OAG setup"
  value = {
    hostname    = var.oag_domain
    private_ip  = aws_instance.oag.private_ip
    admin_url   = "https://${aws_instance.oag.private_ip}:8443"
    public_url  = "https://${var.oag_domain}"
    vpc_id      = aws_vpc.oag.id
    alb_sg_id   = aws_security_group.alb.id
    oag_sg_id   = aws_security_group.oag.id
  }
}
