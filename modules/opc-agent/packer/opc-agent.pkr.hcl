# =============================================================================
# OPC Agent AMI - Packer Template
# =============================================================================
# Builds a pre-configured RHEL 8 AMI with:
# - SSM Agent
# - Java 11 OpenJDK
# - Okta PAM sftd (scaleft-server-tools)
# - Common utilities
# - Directory structure for OPC installation
#
# At deployment time, user_data only needs to:
# - Write connector-specific config files
# - Download JDBC driver (if needed)
# - Configure sftd enrollment token
# - Start sftd service
# =============================================================================

packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "aws_region" {
  type        = string
  default     = "us-east-2"
  description = "AWS region to build the AMI in"
}

variable "instance_type" {
  type        = string
  default     = "t3.small"
  description = "Instance type for building the AMI"
}

variable "ami_name_prefix" {
  type        = string
  default     = "opc-agent-rhel8"
  description = "Prefix for the AMI name"
}

variable "vpc_id" {
  type        = string
  default     = ""
  description = "VPC ID to build in (leave empty for default VPC)"
}

variable "subnet_id" {
  type        = string
  default     = ""
  description = "Subnet ID to build in (leave empty for default)"
}

variable "tags" {
  type = map(string)
  default = {
    Environment = "shared"
    ManagedBy   = "packer"
    Purpose     = "opc-agent-base"
  }
}

# =============================================================================
# DATA SOURCES
# =============================================================================

data "amazon-ami" "rhel8" {
  filters = {
    name                = "RHEL-8*_HVM-*-x86_64-*-Hourly*-GP*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = ["309956199498"] # Red Hat official
  region      = var.aws_region
}

# =============================================================================
# SOURCE - EC2 INSTANCE
# =============================================================================

source "amazon-ebs" "opc-agent" {
  ami_name        = "${var.ami_name_prefix}-{{timestamp}}"
  ami_description = "OPC Agent base image with SSM, Java 11, sftd pre-installed"
  instance_type   = var.instance_type
  region          = var.aws_region
  source_ami      = data.amazon-ami.rhel8.id

  # Network configuration
  vpc_id                      = var.vpc_id != "" ? var.vpc_id : null
  subnet_id                   = var.subnet_id != "" ? var.subnet_id : null
  associate_public_ip_address = true

  # SSH configuration
  ssh_username         = "ec2-user"
  ssh_timeout          = "10m"
  ssh_interface        = "public_ip"
  communicator         = "ssh"

  # Build instance configuration
  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
    encrypted             = true
  }

  # AMI configuration
  tags = merge(var.tags, {
    Name        = "${var.ami_name_prefix}-{{timestamp}}"
    BaseAMI     = data.amazon-ami.rhel8.id
    BuildDate   = "{{timestamp}}"
  })

  run_tags = {
    Name = "packer-opc-agent-builder"
  }
}

# =============================================================================
# BUILD
# =============================================================================

build {
  name    = "opc-agent"
  sources = ["source.amazon-ebs.opc-agent"]

  # =============================================================================
  # PROVISIONER: Install packages and configure system
  # =============================================================================
  provisioner "shell" {
    inline = [
      "echo '=== OPC Agent AMI Build - Starting ==='",
      "echo 'Build timestamp: '$(date -u +%Y-%m-%dT%H:%M:%SZ)",
      "",
      "# Wait for cloud-init to complete",
      "cloud-init status --wait || true",
      "",
      "# Install SSM Agent",
      "echo '>>> Installing SSM Agent...'",
      "sudo dnf install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm || true",
      "sudo systemctl enable amazon-ssm-agent",
      "",
      "# System updates",
      "echo '>>> Installing system updates...'",
      "sudo dnf update -y",
      "",
      "# Install essential packages",
      "echo '>>> Installing essential packages...'",
      "sudo dnf install -y java-11-openjdk java-11-openjdk-devel wget curl unzip nc jq",
      "",
      "# Configure Java",
      "echo '>>> Configuring Java...'",
      "export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))",
      "echo \"export JAVA_HOME=$JAVA_HOME\" | sudo tee /etc/profile.d/java.sh",
      "echo 'export PATH=$JAVA_HOME/bin:$PATH' | sudo tee -a /etc/profile.d/java.sh",
      "sudo chmod 644 /etc/profile.d/java.sh",
      "",
      "# Create directories",
      "echo '>>> Creating directories...'",
      "sudo mkdir -p /installers/jdbc /installers/opc /opt/okta",
      "sudo chmod 755 /installers /opt/okta",
      "",
      "# Install Okta PAM sftd",
      "echo '>>> Installing Okta PAM sftd...'",
      "sudo rpm --import https://dist.scaleft.com/GPG-KEY-OktaPAM-2023",
      "cat << 'REPO' | sudo tee /etc/yum.repos.d/oktapam-stable.repo",
      "[oktapam-stable]",
      "name=Okta PAM Stable - RHEL 8",
      "baseurl=https://dist.scaleft.com/repos/rpm/stable/rhel/8/$basearch",
      "gpgcheck=1",
      "repo_gpgcheck=1",
      "enabled=1",
      "gpgkey=https://dist.scaleft.com/GPG-KEY-OktaPAM-2023",
      "REPO",
      "sudo dnf makecache -y",
      "sudo dnf install -y scaleft-server-tools",
      "",
      "# Verify sftd installation",
      "echo '>>> Verifying sftd installation...'",
      "rpm -q scaleft-server-tools",
      "sftd --version || true",
      "",
      "# Create enrollment helper script",
      "echo '>>> Creating enrollment helper script...'",
      "cat << 'SCRIPT' | sudo tee /usr/local/bin/opc-enroll.sh",
      "#!/bin/bash",
      "# OPC Agent OPA Enrollment Script",
      "# Usage: opc-enroll.sh <enrollment-token>",
      "",
      "if [ -z \"$1\" ]; then",
      "  echo 'Usage: opc-enroll.sh <enrollment-token>'",
      "  echo 'Get token from Terraform output or SSM Parameter Store'",
      "  exit 1",
      "fi",
      "",
      "TOKEN=\"$1\"",
      "sudo mkdir -p /var/lib/sftd",
      "echo \"$TOKEN\" | sudo tee /var/lib/sftd/enrollment.token",
      "sudo chmod 600 /var/lib/sftd/enrollment.token",
      "sudo systemctl enable sftd",
      "sudo systemctl start sftd",
      "",
      "echo 'Waiting for enrollment...'",
      "sleep 5",
      "sudo sftd --check-registered && echo 'Enrollment successful!' || echo 'Enrollment pending - check OPA console'",
      "SCRIPT",
      "sudo chmod 755 /usr/local/bin/opc-enroll.sh",
      "",
      "# Create AMI info file",
      "echo '>>> Creating AMI info file...'",
      "cat << 'INFO' | sudo tee /etc/opc-agent-ami.info",
      "OPC Agent Base AMI",
      "==================",
      "Build Date: {{timestamp}}",
      "",
      "Pre-installed software:",
      "- SSM Agent",
      "- Java 11 OpenJDK",
      "- Okta PAM sftd (scaleft-server-tools)",
      "- curl, wget, nc, jq, unzip",
      "",
      "Directory structure:",
      "- /installers/jdbc   - JDBC drivers",
      "- /installers/opc    - OPC installer files",
      "- /opt/okta          - Okta software",
      "",
      "To enroll with OPA:",
      "  opc-enroll.sh <enrollment-token>",
      "",
      "Or manually:",
      "  echo '<token>' | sudo tee /var/lib/sftd/enrollment.token",
      "  sudo chmod 600 /var/lib/sftd/enrollment.token",
      "  sudo systemctl enable --now sftd",
      "INFO",
      "",
      "# Clean up",
      "echo '>>> Cleaning up...'",
      "sudo dnf clean all",
      "sudo rm -rf /var/cache/dnf/*",
      "sudo rm -rf /tmp/*",
      "",
      "echo '=== OPC Agent AMI Build - Complete ==='"
    ]
  }

  # =============================================================================
  # POST-PROCESSORS
  # =============================================================================
  post-processor "manifest" {
    output     = "manifest.json"
    strip_path = true
  }
}
