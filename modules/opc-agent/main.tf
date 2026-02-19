# ==============================================================================
# OPC AGENT MODULE
# ==============================================================================
# Deploys Okta On-Prem Connector (OPC) agents for various connector types:
# - Generic Database (PostgreSQL, MySQL, etc.)
# - Oracle EBS
# - SAP
#
# Supports multiple instances for high availability.
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

locals {
  name_prefix = "${var.environment}-${var.region_short}"
  agent_name  = "${local.name_prefix}-opc-${var.connector_type}-${var.instance_number}"

  # Connector-specific database ports
  db_ports = {
    "generic-db"  = 5432  # PostgreSQL
    "oracle-ebs"  = 1521  # Oracle
    "sap"         = 3306  # SAP HANA / MySQL
  }

  common_tags = merge(var.tags, {
    Environment    = var.environment
    ManagedBy      = "terraform"
    Module         = "opc-agent"
    ConnectorType  = var.connector_type
    InstanceNumber = tostring(var.instance_number)
    Role           = "OPC-Agent"
  })
}

# ==============================================================================
# RHEL 8 AMI
# ==============================================================================

data "aws_ami" "rhel8" {
  most_recent = true
  owners      = ["309956199498"]  # Red Hat official

  filter {
    name   = "name"
    values = ["RHEL-8*_HVM-*-x86_64-*-Hourly*-GP*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# ==============================================================================
# IAM ROLE
# ==============================================================================

resource "aws_iam_role" "opc_agent" {
  name = "${local.agent_name}-role"

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

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.opc_agent.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "cloudwatch" {
  role       = aws_iam_role.opc_agent.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_instance_profile" "opc_agent" {
  name = "${local.agent_name}-profile"
  role = aws_iam_role.opc_agent.name
  tags = local.common_tags
}

# ==============================================================================
# EC2 INSTANCE
# ==============================================================================

resource "aws_instance" "opc_agent" {
  ami                    = var.custom_ami_id != "" ? var.custom_ami_id : data.aws_ami.rhel8.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = var.security_group_ids
  iam_instance_profile   = aws_iam_instance_profile.opc_agent.name
  key_name               = var.key_pair_name != "" ? var.key_pair_name : null

  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true

    tags = merge(local.common_tags, {
      Name = "${local.agent_name}-root"
    })
  }

  user_data = base64encode(templatefile(
    var.use_prebuilt_ami ? "${path.module}/scripts/bootstrap-from-ami.sh" : "${path.module}/scripts/bootstrap.sh",
    {
      okta_org_url         = var.okta_org_url
      connector_type       = var.connector_type
      instance_number      = var.instance_number
      database_host        = var.database_host
      database_port        = lookup(local.db_ports, var.connector_type, 5432)
      jdbc_driver_url      = var.jdbc_driver_url
      agent_name           = local.agent_name
      opa_enrollment_token = var.opa_enrollment_token
    }
  ))

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # IMDSv2
    http_put_response_hop_limit = 1
  }

  tags = merge(local.common_tags, {
    Name = local.agent_name
    OS   = "RHEL8"
  })

  # ==============================================================================
  # LIFECYCLE PROTECTION
  # ==============================================================================
  # NOTE: Temporarily disabled for redeployment testing
  # Re-enable prevent_destroy after deployment is verified
  lifecycle {
    # prevent_destroy = true  # DISABLED FOR REDEPLOY

    # Ignore changes that would trigger recreation
    ignore_changes = [
      ami,        # Don't recreate on new AMI versions
      # user_data,  # DISABLED - allow recreation on bootstrap changes
    ]
  }
}

# ==============================================================================
# SSM PARAMETER STORE - FOR DISCOVERY
# ==============================================================================

# ==============================================================================
# ELASTIC IP - REQUIRED FOR INTERNET ACCESS
# ==============================================================================

resource "aws_eip" "opc_agent" {
  domain = "vpc"

  tags = merge(local.common_tags, {
    Name = "${local.agent_name}-eip"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_eip_association" "opc_agent" {
  instance_id   = aws_instance.opc_agent.id
  allocation_id = aws_eip.opc_agent.id
}

# ==============================================================================
# SSM PARAMETER STORE - FOR DISCOVERY
# ==============================================================================

resource "aws_ssm_parameter" "instance_id" {
  name        = "/${var.environment}/${var.region_short}/opc/${var.connector_type}/${var.instance_number}/instance-id"
  description = "OPC Agent Instance ID - ${local.agent_name}"
  type        = "String"
  value       = aws_instance.opc_agent.id

  tags = local.common_tags
}

resource "aws_ssm_parameter" "private_ip" {
  name        = "/${var.environment}/${var.region_short}/opc/${var.connector_type}/${var.instance_number}/private-ip"
  description = "OPC Agent Private IP - ${local.agent_name}"
  type        = "String"
  value       = aws_instance.opc_agent.private_ip

  tags = local.common_tags
}
