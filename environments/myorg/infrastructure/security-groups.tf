# ==============================================================================
# Domain Controller Security Group
# ==============================================================================

resource "aws_security_group" "domain_controller" {
  name        = "${var.environment_name}-ad-dc-sg"
  description = "Security group for Active Directory Domain Controller"
  vpc_id      = aws_vpc.main.id

  tags = merge(
    {
      Name = "${var.environment_name}-ad-dc-sg"
    },
    var.additional_tags
  )
}

# ==============================================================================
# Ingress Rules - RDP Access
# ==============================================================================

resource "aws_security_group_rule" "dc_rdp" {
  type              = "ingress"
  from_port         = 3389
  to_port           = 3389
  protocol          = "tcp"
  cidr_blocks       = var.allowed_rdp_cidrs
  description       = "RDP access"
  security_group_id = aws_security_group.domain_controller.id
}

# ==============================================================================
# Ingress Rules - Active Directory Ports
# ==============================================================================

# DNS
resource "aws_security_group_rule" "dc_dns_tcp" {
  type              = "ingress"
  from_port         = 53
  to_port           = 53
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "DNS (TCP)"
  security_group_id = aws_security_group.domain_controller.id
}

resource "aws_security_group_rule" "dc_dns_udp" {
  type              = "ingress"
  from_port         = 53
  to_port           = 53
  protocol          = "udp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "DNS (UDP)"
  security_group_id = aws_security_group.domain_controller.id
}

# Kerberos
resource "aws_security_group_rule" "dc_kerberos_tcp" {
  type              = "ingress"
  from_port         = 88
  to_port           = 88
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "Kerberos (TCP)"
  security_group_id = aws_security_group.domain_controller.id
}

resource "aws_security_group_rule" "dc_kerberos_udp" {
  type              = "ingress"
  from_port         = 88
  to_port           = 88
  protocol          = "udp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "Kerberos (UDP)"
  security_group_id = aws_security_group.domain_controller.id
}

# RPC Endpoint Mapper
resource "aws_security_group_rule" "dc_rpc_mapper" {
  type              = "ingress"
  from_port         = 135
  to_port           = 135
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "RPC Endpoint Mapper"
  security_group_id = aws_security_group.domain_controller.id
}

# NetBIOS
resource "aws_security_group_rule" "dc_netbios_ns" {
  type              = "ingress"
  from_port         = 137
  to_port           = 137
  protocol          = "udp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "NetBIOS Name Service"
  security_group_id = aws_security_group.domain_controller.id
}

resource "aws_security_group_rule" "dc_netbios_dgm" {
  type              = "ingress"
  from_port         = 138
  to_port           = 138
  protocol          = "udp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "NetBIOS Datagram Service"
  security_group_id = aws_security_group.domain_controller.id
}

resource "aws_security_group_rule" "dc_netbios_ssn" {
  type              = "ingress"
  from_port         = 139
  to_port           = 139
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "NetBIOS Session Service"
  security_group_id = aws_security_group.domain_controller.id
}

# LDAP
resource "aws_security_group_rule" "dc_ldap" {
  type              = "ingress"
  from_port         = 389
  to_port           = 389
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "LDAP"
  security_group_id = aws_security_group.domain_controller.id
}

resource "aws_security_group_rule" "dc_ldap_udp" {
  type              = "ingress"
  from_port         = 389
  to_port           = 389
  protocol          = "udp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "LDAP (UDP)"
  security_group_id = aws_security_group.domain_controller.id
}

# SMB
resource "aws_security_group_rule" "dc_smb" {
  type              = "ingress"
  from_port         = 445
  to_port           = 445
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "SMB over TCP"
  security_group_id = aws_security_group.domain_controller.id
}

# Kerberos Password Change
resource "aws_security_group_rule" "dc_kerberos_pwd" {
  type              = "ingress"
  from_port         = 464
  to_port           = 464
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "Kerberos Password Change"
  security_group_id = aws_security_group.domain_controller.id
}

resource "aws_security_group_rule" "dc_kerberos_pwd_udp" {
  type              = "ingress"
  from_port         = 464
  to_port           = 464
  protocol          = "udp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "Kerberos Password Change (UDP)"
  security_group_id = aws_security_group.domain_controller.id
}

# LDAPS
resource "aws_security_group_rule" "dc_ldaps" {
  type              = "ingress"
  from_port         = 636
  to_port           = 636
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "LDAPS (LDAP over SSL)"
  security_group_id = aws_security_group.domain_controller.id
}

# Global Catalog
resource "aws_security_group_rule" "dc_gc" {
  type              = "ingress"
  from_port         = 3268
  to_port           = 3268
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "Global Catalog"
  security_group_id = aws_security_group.domain_controller.id
}

resource "aws_security_group_rule" "dc_gc_ssl" {
  type              = "ingress"
  from_port         = 3269
  to_port           = 3269
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "Global Catalog over SSL"
  security_group_id = aws_security_group.domain_controller.id
}

# Dynamic RPC (for AD replication and other services)
resource "aws_security_group_rule" "dc_dynamic_rpc" {
  type              = "ingress"
  from_port         = 49152
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "Dynamic RPC range"
  security_group_id = aws_security_group.domain_controller.id
}

# WinRM (for remote management)
resource "aws_security_group_rule" "dc_winrm_http" {
  type              = "ingress"
  from_port         = 5985
  to_port           = 5985
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "WinRM HTTP"
  security_group_id = aws_security_group.domain_controller.id
}

resource "aws_security_group_rule" "dc_winrm_https" {
  type              = "ingress"
  from_port         = 5986
  to_port           = 5986
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]
  description       = "WinRM HTTPS"
  security_group_id = aws_security_group.domain_controller.id
}

# ==============================================================================
# Egress Rules - Allow all outbound
# ==============================================================================

resource "aws_security_group_rule" "dc_egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow all outbound traffic"
  security_group_id = aws_security_group.domain_controller.id
}
