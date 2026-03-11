# ==============================================================================
# AD INFRASTRUCTURE VARIABLES
# ==============================================================================

# ==============================================================================
# PROJECT SETTINGS
# ==============================================================================

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "okta-gitops-demo"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "myorg"
}

# ==============================================================================
# AWS SETTINGS
# ==============================================================================

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "availability_zone" {
  description = "Availability zone (defaults to <region>a if not specified)"
  type        = string
  default     = ""
}

# ==============================================================================
# NETWORK SETTINGS
# ==============================================================================

variable "create_vpc" {
  description = "Create a new VPC or use existing"
  type        = bool
  default     = true
}

variable "existing_vpc_id" {
  description = "Existing VPC ID (when create_vpc = false)"
  type        = string
  default     = ""
}

variable "existing_subnet_id" {
  description = "Existing subnet ID (when create_vpc = false)"
  type        = string
  default     = ""
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR block"
  type        = string
  default     = "10.0.1.0/24"
}

# ==============================================================================
# EC2 INSTANCE SETTINGS
# ==============================================================================

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "root_volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 100
}

variable "key_pair_name" {
  description = "EC2 key pair name (optional)"
  type        = string
  default     = ""
}

variable "assign_elastic_ip" {
  description = "Assign Elastic IP to instance"
  type        = bool
  default     = false
}

# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

variable "enable_rdp" {
  description = "Enable RDP access"
  type        = bool
  default     = false
}

variable "rdp_allowed_cidrs" {
  description = "CIDR blocks allowed for RDP"
  type        = list(string)
  default     = []
}

# ==============================================================================
# ACTIVE DIRECTORY SETTINGS
# ==============================================================================

variable "ad_domain_name" {
  description = "AD domain name (e.g., corp.example.com)"
  type        = string
  default     = "corp.demo.local"
}

variable "ad_netbios_name" {
  description = "AD NetBIOS name"
  type        = string
  default     = "CORP"
}

variable "ad_admin_username" {
  description = "AD administrator username"
  type        = string
  default     = "Administrator"
}

variable "create_sample_users" {
  description = "Create sample OUs, groups, and users"
  type        = bool
  default     = true
}

# ==============================================================================
# S3 SCRIPTS SETTINGS
# ==============================================================================

variable "scripts_bucket_name" {
  description = "S3 bucket for setup scripts"
  type        = string
  default     = ""
}

variable "setup_script_s3_key" {
  description = "S3 key for setup script"
  type        = string
  default     = "scripts/userdata.ps1"
}

# ==============================================================================
# OKTA AD AGENT SETTINGS
# ==============================================================================

variable "okta_agent_token" {
  description = "Okta AD Agent registration token"
  type        = string
  default     = ""
  sensitive   = true
}

variable "okta_org_url" {
  description = "Okta organization URL"
  type        = string
  default     = ""
}

# ==============================================================================
# TAGS
# ==============================================================================

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
