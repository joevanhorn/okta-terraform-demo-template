# ==============================================================================
# SSF (Shared Signals Framework) JWKS Endpoint
# ==============================================================================
# Hosts a public JWKS endpoint via Lambda Function URL for SSF demo.
# Okta fetches this JWKS to verify Security Event Token (SET) signatures.
#
# Resources created:
#   - RSA key pair (tls_private_key)
#   - Lambda function serving JWKS JSON
#   - Lambda Function URL (public, no auth)
#   - SSM parameters for private key and provider config
#   - IAM role for Lambda execution
#
# After terraform apply:
#   1. Run setup_ssf_provider.py to register the provider with Okta
#   2. Use trigger_itp_demo.py --mode ssf to send signals
# ==============================================================================

# --- Key Generation ---

resource "random_id" "ssf_key_id" {
  count = var.enable_ssf_endpoint ? 1 : 0

  byte_length = 4
  prefix      = "ssf-demo-"
}

resource "tls_private_key" "ssf_demo" {
  count = var.enable_ssf_endpoint ? 1 : 0

  algorithm = "RSA"
  rsa_bits  = 2048
}

# Convert public key PEM to JWKS format
data "external" "ssf_jwks" {
  count = var.enable_ssf_endpoint ? 1 : 0

  program = ["python3", "${path.module}/scripts/pem_to_jwks.py"]

  query = {
    public_key_pem = tls_private_key.ssf_demo[0].public_key_pem
    key_id         = random_id.ssf_key_id[0].hex
  }
}

# --- Lambda Function ---

data "archive_file" "ssf_jwks_lambda" {
  count = var.enable_ssf_endpoint ? 1 : 0

  type        = "zip"
  output_path = "${path.module}/ssf_jwks_lambda.zip"

  source {
    content  = <<-PYTHON
import json
import os

def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "public, max-age=3600",
        },
        "body": os.environ["JWKS_JSON"],
    }
    PYTHON
    filename = "index.py"
  }
}

resource "aws_iam_role" "ssf_jwks_lambda" {
  count = var.enable_ssf_endpoint ? 1 : 0

  name = "${local.name_prefix}-ssf-jwks-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ssf_jwks_lambda_basic" {
  count = var.enable_ssf_endpoint ? 1 : 0

  role       = aws_iam_role.ssf_jwks_lambda[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "ssf_jwks" {
  count = var.enable_ssf_endpoint ? 1 : 0

  function_name    = "${local.name_prefix}-ssf-jwks"
  role             = aws_iam_role.ssf_jwks_lambda[0].arn
  handler          = "index.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.ssf_jwks_lambda[0].output_path
  source_code_hash = data.archive_file.ssf_jwks_lambda[0].output_base64sha256
  timeout          = 5
  memory_size      = 128

  environment {
    variables = {
      JWKS_JSON = data.external.ssf_jwks[0].result.jwks_json
    }
  }

  tags = var.tags
}

resource "aws_lambda_function_url" "ssf_jwks" {
  count = var.enable_ssf_endpoint ? 1 : 0

  function_name      = aws_lambda_function.ssf_jwks[0].function_name
  authorization_type = "NONE"
}

# --- SSM Parameters ---

resource "aws_ssm_parameter" "ssf_private_key" {
  count = var.enable_ssf_endpoint ? 1 : 0

  name        = "${local.ssm_prefix}/ssf-demo/private-key"
  description = "SSF Demo - RSA private key for SET signing"
  type        = "SecureString"
  value       = tls_private_key.ssf_demo[0].private_key_pem

  tags = var.tags
}

resource "aws_ssm_parameter" "ssf_provider_config" {
  count = var.enable_ssf_endpoint ? 1 : 0

  name        = "${local.ssm_prefix}/ssf-demo/provider-config"
  description = "SSF Demo - Provider configuration (update provider_id after Okta registration)"
  type        = "String"
  value = jsonencode({
    issuer        = aws_lambda_function_url.ssf_jwks[0].function_url
    jwks_url      = aws_lambda_function_url.ssf_jwks[0].function_url
    key_id        = random_id.ssf_key_id[0].hex
    provider_name = "ITP Demo Signal Source"
    provider_id   = "pending-registration"
  })

  lifecycle {
    ignore_changes = [value]
  }

  tags = var.tags
}
