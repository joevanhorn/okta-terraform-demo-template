# ==============================================================================
# General Configuration
# ==============================================================================

variable "environment_name" {
  description = "Environment name (matches Okta environment directory name)"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region for infrastructure"
  type        = string
  default     = "us-east-1"
}

# ==============================================================================
# Network Configuration
# ==============================================================================

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnet"
  type        = string
  default     = "10.0.2.0/24"
}

variable "allowed_rdp_cidrs" {
  description = "List of CIDR blocks allowed to RDP to Domain Controller"
  type        = list(string)
  default     = ["0.0.0.0/0"] # CHANGE THIS: Restrict to your IP or VPN
}

# ==============================================================================
# Active Directory Configuration
# ==============================================================================

variable "ad_domain_name" {
  description = "Active Directory domain name (e.g., demo.local)"
  type        = string
  default     = "demo.local"
}

variable "ad_netbios_name" {
  description = "Active Directory NetBIOS name"
  type        = string
  default     = "DEMO"
}

variable "ad_safe_mode_password" {
  description = "Active Directory Safe Mode (DSRM) Administrator password"
  type        = string
  sensitive   = true
  # IMPORTANT: Set this via environment variable or tfvars file
  # Example: export TF_VAR_ad_safe_mode_password="YourSecurePassword123!"
}

variable "admin_password" {
  description = "Windows Administrator password"
  type        = string
  sensitive   = true
  # IMPORTANT: Set this via environment variable or tfvars file
  # Example: export TF_VAR_admin_password="YourAdminPassword123!"
}

# ==============================================================================
# EC2 Configuration
# ==============================================================================

variable "dc_instance_type" {
  description = "EC2 instance type for Domain Controller"
  type        = string
  default     = "t3.medium" # Minimum recommended for DC
}

variable "dc_volume_size" {
  description = "Root volume size in GB for Domain Controller"
  type        = number
  default     = 50
}

variable "key_pair_name" {
  description = "Name of existing EC2 key pair for SSH/RDP access (optional)"
  type        = string
  default     = null
}

# ==============================================================================
# Okta Configuration
# ==============================================================================

variable "okta_org_url" {
  description = "Okta organization URL (e.g., https://dev-12345.okta.com)"
  type        = string
  # IMPORTANT: Set this via environment variable or tfvars file
  # This is used by scripts to download the Okta AD Agent
}

variable "okta_opa_enabled" {
  description = "Enable Okta Privileged Access integration"
  type        = bool
  default     = true
}

# ==============================================================================
# Tags
# ==============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
