# ==============================================================================
# REQUIRED VARIABLES
# ==============================================================================

variable "name_prefix" {
  description = "Prefix for all resource names (e.g., myorg-prod-use2)"
  type        = string
}

variable "environment" {
  description = "Environment name for tagging and SSM paths (e.g., myorg-prod)"
  type        = string
}

# ==============================================================================
# VPC CONFIGURATION
# ==============================================================================

variable "use_existing_vpc" {
  description = "Use an existing VPC instead of creating a new one"
  type        = bool
  default     = false
}

variable "existing_vpc_id" {
  description = "Existing VPC ID (required if use_existing_vpc = true)"
  type        = string
  default     = ""
}

variable "existing_subnet_ids" {
  description = "Existing subnet IDs for RDS (required if use_existing_vpc = true, need at least 2 in different AZs)"
  type        = list(string)
  default     = []
}

variable "vpc_cidr" {
  description = "CIDR block for the new VPC (ignored if use_existing_vpc = true)"
  type        = string
  default     = "10.5.0.0/16"
}

variable "subnet_a_cidr" {
  description = "CIDR block for subnet A (ignored if use_existing_vpc = true)"
  type        = string
  default     = "10.5.1.0/24"
}

variable "subnet_b_cidr" {
  description = "CIDR block for subnet B (ignored if use_existing_vpc = true)"
  type        = string
  default     = "10.5.2.0/24"
}

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "okta_connector"
}

variable "db_username" {
  description = "Database admin username"
  type        = string
  default     = "oktaadmin"
}

variable "postgres_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.10"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Max storage for autoscaling in GB"
  type        = number
  default     = 100
}

variable "backup_retention_days" {
  description = "Backup retention in days"
  type        = number
  default     = 7
}

variable "publicly_accessible" {
  description = "Make RDS publicly accessible (for demo/OPC access)"
  type        = bool
  default     = true
}

variable "db_allowed_cidrs" {
  description = "CIDR blocks allowed to access PostgreSQL"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# ==============================================================================
# TAGS
# ==============================================================================

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
