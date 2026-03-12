# AWS Provider Configuration for SCIM Server Infrastructure
# This is separate from Okta Terraform resources

terraform {
  backend "s3" {
    # Backend configuration should match your main infrastructure
    # Update these values to match your setup or use terraform.tfvars
    bucket         = "okta-terraform-demo"           # Your S3 bucket name
    key            = "Okta-GitOps/myorg/scim-server/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }

  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Okta Terraform Demo - SCIM Server"
      Repository  = "okta-terraform-demo-template"
      ManagedBy   = "Terraform"
      Environment = var.environment
      Purpose     = "Custom SCIM Integration for API-Only Entitlements"
    }
  }
}
