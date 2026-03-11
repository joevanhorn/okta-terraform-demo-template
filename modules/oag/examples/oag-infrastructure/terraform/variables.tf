# OAG Infrastructure Variables

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
  default     = "demo"
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "oag"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# OAG Instance Configuration
variable "oag_ami_id" {
  description = "AMI ID for OAG appliance (import OVA first)"
  type        = string
}

variable "oag_instance_type" {
  description = "EC2 instance type for OAG"
  type        = string
  default     = "t3.medium"
}

variable "oag_volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 60
}

variable "key_pair_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
  default     = ""
}

# Domain Configuration
variable "oag_domain" {
  description = "Primary domain for OAG (e.g., oag.example.com)"
  type        = string
}

variable "oag_san_domains" {
  description = "Additional domains for certificate (SAN)"
  type        = list(string)
  default     = []
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID (leave empty if not using Route53)"
  type        = string
  default     = ""
}

# Security Configuration
variable "admin_cidr_blocks" {
  description = "CIDR blocks allowed to access admin console"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict in production!
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for ALB"
  type        = bool
  default     = false
}

# Okta Configuration
variable "okta_org_url" {
  description = "Okta organization URL (e.g., https://dev-12345.okta.com)"
  type        = string
  default     = ""
}
