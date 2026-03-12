# Okta Access Gateway Infrastructure
# Deploys OAG virtual appliance on AWS EC2 with ALB and Let's Encrypt certificates

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # Backend configuration - update for your environment
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "oag/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-state-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "okta-access-gateway"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC for OAG
resource "aws_vpc" "oag" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.name_prefix}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "oag" {
  vpc_id = aws_vpc.oag.id

  tags = {
    Name = "${var.name_prefix}-igw"
  }
}

# Public subnets for ALB
resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.oag.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.name_prefix}-public-${count.index + 1}"
    Type = "public"
  }
}

# Private subnets for OAG and backend apps
resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.oag.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.name_prefix}-private-${count.index + 1}"
    Type = "private"
  }
}

# NAT Gateway for private subnets
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "${var.name_prefix}-nat-eip"
  }
}

resource "aws_nat_gateway" "oag" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "${var.name_prefix}-nat"
  }

  depends_on = [aws_internet_gateway.oag]
}

# Route tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.oag.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.oag.id
  }

  tags = {
    Name = "${var.name_prefix}-public-rt"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.oag.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.oag.id
  }

  tags = {
    Name = "${var.name_prefix}-private-rt"
  }
}

resource "aws_route_table_association" "public" {
  count = 2

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = 2

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Security group for ALB
resource "aws_security_group" "alb" {
  name_prefix = "${var.name_prefix}-alb-"
  vpc_id      = aws_vpc.oag.id
  description = "Security group for OAG ALB"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from anywhere"
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP for redirect"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name = "${var.name_prefix}-alb-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security group for OAG instance
resource "aws_security_group" "oag" {
  name_prefix = "${var.name_prefix}-oag-"
  vpc_id      = aws_vpc.oag.id
  description = "Security group for OAG instance"

  # HTTPS from ALB
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "HTTPS from ALB"
  }

  # Admin console (restrict in production)
  ingress {
    from_port   = 8443
    to_port     = 8443
    protocol    = "tcp"
    cidr_blocks = var.admin_cidr_blocks
    description = "Admin console access"
  }

  # SSH for management (restrict in production)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.admin_cidr_blocks
    description = "SSH access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name = "${var.name_prefix}-oag-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ACM Certificate with DNS validation
resource "aws_acm_certificate" "oag" {
  domain_name               = var.oag_domain
  subject_alternative_names = var.oag_san_domains
  validation_method         = "DNS"

  tags = {
    Name = "${var.name_prefix}-cert"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Route53 DNS validation records (if using Route53)
resource "aws_route53_record" "cert_validation" {
  for_each = var.route53_zone_id != "" ? {
    for dvo in aws_acm_certificate.oag.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.route53_zone_id
}

resource "aws_acm_certificate_validation" "oag" {
  count = var.route53_zone_id != "" ? 1 : 0

  certificate_arn         = aws_acm_certificate.oag.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# Application Load Balancer
resource "aws_lb" "oag" {
  name               = "${var.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = var.enable_deletion_protection

  tags = {
    Name = "${var.name_prefix}-alb"
  }
}

# ALB Target Group
resource "aws_lb_target_group" "oag" {
  name     = "${var.name_prefix}-tg"
  port     = 443
  protocol = "HTTPS"
  vpc_id   = aws_vpc.oag.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTPS"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "${var.name_prefix}-tg"
  }
}

# HTTPS Listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.oag.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.route53_zone_id != "" ? aws_acm_certificate_validation.oag[0].certificate_arn : aws_acm_certificate.oag.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.oag.arn
  }
}

# HTTP to HTTPS redirect
resource "aws_lb_listener" "http_redirect" {
  load_balancer_arn = aws_lb.oag.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# Route53 record for OAG
resource "aws_route53_record" "oag" {
  count = var.route53_zone_id != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = var.oag_domain
  type    = "A"

  alias {
    name                   = aws_lb.oag.dns_name
    zone_id                = aws_lb.oag.zone_id
    evaluate_target_health = true
  }
}

# IAM role for OAG EC2 instance
resource "aws_iam_role" "oag" {
  name = "${var.name_prefix}-ec2-role"

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

  tags = {
    Name = "${var.name_prefix}-ec2-role"
  }
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.oag.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "oag" {
  name = "${var.name_prefix}-instance-profile"
  role = aws_iam_role.oag.name
}

# OAG EC2 Instance
# Note: You need to import the OAG OVA to create an AMI first
resource "aws_instance" "oag" {
  ami                    = var.oag_ami_id
  instance_type          = var.oag_instance_type
  subnet_id              = aws_subnet.private[0].id
  vpc_security_group_ids = [aws_security_group.oag.id]
  iam_instance_profile   = aws_iam_instance_profile.oag.name
  key_name               = var.key_pair_name

  root_block_device {
    volume_size           = var.oag_volume_size
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name = "${var.name_prefix}-instance"
  }

  lifecycle {
    ignore_changes = [ami]
  }
}

# Register OAG with target group
resource "aws_lb_target_group_attachment" "oag" {
  target_group_arn = aws_lb_target_group.oag.arn
  target_id        = aws_instance.oag.id
  port             = 443
}
