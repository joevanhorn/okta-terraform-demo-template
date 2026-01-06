# ==============================================================================
# ACTIVE DIRECTORY DOMAIN CONTROLLER MODULE - VARIABLES
# ==============================================================================

# ==============================================================================
# REQUIRED VARIABLES
# ==============================================================================

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
}

variable "region_short" {
  description = "Short region identifier (e.g., use1, usw2, euw1)"
  type        = string
}

variable "ad_domain_name" {
  description = "Active Directory domain name (e.g., corp.example.com)"
  type        = string
}

variable "ad_netbios_name" {
  description = "NetBIOS name for the domain (e.g., CORP)"
  type        = string
}

# ==============================================================================
# NETWORK CONFIGURATION
# ==============================================================================

variable "create_vpc" {
  description = "Create a new VPC for AD infrastructure"
  type        = bool
  default     = true
}

variable "existing_vpc_id" {
  description = "Existing VPC ID (required if create_vpc = false)"
  type        = string
  default     = ""
}

variable "existing_subnet_id" {
  description = "Existing subnet ID (required if create_vpc = false)"
  type        = string
  default     = ""
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  description = "Availability zone for the subnet"
  type        = string
  default     = ""
}

# ==============================================================================
# EC2 INSTANCE CONFIGURATION
# ==============================================================================

variable "instance_type" {
  description = "EC2 instance type for the domain controller"
  type        = string
  default     = "t3.medium"
}

variable "root_volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 100
}

variable "key_pair_name" {
  description = "EC2 key pair name for RDP access (optional)"
  type        = string
  default     = ""
}

variable "assign_elastic_ip" {
  description = "Assign an Elastic IP to the domain controller"
  type        = bool
  default     = false
}

# ==============================================================================
# SECURITY CONFIGURATION
# ==============================================================================

variable "enable_rdp" {
  description = "Enable RDP access in security group"
  type        = bool
  default     = false
}

variable "rdp_allowed_cidrs" {
  description = "CIDR blocks allowed for RDP access"
  type        = list(string)
  default     = []
}

# ==============================================================================
# AD CONFIGURATION
# ==============================================================================

variable "ad_admin_username" {
  description = "AD administrator username"
  type        = string
  default     = "Administrator"
}

variable "create_sample_users" {
  description = "Create sample OUs, groups, and users for demo purposes"
  type        = bool
  default     = true
}

# ==============================================================================
# S3 SCRIPTS CONFIGURATION
# ==============================================================================

variable "scripts_bucket_name" {
  description = "S3 bucket containing setup scripts (optional)"
  type        = string
  default     = ""
}

variable "setup_script_s3_key" {
  description = "S3 key for the main setup script"
  type        = string
  default     = "scripts/userdata.ps1"
}

# ==============================================================================
# OKTA AD AGENT CONFIGURATION
# ==============================================================================

variable "okta_agent_token" {
  description = "Okta AD Agent installation token (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "okta_org_url" {
  description = "Okta organization URL for AD Agent (e.g., https://myorg.okta.com)"
  type        = string
  default     = ""
}

# ==============================================================================
# TAGS
# ==============================================================================

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}
