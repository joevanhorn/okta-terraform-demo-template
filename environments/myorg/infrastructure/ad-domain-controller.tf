# ==============================================================================
# Data Source - Latest Windows Server 2022 AMI
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

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

# ==============================================================================
# EC2 Instance - Domain Controller
# ==============================================================================

resource "aws_instance" "domain_controller" {
  ami           = data.aws_ami.windows_2022.id
  instance_type = var.dc_instance_type
  key_name      = var.key_pair_name

  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.domain_controller.id]
  associate_public_ip_address = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.dc_volume_size
    delete_on_termination = true
    encrypted             = true

    tags = merge(
      {
        Name = "${var.environment_name}-ad-dc-root"
      },
      var.additional_tags
    )
  }

  # User data script for Windows initialization
  user_data = templatefile("${path.module}/scripts/userdata.ps1", {
    admin_password         = var.admin_password
    ad_domain_name         = var.ad_domain_name
    ad_netbios_name        = var.ad_netbios_name
    ad_safe_mode_password  = var.ad_safe_mode_password
    okta_org_url           = var.okta_org_url
    okta_opa_enabled       = var.okta_opa_enabled
    environment_name       = var.environment_name
  })

  # Enable metadata service v2 (IMDSv2)
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  tags = merge(
    {
      Name = "${var.environment_name}-ad-dc"
      Role = "Domain-Controller"
    },
    var.additional_tags
  )

  lifecycle {
    ignore_changes = [
      ami, # Don't replace instance when newer AMI becomes available
      user_data # Don't replace instance when user_data changes
    ]
  }
}

# ==============================================================================
# Elastic IP for stable public address
# ==============================================================================

resource "aws_eip" "dc" {
  instance = aws_instance.domain_controller.id
  domain   = "vpc"

  tags = merge(
    {
      Name = "${var.environment_name}-ad-dc-eip"
    },
    var.additional_tags
  )

  depends_on = [aws_internet_gateway.main]
}
