terraform {
  required_version = ">= 1.9.0"

  required_providers {
    okta = {
      source  = "okta/okta"
      version = ">= 6.4.0, < 7.0.0" # Auto-update to latest 6.x
    }
  }

  # S3 Backend for State Storage
  # State is stored in S3 with DynamoDB locking
  # See aws-backend/README.md for setup instructions
  backend "s3" {
    bucket         = "okta-terraform-demo"
    key            = "Okta-GitOps/myorg/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "okta-terraform-state-lock"
  }
}

provider "okta" {
  org_name  = var.okta_org_name
  base_url  = var.okta_base_url
  api_token = var.okta_api_token
}
