# Repository Structure Context

This document provides context about the Okta Terraform Complete Demo repository structure for AI assistants.

## Directory Layout

```
okta-terraform-complete-demo/
├── environments/
│   ├── myorg/          # Example tenant environment
│   │   ├── terraform/          # Terraform configurations (Okta resources)
│   │   │   ├── provider.tf     # Okta provider configuration
│   │   │   ├── variables.tf    # Variable definitions
│   │   │   ├── QUICKSTART_DEMO.tf.example  # Ready-to-use demo template ⭐
│   │   │   ├── RESOURCE_EXAMPLES.tf        # Comprehensive reference examples
│   │   │   ├── README.md       # Template usage guide
│   │   │   ├── users.tf        # User resources
│   │   │   ├── groups.tf       # Group resources
│   │   │   ├── apps.tf         # Application resources
│   │   │   ├── scim_app.tf     # SCIM application (connects to scim-server) ⭐ NEW!
│   │   │   ├── oig_entitlements.tf  # OIG entitlement bundles
│   │   │   └── oig_reviews.tf  # OIG access reviews
│   │   ├── infrastructure/     # Terraform configurations (AWS infrastructure)
│   │   │   ├── active-directory/  # Active Directory Domain Controller (optional)
│   │   │   │   ├── provider.tf     # AWS provider with S3 backend
│   │   │   │   ├── variables.tf    # Infrastructure variables
│   │   │   │   ├── vpc.tf          # VPC and networking
│   │   │   │   ├── security-groups.tf  # Security groups (AD ports)
│   │   │   │   ├── ad-domain-controller.tf  # EC2 Domain Controller
│   │   │   │   ├── outputs.tf      # Infrastructure outputs
│   │   │   │   ├── scripts/        # PowerShell automation scripts
│   │   │   │   └── terraform.tfvars.example  # Example variables
│   │   │   └── scim-server/    # Custom SCIM 2.0 Server (optional) ⭐ NEW!
│   │   │       ├── provider.tf     # AWS provider with S3 backend
│   │   │       ├── variables.tf    # SCIM server variables
│   │   │       ├── main.tf         # EC2, security groups, Route53
│   │   │       ├── outputs.tf      # SCIM URLs, connection info
│   │   │       ├── user-data.sh    # Server initialization (Caddy + Flask)
│   │   │       ├── demo_scim_server.py  # Flask SCIM 2.0 server
│   │   │       ├── requirements.txt     # Python dependencies
│   │   │       └── README.md       # Deployment guide
│   │   ├── imports/            # Imported JSON data
│   │   └── config/             # Configuration files
│   │       ├── owner_mappings.json    # Resource owners (API-managed)
│   │       ├── label_mappings.json    # Governance labels (API-managed)
│   │       └── risk_rules.json        # Risk rules/SOD policies (API-managed)
│   ├── production/             # Production environment (template)
│   ├── staging/                # Staging environment (template)
│   └── development/            # Development environment (template)
├── scripts/                    # Python automation scripts
│   ├── import_oig_resources.py     # Import OIG resources from Okta
│   ├── sync_owner_mappings.py      # Sync resource owners
│   ├── apply_resource_owners.py    # Apply resource owners
│   ├── sync_label_mappings.py      # Sync governance labels
│   ├── apply_admin_labels.py       # Auto-label admin resources
│   ├── import_risk_rules.py        # Import risk rules (SOD policies)
│   ├── apply_risk_rules.py         # Apply risk rules to Okta
│   └── configure_scim_app.py       # Configure SCIM connection (API-only) ⭐ NEW!
├── docs/                       # Documentation
├── testing/                    # Testing and validation guides
└── .github/workflows/          # GitHub Actions workflows
```

## Key Files to Know

### Provider Configuration
- **File:** `environments/{env}/terraform/provider.tf`
- **Purpose:** Configures the Okta Terraform provider
- **Important:** Uses variables for credentials (never hardcode secrets)

### Variables
- **File:** `environments/{env}/terraform/variables.tf`
- **Purpose:** Defines input variables for Okta connection
- **Variables:**
  - `okta_org_name` - Okta organization name
  - `okta_base_url` - Base URL (okta.com, oktapreview.com, etc.)
  - `okta_api_token` - API token (from terraform.tfvars)

### Template Files (NEW!)
- **File:** `environments/{env}/terraform/QUICKSTART_DEMO.tf.example`
- **Purpose:** Ready-to-use demo with 5 users, 3 groups, 1 OAuth app
- **Usage:** Copy, uncomment, customize, deploy in 2 minutes
- **Perfect for:** Testing, learning, quick demos

- **File:** `environments/{env}/terraform/RESOURCE_EXAMPLES.tf`
- **Purpose:** Comprehensive reference with examples of ALL Okta resources
- **Contains:** Users, Groups, Apps, Policies, OIG, Auth Servers, Hooks
- **Usage:** Browse for examples, copy what you need

- **File:** `environments/{env}/terraform/README.md`
- **Purpose:** Complete guide to using templates, best practices, workflows
- **When to use:** Reference before AI generation, learn Terraform patterns

**💡 Tip:** Before using AI, check if the templates already have what you need! They're faster and proven to work.

### Resource Files
Each resource type has its own file:
- `users.tf` - Okta users
- `groups.tf` - Okta groups
- `group_memberships.tf` - Group member assignments
- `apps.tf` - OAuth applications
- `auth_servers.tf` - Authorization servers
- `policies.tf` - MFA and other policies
- `oig_entitlements.tf` - OIG entitlement bundles
- `oig_reviews.tf` - OIG access review campaigns

### Infrastructure Files (Optional)

**Active Directory** infrastructure files (in `infrastructure/active-directory/` subdirectory):
- `provider.tf` - AWS provider with S3 backend configuration
- `variables.tf` - Infrastructure input variables (passwords, domain names)
- `vpc.tf` - VPC, subnets, internet gateway, routing tables
- `security-groups.tf` - Security groups with AD ports (DNS, LDAP, Kerberos, RDP)
- `ad-domain-controller.tf` - EC2 instance configured as Domain Controller
- `outputs.tf` - Connection info, next steps instructions
- `scripts/userdata.ps1` - PowerShell script for automated DC setup
- `terraform.tfvars.example` - Example configuration template
- `.gitignore` - Protect sensitive files (*.tfvars, *.tfstate)
- `README.md` - Comprehensive deployment guide

**SCIM Server** infrastructure files (in `infrastructure/scim-server/` subdirectory):
- `provider.tf` - AWS provider with S3 backend configuration
- `variables.tf` - SCIM server variables (domain, tokens, network config, entitlements_file)
- `main.tf` - EC2 instance, security groups, Elastic IP, Route53 DNS
- `outputs.tf` - SCIM URLs, Okta configuration values, setup instructions
- `user-data.sh` - Server initialization (Caddy + Flask, downloads entitlements.json)
- `demo_scim_server.py` - Flask SCIM 2.0 server (loads entitlements from JSON file)
- `entitlements.json` - Default entitlement/role definitions (5 standard roles)
- `examples/entitlements-salesforce.json` - Salesforce-style roles (6 roles)
- `examples/entitlements-aws.json` - AWS IAM-style permissions (7 roles)
- `examples/entitlements-generic.json` - Generic application roles (7 roles)
- `requirements.txt` - Python dependencies
- `.gitignore` - Protect sensitive files
- `README.md` - Complete deployment and configuration guide

**SCIM Application** (in `terraform/` directory - Okta side):
- `scim_app.tf` - Okta SCIM application resource
  - Data source to read SCIM server state from S3
  - Creates Okta app for SCIM provisioning
  - Outputs app ID and configuration commands
- `scripts/configure_scim_app.py` - Python script to configure SCIM connection via API
  - Enables SCIM provisioning
  - Configures connection (base URL, authentication)
  - Tests connection
  - Enables provisioning features

## Naming Conventions

### Resource Names (in Terraform)
- Use snake_case: `okta_user.john_doe`
- Be descriptive: `okta_group.engineering_team`
- Use prefixes for imported resources: `tfer--user_00u1234567890`

### File Organization
- One resource type per file
- Group related resources together
- Use comments to explain complex configurations

## Important Patterns

### User Name Template
Always escape template strings with `$$`:
```hcl
user_name_template = "$${source.login}"
```

### Resource Dependencies
Use explicit depends_on when needed:
```hcl
resource "okta_group_memberships" "example" {
  depends_on = [okta_user.john_doe]
  # ...
}
```

### OIG Resources
- Entitlement bundles: Manage bundle definitions only
- Principal assignments: Manage via Okta Admin Console (not Terraform)
- Resource owners: Manage via Python scripts (API-only, stored in `config/owner_mappings.json`)
- Governance labels: Manage via Python scripts (API-only, stored in `config/label_mappings.json`)
- Risk rules (SOD policies): Manage via Python scripts (API-only, stored in `config/risk_rules.json`)

## Environment-Specific Paths

When generating code for a specific environment, use:
- Okta Terraform files: `environments/{env}/terraform/`
- Infrastructure files: `environments/{env}/infrastructure/`
- Imports: `environments/{env}/imports/`
- Config: `environments/{env}/config/`

Example for myorg:
- `environments/myorg/terraform/users.tf` (Okta resources)
- `environments/myorg/infrastructure/vpc.tf` (AWS resources)

## Infrastructure Patterns

### When to Generate Infrastructure
Generate infrastructure code when the user requests:
- Active Directory integration or Domain Controller setup
- Windows Server deployment
- VPC or AWS networking setup
- "AD Agent" or "Okta AD integration" infrastructure

### Infrastructure Directory Structure
Infrastructure is SEPARATE from Okta Terraform:
- **Location:** `environments/{env}/infrastructure/`
- **Provider:** AWS (not Okta)
- **State:** Separate S3 backend (`{env}/infrastructure/terraform.tfstate`)
- **Purpose:** Supporting infrastructure for Okta integrations

### Infrastructure vs Okta Resources
**Never mix infrastructure and Okta resources in the same file!**

```
terraform/           → Okta provider (okta_user, okta_group, etc.)
infrastructure/      → AWS provider (aws_vpc, aws_instance, etc.)
```

Each has its own provider, state, and backend configuration.

### SCIM Server Integration (NEW!)

When to generate SCIM server infrastructure:
- User requests "SCIM server", "custom SCIM", or "API-only entitlements" demo
- User wants to demonstrate provisioning to custom applications
- User needs to show custom roles/entitlements not mapped to app resources

**Two-Phase SCIM Automation:**

1. **Infrastructure** (`infrastructure/scim-server/`):
   - Deploys AWS EC2 with Flask SCIM 2.0 server
   - Automatic HTTPS via Caddy + Let's Encrypt
   - Custom entitlements/roles
   - State: `s3://bucket/Okta-GitOps/{env}/scim-server/terraform.tfstate`
   - **Deployment:** GitHub Actions workflow (`.github/workflows/deploy-scim-server.yml`)

2. **Okta App** (`terraform/scim_app.tf`):
   - Creates Okta application for SCIM provisioning
   - Reads SCIM server outputs via data source
   - Must be configured via Python script (provider limitation)

**Complete Workflow (GitHub Actions - Recommended):**
```bash
# Step 1: Add secrets to GitHub Environment
# Navigate to: Settings → Environments → MyOrg → Add secrets
# Required: SCIM_AUTH_TOKEN, AWS_REGION, AWS_ROLE_ARN

# Step 2: Deploy SCIM server via workflow
gh workflow run deploy-scim-server.yml \
  -f environment=myorg \
  -f domain_name=scim.demo-myorg.example.com \
  -f route53_zone_id=Z1234567890ABC \
  -f instance_type=t3.micro \
  -f entitlements_file=entitlements.json \
  -f action=apply

# Optional: Use custom entitlements (e.g., Salesforce roles)
# -f entitlements_file=examples/entitlements-salesforce.json

# Step 3: Create Okta SCIM app
cd environments/myorg/terraform
terraform apply

# Step 4: Configure SCIM connection (Python - API only)
python3 ../../scripts/configure_scim_app.py \
  --app-id $(terraform output -raw scim_app_id) \
  --scim-url https://scim.demo-myorg.example.com/scim/v2 \
  --scim-token <from-github-secret-SCIM_AUTH_TOKEN> \
  --test-connection
```

**Alternative: Manual Terraform Deployment**
```bash
# For local development/testing
cd environments/myorg/infrastructure/scim-server
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars  # Edit with your values
terraform init
terraform apply
```

**Why Python Script?**
Okta Terraform provider (v6.4.0) does NOT support SCIM connection configuration.
These settings must be configured via Okta Admin API (Python script handles this).

**Documentation:**
- GitHub Workflow: `.github/workflows/deploy-scim-server.yml`
- SCIM Server README: `environments/myorg/infrastructure/scim-server/README.md`
- Automation Guide: `docs/SCIM_OKTA_AUTOMATION.md`
- Secrets Migration: `environments/myorg/infrastructure/scim-server/GITHUB_SECRETS_MIGRATION.md`
