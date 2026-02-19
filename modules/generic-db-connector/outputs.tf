# ==============================================================================
# GENERIC DB CONNECTOR MODULE OUTPUTS
# ==============================================================================

output "db_endpoint" {
  description = "PostgreSQL endpoint"
  value       = aws_db_instance.postgres.address
}

output "db_port" {
  description = "PostgreSQL port"
  value       = aws_db_instance.postgres.port
}

output "db_name" {
  description = "Database name"
  value       = var.db_name
}

output "jdbc_url" {
  description = "JDBC URL for Okta Generic DB Connector"
  value       = "jdbc:postgresql://${aws_db_instance.postgres.address}:5432/${var.db_name}"
}

output "credentials_secret_name" {
  description = "Secrets Manager secret name for credentials"
  value       = aws_secretsmanager_secret.postgres_credentials.name
}

output "credentials_secret_arn" {
  description = "Secrets Manager secret ARN for credentials"
  value       = aws_secretsmanager_secret.postgres_credentials.arn
}

output "security_group_id" {
  description = "Security group ID for PostgreSQL"
  value       = aws_security_group.postgres.id
}

output "vpc_id" {
  description = "VPC ID (created or existing)"
  value       = var.use_existing_vpc ? var.existing_vpc_id : aws_vpc.generic_db[0].id
}

output "subnet_ids" {
  description = "Subnet IDs"
  value = var.use_existing_vpc ? var.existing_subnet_ids : [
    aws_subnet.generic_db_a[0].id,
    aws_subnet.generic_db_b[0].id
  ]
}

output "connection_info" {
  description = "Connection information for Okta Generic DB Connector"
  value = {
    host        = aws_db_instance.postgres.address
    port        = aws_db_instance.postgres.port
    database    = var.db_name
    username    = var.db_username
    jdbc_url    = "jdbc:postgresql://${aws_db_instance.postgres.address}:5432/${var.db_name}"
    jdbc_driver = "org.postgresql.Driver"
    secret_name = aws_secretsmanager_secret.postgres_credentials.name
  }
}
