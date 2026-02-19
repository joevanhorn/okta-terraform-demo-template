# ==============================================================================
# GENERIC DATABASE CONNECTOR MODULE
# ==============================================================================
# Deploys PostgreSQL RDS for use with Okta Generic Database Connector.
# Supports user provisioning, deprovisioning, and entitlement management.
#
# Usage:
#   module "generic_db" {
#     source       = "../../modules/generic-db-connector"
#     name_prefix  = "myorg-prod-use2"
#     environment  = "myorg-prod"
#   }
# ==============================================================================

terraform {
  required_version = ">= 1.9.0"

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
# DATA SOURCES
# ==============================================================================

data "aws_availability_zones" "available" {
  state = "available"
}

# ==============================================================================
# LOCAL VALUES
# ==============================================================================

locals {
  common_tags = merge(var.tags, {
    Environment = var.environment
    Project     = "generic-db-connector"
    ManagedBy   = "terraform"
  })
}

# ==============================================================================
# VPC (if not using existing)
# ==============================================================================

resource "aws_vpc" "generic_db" {
  count = var.use_existing_vpc ? 0 : 1

  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-generic-db-vpc"
  })
}

resource "aws_internet_gateway" "generic_db" {
  count  = var.use_existing_vpc ? 0 : 1
  vpc_id = aws_vpc.generic_db[0].id

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-generic-db-igw"
  })
}

resource "aws_subnet" "generic_db_a" {
  count = var.use_existing_vpc ? 0 : 1

  vpc_id            = aws_vpc.generic_db[0].id
  cidr_block        = var.subnet_a_cidr
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-generic-db-subnet-a"
  })
}

resource "aws_subnet" "generic_db_b" {
  count = var.use_existing_vpc ? 0 : 1

  vpc_id            = aws_vpc.generic_db[0].id
  cidr_block        = var.subnet_b_cidr
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-generic-db-subnet-b"
  })
}

resource "aws_route_table" "generic_db" {
  count  = var.use_existing_vpc ? 0 : 1
  vpc_id = aws_vpc.generic_db[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.generic_db[0].id
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-generic-db-rt"
  })
}

resource "aws_route_table_association" "generic_db_a" {
  count          = var.use_existing_vpc ? 0 : 1
  subnet_id      = aws_subnet.generic_db_a[0].id
  route_table_id = aws_route_table.generic_db[0].id
}

resource "aws_route_table_association" "generic_db_b" {
  count          = var.use_existing_vpc ? 0 : 1
  subnet_id      = aws_subnet.generic_db_b[0].id
  route_table_id = aws_route_table.generic_db[0].id
}

# ==============================================================================
# SECURITY GROUP
# ==============================================================================

resource "aws_security_group" "postgres" {
  name        = "${var.name_prefix}-generic-db-postgres-sg"
  description = "Security group for PostgreSQL RDS (Generic DB Connector)"
  vpc_id      = var.use_existing_vpc ? var.existing_vpc_id : aws_vpc.generic_db[0].id

  ingress {
    description = "PostgreSQL"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = var.db_allowed_cidrs
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-generic-db-postgres-sg"
  })
}

# ==============================================================================
# DB SUBNET GROUP
# ==============================================================================

resource "aws_db_subnet_group" "postgres" {
  name        = "${var.name_prefix}-generic-db-subnet-group"
  description = "Subnet group for PostgreSQL RDS"
  subnet_ids = var.use_existing_vpc ? var.existing_subnet_ids : [
    aws_subnet.generic_db_a[0].id,
    aws_subnet.generic_db_b[0].id
  ]

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-generic-db-subnet-group"
  })
}

# ==============================================================================
# RANDOM PASSWORD
# ==============================================================================

resource "random_password" "postgres_admin" {
  length           = 20
  special          = true
  override_special = "!#$%^&*"
  min_lower        = 2
  min_upper        = 2
  min_numeric      = 2
  min_special      = 1
}

# ==============================================================================
# SECRETS MANAGER
# ==============================================================================

resource "aws_secretsmanager_secret" "postgres_credentials" {
  name        = "${var.name_prefix}-generic-db-credentials"
  description = "PostgreSQL credentials for Generic Database Connector"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "postgres_credentials" {
  secret_id = aws_secretsmanager_secret.postgres_credentials.id
  secret_string = jsonencode({
    host     = aws_db_instance.postgres.address
    port     = aws_db_instance.postgres.port
    database = var.db_name
    username = var.db_username
    password = random_password.postgres_admin.result
    jdbc_url = "jdbc:postgresql://${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${var.db_name}"
  })
}

# ==============================================================================
# RDS POSTGRESQL INSTANCE
# ==============================================================================

resource "aws_db_instance" "postgres" {
  identifier = "${var.name_prefix}-generic-db"

  engine               = "postgres"
  engine_version       = var.postgres_version
  instance_class       = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.postgres_admin.result

  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.postgres.id]
  publicly_accessible    = var.publicly_accessible
  port                   = 5432

  backup_retention_period = var.backup_retention_days
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  multi_az            = false
  skip_final_snapshot = true
  deletion_protection = false

  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  parameter_group_name = aws_db_parameter_group.postgres.name

  tags = merge(local.common_tags, {
    Name = "${var.name_prefix}-generic-db"
  })
}

resource "aws_db_parameter_group" "postgres" {
  name   = "${var.name_prefix}-generic-db-params"
  family = "postgres${split(".", var.postgres_version)[0]}"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "0"
  }

  tags = local.common_tags
}

# ==============================================================================
# SSM PARAMETERS (for easy reference)
# ==============================================================================

resource "aws_ssm_parameter" "db_endpoint" {
  name        = "/${var.environment}/generic-db/endpoint"
  description = "PostgreSQL endpoint for Generic DB Connector"
  type        = "String"
  value       = aws_db_instance.postgres.address

  tags = local.common_tags
}

resource "aws_ssm_parameter" "db_jdbc_url" {
  name        = "/${var.environment}/generic-db/jdbc-url"
  description = "JDBC URL for Generic DB Connector"
  type        = "String"
  value       = "jdbc:postgresql://${aws_db_instance.postgres.address}:5432/${var.db_name}"

  tags = local.common_tags
}
