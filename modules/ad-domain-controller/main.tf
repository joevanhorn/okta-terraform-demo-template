# ==============================================================================
# ACTIVE DIRECTORY DOMAIN CONTROLLER MODULE
# ==============================================================================
# Creates a Windows Server EC2 instance configured as an AD Domain Controller
# with full IAM roles, Secrets Manager integration, and SSM management support.
#
# Features:
# - VPC with public/private subnets (optional - can use existing)
# - Windows Server 2022 EC2 instance
# - IAM roles for SSM management
# - Secrets Manager for credentials
# - Security groups for AD traffic
# - Two-stage PowerShell bootstrap pattern
# ==============================================================================

terraform {
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
}

# ==============================================================================
# LOCAL VALUES
# ==============================================================================

locals {
  name_prefix = "${var.environment}-${var.region_short}"

  common_tags = merge(var.tags, {
    Environment = var.environment
    Region      = var.aws_region
    ManagedBy   = "terraform"
    Module      = "ad-domain-controller"
  })
}

# ==============================================================================
# RANDOM PASSWORD FOR AD ADMIN
# ==============================================================================

resource "random_password" "ad_admin" {
  length           = 20
  special          = true
  override_special = "!@#$%^&*"
  min_lower        = 2
  min_upper        = 2
  min_numeric      = 2
  min_special      = 2
}

# ==============================================================================
# SECRETS MANAGER - AD CREDENTIALS
# ==============================================================================

resource "aws_secretsmanager_secret" "ad_credentials" {
  name        = "${local.name_prefix}-ad-credentials"
  description = "Active Directory administrator credentials for ${var.environment}"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "ad_credentials" {
  secret_id = aws_secretsmanager_secret.ad_credentials.id
  secret_string = jsonencode({
    domain_name       = var.ad_domain_name
    netbios_name      = var.ad_netbios_name
    admin_username    = var.ad_admin_username
    admin_password    = random_password.ad_admin.result
    safe_mode_password = random_password.ad_admin.result
  })
}

# ==============================================================================
# IAM ROLE FOR EC2 (SSM + Secrets Manager Access)
# ==============================================================================

resource "aws_iam_role" "ad_instance" {
  name = "${local.name_prefix}-ad-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ssm_managed_instance" {
  role       = aws_iam_role.ad_instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "secrets_access" {
  name = "${local.name_prefix}-secrets-access"
  role = aws_iam_role.ad_instance.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.ad_credentials.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "s3_scripts_access" {
  count = var.scripts_bucket_name != "" ? 1 : 0
  name  = "${local.name_prefix}-s3-scripts-access"
  role  = aws_iam_role.ad_instance.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.scripts_bucket_name}",
          "arn:aws:s3:::${var.scripts_bucket_name}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ad_instance" {
  name = "${local.name_prefix}-ad-instance-profile"
  role = aws_iam_role.ad_instance.name

  tags = local.common_tags
}

# ==============================================================================
# VPC RESOURCES (OPTIONAL - CREATE NEW OR USE EXISTING)
# ==============================================================================

resource "aws_vpc" "ad" {
  count = var.create_vpc ? 1 : 0

  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ad-vpc"
  })
}

resource "aws_internet_gateway" "ad" {
  count = var.create_vpc ? 1 : 0

  vpc_id = aws_vpc.ad[0].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ad-igw"
  })
}

resource "aws_subnet" "ad_public" {
  count = var.create_vpc ? 1 : 0

  vpc_id                  = aws_vpc.ad[0].id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ad-public-subnet"
    Type = "public"
  })
}

resource "aws_route_table" "ad_public" {
  count = var.create_vpc ? 1 : 0

  vpc_id = aws_vpc.ad[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.ad[0].id
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ad-public-rt"
  })
}

resource "aws_route_table_association" "ad_public" {
  count = var.create_vpc ? 1 : 0

  subnet_id      = aws_subnet.ad_public[0].id
  route_table_id = aws_route_table.ad_public[0].id
}

locals {
  vpc_id    = var.create_vpc ? aws_vpc.ad[0].id : var.existing_vpc_id
  subnet_id = var.create_vpc ? aws_subnet.ad_public[0].id : var.existing_subnet_id
}

# ==============================================================================
# SECURITY GROUP
# ==============================================================================

resource "aws_security_group" "ad" {
  name        = "${local.name_prefix}-ad-sg"
  description = "Security group for AD Domain Controller"
  vpc_id      = local.vpc_id

  # RDP Access (optional)
  dynamic "ingress" {
    for_each = var.enable_rdp ? [1] : []
    content {
      description = "RDP"
      from_port   = 3389
      to_port     = 3389
      protocol    = "tcp"
      cidr_blocks = var.rdp_allowed_cidrs
    }
  }

  # DNS
  ingress {
    description = "DNS TCP"
    from_port   = 53
    to_port     = 53
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  ingress {
    description = "DNS UDP"
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Kerberos
  ingress {
    description = "Kerberos TCP"
    from_port   = 88
    to_port     = 88
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  ingress {
    description = "Kerberos UDP"
    from_port   = 88
    to_port     = 88
    protocol    = "udp"
    cidr_blocks = [var.vpc_cidr]
  }

  # LDAP
  ingress {
    description = "LDAP TCP"
    from_port   = 389
    to_port     = 389
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  ingress {
    description = "LDAP UDP"
    from_port   = 389
    to_port     = 389
    protocol    = "udp"
    cidr_blocks = [var.vpc_cidr]
  }

  # LDAPS
  ingress {
    description = "LDAPS"
    from_port   = 636
    to_port     = 636
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # SMB/CIFS
  ingress {
    description = "SMB"
    from_port   = 445
    to_port     = 445
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Global Catalog
  ingress {
    description = "Global Catalog"
    from_port   = 3268
    to_port     = 3269
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # RPC
  ingress {
    description = "RPC"
    from_port   = 135
    to_port     = 135
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # RPC Dynamic Ports
  ingress {
    description = "RPC Dynamic"
    from_port   = 49152
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # NTP
  ingress {
    description = "NTP"
    from_port   = 123
    to_port     = 123
    protocol    = "udp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Outbound
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ad-sg"
  })
}

# ==============================================================================
# WINDOWS AMI LOOKUP
# ==============================================================================

data "aws_ami" "windows_2022" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["Windows_Server-2022-English-Full-Base-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ==============================================================================
# EC2 INSTANCE - DOMAIN CONTROLLER
# ==============================================================================

resource "aws_instance" "ad_dc" {
  ami                    = data.aws_ami.windows_2022.id
  instance_type          = var.instance_type
  subnet_id              = local.subnet_id
  vpc_security_group_ids = [aws_security_group.ad.id]
  iam_instance_profile   = aws_iam_instance_profile.ad_instance.name
  key_name               = var.key_pair_name

  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  user_data = base64encode(templatefile("${path.module}/scripts/bootstrap.ps1", {
    secret_arn         = aws_secretsmanager_secret.ad_credentials.arn
    aws_region         = var.aws_region
    scripts_bucket     = var.scripts_bucket_name
    setup_script_key   = var.setup_script_s3_key
    domain_name        = var.ad_domain_name
    netbios_name       = var.ad_netbios_name
    create_sample_data = var.create_sample_users
  }))

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # IMDSv2 required
    http_put_response_hop_limit = 1
  }

  tags = merge(local.common_tags, {
    Name     = "${local.name_prefix}-ad-dc"
    Role     = "DomainController"
    OS       = "Windows Server 2022"
  })

  lifecycle {
    ignore_changes = [ami, user_data]
  }
}

# ==============================================================================
# ELASTIC IP (OPTIONAL)
# ==============================================================================

resource "aws_eip" "ad_dc" {
  count = var.assign_elastic_ip ? 1 : 0

  instance = aws_instance.ad_dc.id
  domain   = "vpc"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ad-dc-eip"
  })
}

# ==============================================================================
# SSM PARAMETER STORE - INSTANCE INFO
# ==============================================================================

resource "aws_ssm_parameter" "ad_instance_id" {
  name        = "/${var.environment}/${var.region_short}/ad/instance-id"
  description = "AD Domain Controller Instance ID for ${var.region_short}"
  type        = "String"
  value       = aws_instance.ad_dc.id

  tags = local.common_tags
}

resource "aws_ssm_parameter" "ad_private_ip" {
  name        = "/${var.environment}/${var.region_short}/ad/private-ip"
  description = "AD Domain Controller Private IP for ${var.region_short}"
  type        = "String"
  value       = aws_instance.ad_dc.private_ip

  tags = local.common_tags
}
