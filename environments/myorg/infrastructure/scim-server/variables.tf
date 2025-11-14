# Variables for SCIM Server Infrastructure

variable "aws_region" {
  description = "AWS region to deploy SCIM server"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (matches parent directory)"
  type        = string
  default     = "myorg"
}

variable "domain_name" {
  description = "Fully qualified domain name for SCIM server (e.g., scim.demo-myorg.com)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]\\.[a-z]{2,}$", var.domain_name))
    error_message = "Domain name must be a valid FQDN (e.g., scim.example.com)"
  }
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for your domain"
  type        = string

  validation {
    condition     = can(regex("^Z[A-Z0-9]+$", var.route53_zone_id))
    error_message = "Route53 zone ID must start with Z followed by alphanumeric characters"
  }
}

variable "instance_type" {
  description = "EC2 instance type for SCIM server"
  type        = string
  default     = "t3.micro"

  validation {
    condition     = can(regex("^t[23]\\.(micro|small|medium)", var.instance_type))
    error_message = "Instance type should be t2/t3 micro, small, or medium for cost efficiency"
  }
}

variable "scim_auth_token" {
  description = "Bearer token for SCIM authentication (generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.scim_auth_token) >= 32
    error_message = "SCIM auth token must be at least 32 characters for security"
  }
}

variable "scim_basic_user" {
  description = "Username for HTTP Basic authentication (alternative to bearer token)"
  type        = string
  default     = "okta_scim_user"
}

variable "scim_basic_pass" {
  description = "Password for HTTP Basic authentication (generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
  type        = string
  sensitive   = true
  default     = ""  # Empty means Basic Auth disabled, Bearer only
}

variable "ssh_key_name" {
  description = "Optional SSH key pair name for EC2 access (leave empty to disable SSH access)"
  type        = string
  default     = ""
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed to SSH to the server (only used if ssh_key_name is set)"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict this in production!
}

variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch Logs for SCIM server monitoring"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365], var.log_retention_days)
    error_message = "Log retention must be a valid CloudWatch value"
  }
}

variable "root_volume_size" {
  description = "Size of root EBS volume in GB"
  type        = number
  default     = 8
}

variable "github_repo" {
  description = "GitHub repository to download SCIM server code from"
  type        = string
  default     = "joevanhorn/okta-terraform-demo-template"
}

variable "scim_server_path" {
  description = "Path to SCIM server code within repository"
  type        = string
  default     = "main/environments/myorg/infrastructure/scim-server"
}

variable "custom_entitlements" {
  description = "Custom entitlements/roles for your application (JSON)"
  type        = string
  default     = ""  # If empty, uses default 5 roles
}

# ===========================
# Network Configuration
# ===========================

variable "vpc_id" {
  description = "VPC ID to deploy into (leave empty for default VPC)"
  type        = string
  default     = ""
}

variable "subnet_id" {
  description = "Subnet ID to deploy into (leave empty for default subnet in default VPC)"
  type        = string
  default     = ""
}

variable "use_existing_security_group" {
  description = "Use an existing security group instead of creating one"
  type        = bool
  default     = false
}

variable "security_group_id" {
  description = "Existing security group ID to use (only when use_existing_security_group = true)"
  type        = string
  default     = ""

  validation {
    condition     = var.use_existing_security_group == false || (var.use_existing_security_group == true && var.security_group_id != "")
    error_message = "security_group_id must be provided when use_existing_security_group is true"
  }
}

variable "allowed_https_cidr" {
  description = "CIDR blocks allowed to access HTTPS/SCIM API (only used when creating security group). Restrict to Okta IP ranges + your network for production."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# ===========================
# Additional Configuration
# ===========================

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
