# Generic Database Connector

Deploy a PostgreSQL database on AWS RDS for use with Okta's Generic Database Connector. This enables user provisioning, deprovisioning, entitlement management, and JML (Joiner/Mover/Leaver) lifecycle automation.

## Architecture

```
Okta Tenant ←→ OPC Agent (EC2) ←→ PostgreSQL RDS
                    ↑
              SCIM Server (optional, for write-back)
```

- **PostgreSQL RDS**: Stores users, entitlements, groups, and audit logs
- **OPC Agent**: On-prem connector that bridges Okta to the database (see [OPC Agents](opc-agents.md))
- **SCIM Server**: Optional, enables write-back from Okta to the database

## Quick Start

### 1. Deploy the Database

```bash
cd environments/myorg/generic-db-infrastructure
cp main.tf.example main.tf
# Edit main.tf: set backend bucket, environment name, region
terraform init && terraform apply
```

### 2. Initialize the Schema

```bash
gh workflow run generic-db-schema-init.yml \
  -f environment=myorg-prod \
  -f action=initialize
```

### 3. Deploy OPC Agents

See [OPC Agents](opc-agents.md) for deploying the on-prem connector.

### 4. Configure in Okta

1. Go to Okta Admin > Directory > Directory Integrations
2. Add Generic Database Connector
3. Configure JDBC connection using the output from `terraform output connection_info`
4. Set up attribute mappings (see SQL Queries section below)

## Terraform Module

The `modules/generic-db-connector/` module creates:

- VPC with two subnets (or uses existing VPC)
- Security group for PostgreSQL (port 5432)
- RDS PostgreSQL instance with encrypted storage
- Secrets Manager secret with connection credentials
- SSM parameters for endpoint and JDBC URL
- DB parameter group with query logging enabled

### Module Inputs

| Variable | Description | Default |
|----------|-------------|---------|
| `name_prefix` | Prefix for resource names | (required) |
| `environment` | Environment name for tags/SSM | (required) |
| `use_existing_vpc` | Use existing VPC | `false` |
| `existing_vpc_id` | VPC ID if using existing | `""` |
| `existing_subnet_ids` | Subnet IDs if using existing | `[]` |
| `db_name` | Database name | `okta_connector` |
| `db_username` | Admin username | `oktaadmin` |
| `postgres_version` | PostgreSQL version | `15.10` |
| `instance_class` | RDS instance type | `db.t3.micro` |
| `publicly_accessible` | Public access | `true` |
| `db_allowed_cidrs` | Allowed CIDRs | `["0.0.0.0/0"]` |

### Module Outputs

| Output | Description |
|--------|-------------|
| `db_endpoint` | RDS endpoint hostname |
| `jdbc_url` | Complete JDBC URL |
| `credentials_secret_name` | Secrets Manager secret name |
| `security_group_id` | Security group ID (for OPC agents) |
| `vpc_id` | VPC ID |
| `subnet_ids` | Subnet IDs |
| `connection_info` | Full connection details map |

## Database Schema

The schema (`modules/generic-db-connector/scripts/schema.sql`) creates:

### Tables

| Table | Purpose |
|-------|---------|
| `users` | Core user records (maps to Okta user profile) |
| `entitlements` | Available roles/permissions |
| `user_entitlements` | User-to-entitlement assignments |
| `groups` | Optional group management |
| `user_groups` | User-to-group assignments |
| `audit_log` | All provisioning operations |

### Stored Procedures

| Procedure | Purpose |
|-----------|---------|
| `create_user()` | Create new user with audit trail |
| `update_user()` | Update user attributes |
| `deactivate_user()` | Deactivate user and revoke entitlements |
| `assign_entitlement()` | Grant entitlement to user |
| `revoke_entitlement()` | Revoke entitlement from user |

### Views

| View | Purpose |
|------|---------|
| `v_users_with_entitlements` | Users with entitlement counts and names |
| `v_active_entitlements` | Active entitlements with assigned user counts |

## SQL Queries for OPC Configuration

### User Import Query
```sql
SELECT user_id AS "id", username AS "userName", email,
       first_name AS "givenName", last_name AS "familyName",
       display_name AS "displayName", department, title, status
FROM users WHERE status = 'ACTIVE'
```

### Entitlement Import Query
```sql
SELECT entitlement_id AS "id", name AS "displayName",
       description, category
FROM entitlements WHERE status = 'ACTIVE'
```

### User Entitlement Query
```sql
SELECT user_id, entitlement_id
FROM user_entitlements WHERE status = 'ACTIVE'
```

### OPC Connector Settings

| Setting | Value |
|---------|-------|
| **User ID Column** | `id` (aliased from `user_id`) |
| **JDBC Driver** | `org.postgresql.Driver` |
| **Create User** | `PROCEDURE` type, call `create_user` |
| **Update User** | `PROCEDURE` type, call `update_user` |
| **Deactivate User** | `PROCEDURE` type, call `deactivate_user` |

**Important**: Use `PROCEDURE` (not `FUNCTION`) for executeUpdate operations. Okta's connector uses `CALL` for procedures and `SELECT` for functions.

## JML Lifecycle Workflows

### Joiner (Create User)
```bash
gh workflow run generic-db-create-user.yml \
  -f environment=myorg-prod \
  -f user_id=usr-006 \
  -f username=nwilliams \
  -f email=nwilliams@example.com \
  -f first_name=Nancy \
  -f last_name=Williams \
  -f department=Engineering
```

### Mover (Update User)
```bash
gh workflow run generic-db-update-user.yml \
  -f environment=myorg-prod \
  -f user_id=usr-006 \
  -f attribute=department \
  -f new_value=Marketing
```

### Leaver (Deactivate User)
```bash
gh workflow run generic-db-deactivate-user.yml \
  -f environment=myorg-prod \
  -f user_id=usr-006 \
  -f confirm=yes
```

## SCIM Attribute Mapping

When configuring the SCIM connector for write-back, use the `ext_` prefix for custom attributes:

| SCIM Attribute | Database Column | Direction |
|----------------|-----------------|-----------|
| `userName` | `username` | Import + Write-back |
| `givenName` | `first_name` | Import + Write-back |
| `familyName` | `last_name` | Import + Write-back |
| `email` | `email` | Import + Write-back |
| `ext_department` | `department` | Import + Write-back |
| `ext_title` | `title` | Import + Write-back |
| `ext_write_back` | `write_back` | Write-back only |

**Write-back direction**: Set to "To App" only in the Okta app attribute mapping. This allows Okta to push attribute changes back to the database.

## Cost Estimate

- **RDS db.t3.micro**: ~$15/month (free tier eligible for 12 months)
- **OPC Agent t3.medium**: ~$30/month per agent
- **Elastic IP**: Free while attached to running instance
- **Secrets Manager**: ~$0.40/month per secret

Total for a demo setup (1 RDS + 1 OPC): ~$45/month. Stop instances when not in use to save costs.
