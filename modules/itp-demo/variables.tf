# ==============================================================================
# ITP Demo Module — Variables
# ==============================================================================
# All inputs for the ITP (Identity Threat Protection) demo infrastructure.
# Feature flags allow enabling/disabling individual components.
# ==============================================================================

variable "environment" {
  description = "Environment name, used in SSM paths and resource naming"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names (defaults to environment name)"
  type        = string
  default     = ""
}

variable "enable_session_replayer" {
  description = "Deploy the cross-region Lambda for real-mode session hijacking simulation"
  type        = bool
  default     = true
}

variable "enable_ssf_endpoint" {
  description = "Deploy the Lambda JWKS endpoint for SSF (Shared Signals Framework) mode"
  type        = bool
  default     = true
}

variable "enable_video_bucket" {
  description = "Create an S3 bucket for storing ITP demo video recordings"
  type        = bool
  default     = true
}

variable "attacker_region" {
  description = "AWS region for the attacker Lambda function (should differ from victim)"
  type        = string
  default     = "eu-west-1"
}

variable "ssm_prefix" {
  description = "SSM Parameter Store path prefix for ITP secrets and config"
  type        = string
  default     = ""
}

variable "video_retention_days" {
  description = "Number of days to retain demo video recordings in S3"
  type        = number
  default     = 90
}

variable "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions (for S3 bucket policy). Leave empty to skip bucket policy."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Purpose   = "ITP Demo"
    ManagedBy = "Terraform"
  }
}

# --- Computed Locals ---

locals {
  name_prefix = var.name_prefix != "" ? var.name_prefix : var.environment
  ssm_prefix  = var.ssm_prefix != "" ? var.ssm_prefix : "/${var.environment}/itp"
}
