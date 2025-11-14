# SCIM 2.0 Server Infrastructure
# Deploys a custom SCIM server for demonstrating API-only entitlements in Okta
#
# This infrastructure creates:
# - EC2 instance running Flask SCIM server
# - Caddy reverse proxy with automatic HTTPS (Let's Encrypt)
# - Security group for HTTPS/HTTP access
# - Route53 DNS record
# - IAM role for SSM access (optional SSH)
#
# The SCIM server demonstrates:
# - Custom application with entitlement/role management
# - Okta OPP (On-Premise Provisioning) integration
# - API-only entitlements that don't map to app resources
# - Role-based access control for custom apps

# Data source: Latest Ubuntu 22.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Security Group for SCIM Server (only created if not using existing)
resource "aws_security_group" "scim_server" {
  count = var.use_existing_security_group ? 0 : 1

  name_prefix = "scim-demo-"
  description = "Security group for SCIM entitlements demo server"
  vpc_id      = var.vpc_id != "" ? var.vpc_id : null

  # SSH access (only if ssh_key_name is provided)
  dynamic "ingress" {
    for_each = var.ssh_key_name != "" ? [1] : []
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = var.allowed_ssh_cidr
      description = "SSH access"
    }
  }

  # HTTP (redirects to HTTPS via Caddy)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP (redirects to HTTPS)"
  }

  # HTTPS - restricted by CIDR
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.allowed_https_cidr
    description = "HTTPS for SCIM API and dashboard"
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(
    var.tags,
    {
      Name = "scim-demo-security-group"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# IAM Role for EC2 (allows SSM access for management)
resource "aws_iam_role" "scim_server" {
  name_prefix = "scim-demo-ec2-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "scim-demo-ec2-role"
    }
  )
}

# Attach SSM policy for Session Manager access (no SSH keys required)
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.scim_server.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Optional: CloudWatch Logs policy for log streaming
resource "aws_iam_role_policy_attachment" "cloudwatch_logs" {
  count      = var.enable_cloudwatch_logs ? 1 : 0
  role       = aws_iam_role.scim_server.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "scim_server" {
  name_prefix = "scim-demo-"
  role        = aws_iam_role.scim_server.name

  tags = merge(
    var.tags,
    {
      Name = "scim-demo-instance-profile"
    }
  )
}

# Elastic IP for stable address
resource "aws_eip" "scim_server" {
  domain = "vpc"

  tags = merge(
    var.tags,
    {
      Name = "scim-demo-elastic-ip"
    }
  )
}

# EC2 Instance
resource "aws_instance" "scim_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.ssh_key_name != "" ? var.ssh_key_name : null
  subnet_id              = var.subnet_id != "" ? var.subnet_id : null
  vpc_security_group_ids = var.use_existing_security_group ? [var.security_group_id] : [aws_security_group.scim_server[0].id]
  iam_instance_profile   = aws_iam_instance_profile.scim_server.name

  # User data script for server initialization
  user_data = templatefile("${path.module}/user-data.sh", {
    domain_name         = var.domain_name
    scim_auth_token     = var.scim_auth_token
    scim_basic_user     = var.scim_basic_user
    scim_basic_pass     = var.scim_basic_pass
    github_repo         = var.github_repo
    scim_server_path    = var.scim_server_path
    custom_entitlements = var.custom_entitlements
  })

  user_data_replace_on_change = true

  root_block_device {
    volume_size = var.root_volume_size
    volume_type = "gp3"
    encrypted   = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2 only
    http_put_response_hop_limit = 1
  }

  tags = merge(
    var.tags,
    {
      Name = "scim-demo-server"
    }
  )

  lifecycle {
    ignore_changes = [ami] # Don't replace on AMI updates
  }
}

# Associate Elastic IP with Instance
resource "aws_eip_association" "scim_server" {
  instance_id   = aws_instance.scim_server.id
  allocation_id = aws_eip.scim_server.id
}

# Route53 DNS Record
resource "aws_route53_record" "scim_server" {
  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "A"
  ttl     = 300
  records = [aws_eip.scim_server.public_ip]
}

# CloudWatch Log Group (optional - for future log streaming)
resource "aws_cloudwatch_log_group" "scim_server" {
  count             = var.enable_cloudwatch_logs ? 1 : 0
  name              = "/aws/ec2/scim-demo/${var.environment}"
  retention_in_days = var.log_retention_days

  tags = merge(
    var.tags,
    {
      Name = "scim-demo-logs"
    }
  )
}
