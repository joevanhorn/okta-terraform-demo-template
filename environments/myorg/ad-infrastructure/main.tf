# ==============================================================================
# AD INFRASTRUCTURE - MULTI-REGION DEPLOYMENT
# ==============================================================================
# This configuration deploys AD Domain Controllers to one or more AWS regions.
# Each region gets an independent domain controller using the shared module.
#
# Usage:
#   terraform init
#   terraform workspace new us-east-1   # or select: terraform workspace select us-east-1
#   terraform apply -var="aws_region=us-east-1"
#
# Or use the GitHub Actions workflow for automated multi-region deployment.
# ==============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0"
    }
  }

  backend "s3" {
    bucket         = "okta-terraform-demo"
    key            = "Okta-GitOps/myorg/ad-infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }
}

# ==============================================================================
# PROVIDER CONFIGURATION
# ==============================================================================

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ==============================================================================
# LOCAL VALUES
# ==============================================================================

locals {
  # Region short names for resource naming
  region_short_names = {
    "us-east-1"      = "use1"
    "us-east-2"      = "use2"
    "us-west-1"      = "usw1"
    "us-west-2"      = "usw2"
    "eu-west-1"      = "euw1"
    "eu-west-2"      = "euw2"
    "eu-central-1"   = "euc1"
    "ap-southeast-1" = "apse1"
    "ap-southeast-2" = "apse2"
    "ap-northeast-1" = "apne1"
  }

  region_short = lookup(local.region_short_names, var.aws_region, replace(var.aws_region, "-", ""))

  # Availability zone defaults per region
  default_azs = {
    "us-east-1"      = "us-east-1a"
    "us-east-2"      = "us-east-2a"
    "us-west-1"      = "us-west-1a"
    "us-west-2"      = "us-west-2a"
    "eu-west-1"      = "eu-west-1a"
    "eu-west-2"      = "eu-west-2a"
    "eu-central-1"   = "eu-central-1a"
    "ap-southeast-1" = "ap-southeast-1a"
    "ap-southeast-2" = "ap-southeast-2a"
    "ap-northeast-1" = "ap-northeast-1a"
  }

  availability_zone = var.availability_zone != "" ? var.availability_zone : lookup(local.default_azs, var.aws_region, "${var.aws_region}a")
}

# ==============================================================================
# AD DOMAIN CONTROLLER MODULE
# ==============================================================================

module "ad_dc" {
  source = "../../../modules/ad-domain-controller"

  # Required settings
  environment     = var.environment
  aws_region      = var.aws_region
  region_short    = local.region_short
  ad_domain_name  = var.ad_domain_name
  ad_netbios_name = var.ad_netbios_name

  # Network settings
  create_vpc         = var.create_vpc
  existing_vpc_id    = var.existing_vpc_id
  existing_subnet_id = var.existing_subnet_id
  vpc_cidr           = var.vpc_cidr
  public_subnet_cidr = var.public_subnet_cidr
  availability_zone  = local.availability_zone

  # Instance settings
  instance_type     = var.instance_type
  root_volume_size  = var.root_volume_size
  key_pair_name     = var.key_pair_name
  assign_elastic_ip = var.assign_elastic_ip

  # Security settings
  enable_rdp        = var.enable_rdp
  rdp_allowed_cidrs = var.rdp_allowed_cidrs

  # AD settings
  ad_admin_username   = var.ad_admin_username
  create_sample_users = var.create_sample_users

  # S3 scripts (optional)
  scripts_bucket_name = var.scripts_bucket_name
  setup_script_s3_key = var.setup_script_s3_key

  # Okta AD Agent (optional)
  okta_agent_token = var.okta_agent_token
  okta_org_url     = var.okta_org_url

  # Tags
  tags = var.tags
}

# ==============================================================================
# OUTPUTS
# ==============================================================================

output "instance_id" {
  description = "EC2 instance ID"
  value       = module.ad_dc.instance_id
}

output "private_ip" {
  description = "Private IP address"
  value       = module.ad_dc.private_ip
}

output "public_ip" {
  description = "Public IP address"
  value       = module.ad_dc.public_ip
}

output "domain_name" {
  description = "AD domain name"
  value       = module.ad_dc.domain_name
}

output "credentials_secret_arn" {
  description = "Secrets Manager ARN for AD credentials"
  value       = module.ad_dc.credentials_secret_arn
}

output "ssm_session_command" {
  description = "AWS CLI command to start SSM session"
  value       = module.ad_dc.ssm_start_session_command
}

output "connection_info" {
  description = "All connection information"
  value       = module.ad_dc.connection_info
  sensitive   = true
}
