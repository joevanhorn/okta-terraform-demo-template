# ==============================================================================
# ITP Demo Module — Session Replayer Lambda
# ==============================================================================
# Deploys a Lambda function to a remote region that replays an Okta session
# cookie from a different geographic context, triggering Okta's session
# hijacking detection for the ITP (Identity Threat Protection) demo.
#
# This is the "attacker" side of the real-mode ITP demo.
# ==============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  alias  = "attacker"
  region = var.attacker_region
}

# --- IAM Role for Lambda ---

data "aws_iam_policy_document" "lambda_assume_role" {
  count = var.enable_session_replayer ? 1 : 0

  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "replayer" {
  count = var.enable_session_replayer ? 1 : 0

  name               = "${local.name_prefix}-itp-session-replayer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role[0].json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "replayer_basic" {
  count = var.enable_session_replayer ? 1 : 0

  role       = aws_iam_role.replayer[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Lambda Function ---

data "archive_file" "replayer" {
  count = var.enable_session_replayer ? 1 : 0

  type        = "zip"
  source_file = "${path.module}/lambda/replayer.py"
  output_path = "${path.module}/lambda/replayer.zip"
}

resource "aws_lambda_function" "replayer" {
  count    = var.enable_session_replayer ? 1 : 0
  provider = aws.attacker

  function_name = "${local.name_prefix}-itp-session-replayer"
  description   = "ITP Demo - Replays Okta session cookies from ${var.attacker_region} to trigger session hijacking detection"

  filename         = data.archive_file.replayer[0].output_path
  source_code_hash = data.archive_file.replayer[0].output_base64sha256

  handler = "replayer.handler"
  runtime = "python3.11"
  timeout = 30

  role = aws_iam_role.replayer[0].arn

  tags = var.tags
}
