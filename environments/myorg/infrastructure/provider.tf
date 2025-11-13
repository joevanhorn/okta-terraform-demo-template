terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration - stores state in S3
  # State path: s3://okta-terraform-demo/Okta-GitOps/{environment}/infrastructure/terraform.tfstate
  backend "s3" {
    bucket         = "okta-terraform-demo"
    key            = "Okta-GitOps/myorg/infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment_name
      Project     = "Okta-Demo-Infrastructure"
      ManagedBy   = "Terraform"
      Purpose     = "Active-Directory-Lab"
    }
  }
}
