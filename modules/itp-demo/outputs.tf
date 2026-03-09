# ==============================================================================
# ITP Demo Module — Outputs
# ==============================================================================

# --- Session Replayer ---

output "lambda_function_name" {
  description = "Name of the attacker Lambda function"
  value       = var.enable_session_replayer ? aws_lambda_function.replayer[0].function_name : null
}

output "lambda_function_arn" {
  description = "ARN of the attacker Lambda function"
  value       = var.enable_session_replayer ? aws_lambda_function.replayer[0].arn : null
}

output "lambda_region" {
  description = "Region where the attacker Lambda is deployed"
  value       = var.attacker_region
}

# --- SSF JWKS Endpoint ---

output "ssf_jwks_url" {
  description = "Public JWKS URL for SSF provider registration"
  value       = var.enable_ssf_endpoint ? aws_lambda_function_url.ssf_jwks[0].function_url : null
}

output "ssf_key_id" {
  description = "Key ID used in JWKS and SET headers"
  value       = var.enable_ssf_endpoint ? random_id.ssf_key_id[0].hex : null
}

output "ssf_issuer" {
  description = "Issuer URL for SSF provider (same as JWKS URL)"
  value       = var.enable_ssf_endpoint ? aws_lambda_function_url.ssf_jwks[0].function_url : null
}

output "ssf_ssm_prefix" {
  description = "SSM parameter prefix for SSF config"
  value       = var.enable_ssf_endpoint ? "${local.ssm_prefix}/ssf-demo" : null
}

# --- Video Bucket ---

output "video_bucket_name" {
  description = "S3 bucket name for ITP demo video recordings"
  value       = var.enable_video_bucket ? aws_s3_bucket.itp_demo_videos[0].bucket : null
}

output "video_bucket_arn" {
  description = "S3 bucket ARN for ITP demo video recordings"
  value       = var.enable_video_bucket ? aws_s3_bucket.itp_demo_videos[0].arn : null
}
