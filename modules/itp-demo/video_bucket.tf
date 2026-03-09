# ==============================================================================
# ITP Demo Videos S3 Bucket
# ==============================================================================
# Dedicated S3 bucket for storing ITP real-mode demo video recordings.
# Videos are uploaded by the trigger_itp_demo.py script (--upload-s3 flag)
# and by GitHub Actions workflows when record_video is enabled.
#
# Features:
#   - Configurable auto-expiration (default: 90 days)
#   - AES256 server-side encryption
#   - Public access fully blocked
#   - Optional GitHub Actions OIDC role has PutObject/GetObject access
# ==============================================================================

# --- S3 Bucket ---

resource "aws_s3_bucket" "itp_demo_videos" {
  count = var.enable_video_bucket ? 1 : 0

  bucket = "${local.name_prefix}-itp-demo-videos"

  tags = var.tags
}

# --- Lifecycle: Auto-expire ---

resource "aws_s3_bucket_lifecycle_configuration" "itp_demo_videos" {
  count = var.enable_video_bucket ? 1 : 0

  bucket = aws_s3_bucket.itp_demo_videos[0].id

  rule {
    id     = "expire-after-${var.video_retention_days}-days"
    status = "Enabled"

    expiration {
      days = var.video_retention_days
    }
  }
}

# --- Encryption: AES256 ---

resource "aws_s3_bucket_server_side_encryption_configuration" "itp_demo_videos" {
  count = var.enable_video_bucket ? 1 : 0

  bucket = aws_s3_bucket.itp_demo_videos[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# --- Block all public access ---

resource "aws_s3_bucket_public_access_block" "itp_demo_videos" {
  count = var.enable_video_bucket ? 1 : 0

  bucket = aws_s3_bucket.itp_demo_videos[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- Bucket policy: Allow GitHub Actions role (optional) ---

resource "aws_s3_bucket_policy" "itp_demo_videos" {
  count = var.enable_video_bucket && var.github_actions_role_arn != "" ? 1 : 0

  bucket = aws_s3_bucket.itp_demo_videos[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowGitHubActionsAccess"
        Effect = "Allow"
        Principal = {
          AWS = var.github_actions_role_arn
        }
        Action = [
          "s3:PutObject",
          "s3:GetObject",
        ]
        Resource = "${aws_s3_bucket.itp_demo_videos[0].arn}/*"
      }
    ]
  })
}
