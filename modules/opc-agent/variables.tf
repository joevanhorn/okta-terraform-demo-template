# ==============================================================================
# REQUIRED VARIABLES
# ==============================================================================

variable "environment" {
  description = "Environment name (e.g., myorg-prod)"
  type        = string
}

variable "region_short" {
  description = "Short region identifier (e.g., use2, usw2)"
  type        = string
}

variable "connector_type" {
  description = "OPC connector type: generic-db, oracle-ebs, or sap"
  type        = string

  validation {
    condition     = contains(["generic-db", "oracle-ebs", "sap"], var.connector_type)
    error_message = "connector_type must be one of: generic-db, oracle-ebs, sap"
  }
}

variable "instance_number" {
  description = "Instance number for HA deployments (1, 2, etc.)"
  type        = number
  default     = 1

  validation {
    condition     = var.instance_number >= 1 && var.instance_number <= 10
    error_message = "instance_number must be between 1 and 10"
  }
}

variable "vpc_id" {
  description = "VPC ID for deployment"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for EC2 instance (should be public for Okta connectivity)"
  type        = string
}

variable "security_group_ids" {
  description = "List of security group IDs to attach"
  type        = list(string)
}

# ==============================================================================
# OPTIONAL VARIABLES
# ==============================================================================

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "root_volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 30
}

variable "okta_org_url" {
  description = "Okta organization URL (e.g., https://myorg.okta.com)"
  type        = string
}

variable "database_host" {
  description = "Database host for this connector"
  type        = string
  default     = ""
}

variable "jdbc_driver_url" {
  description = "URL to download JDBC driver"
  type        = string
  default     = ""
}

variable "key_pair_name" {
  description = "EC2 key pair name (optional, SSM preferred)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

# ==============================================================================
# AMI CONFIGURATION
# ==============================================================================

variable "custom_ami_id" {
  description = "Custom AMI ID (leave empty to use latest RHEL 8). Use pre-built OPC Agent AMI for faster deployment."
  type        = string
  default     = ""
}

variable "use_prebuilt_ami" {
  description = "Set to true when using the pre-built OPC Agent AMI (uses simplified bootstrap)"
  type        = bool
  default     = false
}

# ==============================================================================
# OPA PAM CONFIGURATION
# ==============================================================================

variable "opa_enrollment_token" {
  description = "OPA PAM enrollment token for automatic sftd enrollment. If provided, sftd will auto-enroll during bootstrap."
  type        = string
  default     = ""
  sensitive   = true
}
