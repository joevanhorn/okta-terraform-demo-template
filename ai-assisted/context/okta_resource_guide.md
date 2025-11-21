# Okta Resource Quick Reference

Quick reference for common Okta Terraform resources.

## Core Resources

### okta_user
Manages Okta users
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/user
- **Use for:** Creating users for demos, testing, employee onboarding

### okta_group
Manages Okta groups
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/group
- **Use for:** Organizing users by department, role, or access level

### okta_group_memberships
Assigns users to groups
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/group_memberships
- **Use for:** Adding users to one or more groups

### okta_app_oauth
Creates OAuth 2.0 / OIDC applications
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_oauth
- **Use for:** Integrating web apps, SPAs, mobile apps, APIs
- **Types:** web, browser, native, service

### okta_app_saml
Creates SAML applications
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_saml
- **Use for:** Enterprise app integrations (Salesforce, Workday, etc.)

### okta_app_group_assignment
Assigns groups to applications
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_group_assignment
- **Use for:** Controlling which groups can access which apps

## OIG (Identity Governance) Resources

### okta_entitlement
Manages application-level entitlements (access rights)
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/entitlement
- **Use for:** Defining access rights on applications (e.g., "Account Access", "Role Permissions")
- **Note:** Values get Okta-generated IDs that bundles reference
- **Critical:** Values MUST be in alphabetical order by `external_value` (Okta API sorts them)

### okta_entitlement_bundle
Manages entitlement bundles (packages of access)
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/entitlement_bundle
- **Use for:** Creating access bundles (e.g., "Marketing Tools", "Engineering Access")
- **Note:** Manage bundle definitions only; assign principals via Okta UI
- **Critical:** Use dynamic blocks to reference Okta-generated value IDs by external_value string

### okta_reviews
Manages access review campaigns
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/reviews
- **Use for:** Setting up periodic access reviews for compliance

### okta_resource_set
Manages resource sets for OIG
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/resource_set
- **Use for:** Grouping resources for governance workflows

## Authorization & Security

### okta_auth_server
Custom authorization servers
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/auth_server
- **Use for:** Creating custom OAuth 2.0 authorization servers for APIs

### okta_auth_server_scope
OAuth scopes for authorization servers
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/auth_server_scope
- **Use for:** Defining granular permissions (read:data, write:data, etc.)

### okta_auth_server_claim
Custom claims in tokens
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/auth_server_claim
- **Use for:** Adding user attributes to ID tokens and access tokens

### okta_policy_mfa
Multi-factor authentication policies
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/policy_mfa
- **Use for:** Enforcing MFA requirements for users/groups

### okta_policy_password
Password policies
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/policy_password
- **Use for:** Setting password complexity, expiration, history rules

## Common Data Sources

### data "okta_user"
Look up existing users
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/user
- **Use for:** Referencing users created outside Terraform

### data "okta_group"
Look up existing groups
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/group
- **Use for:** Referencing default Okta groups (Everyone, etc.)

### data "okta_app"
Look up existing applications
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/app
- **Use for:** Referencing Okta system apps

## Resource Relationships

```
okta_user ──┐
            ├──> okta_group_memberships ──> okta_group ──> okta_app_group_assignment ──> okta_app_oauth
okta_user ──┘

okta_auth_server ──┬──> okta_auth_server_scope
                   └──> okta_auth_server_claim

okta_entitlement_bundle (manage via Terraform)
    └──> Principal assignments (manage via Okta UI)
```

## Typical Demo Scenarios

### Basic User Onboarding
1. Create users (`okta_user`)
2. Create department groups (`okta_group`)
3. Assign users to groups (`okta_group_memberships`)
4. Create applications (`okta_app_oauth`)
5. Assign groups to apps (`okta_app_group_assignment`)

### API Access Control
1. Create auth server (`okta_auth_server`)
2. Define scopes (`okta_auth_server_scope`)
3. Add custom claims (`okta_auth_server_claim`)
4. Create service app (`okta_app_oauth` type=service)
5. Grant scopes to app

### Identity Governance Demo
1. Create users and groups (basic setup)
2. Create entitlement bundles (`okta_entitlement_bundle`)
3. Assign apps to bundles (via Okta UI)
4. Create access reviews (`okta_reviews`)
5. Demonstrate access certification workflow

## Important Notes

### Template String Escaping
Always use `$$` to escape Okta template expressions:
```hcl
user_name_template = "$${source.login}"  # Correct
```

### Status Values
Most resources support `status` attribute:
- `"ACTIVE"` - Resource is active
- `"INACTIVE"` - Resource is disabled
- `"STAGED"` - User not yet activated (users only)

### OIG License Required
These resources require Okta Identity Governance license:
- `okta_entitlement_bundle`
- `okta_reviews`
- `okta_resource_set`
- Related OIG resources

### Risk Rules (Separation of Duties Policies)

**API-Only** - Not available in Terraform provider

Risk rules detect and prevent conflicting access patterns (Separation of Duties violations).

**Management:**
- **Import:** `python3 scripts/import_risk_rules.py --output environments/myenv/config/risk_rules.json`
- **Apply:** `python3 scripts/apply_risk_rules.py --config environments/myenv/config/risk_rules.json`
- **Configuration:** JSON file at `environments/{env}/config/risk_rules.json`

**Structure:**
- **Type:** Always "SEPARATION_OF_DUTIES"
- **Resources:** Array with max 1 resource (app, bundle, or collection ORN)
- **Conflict Criteria:** AND conditions with CONTAINS_ONE or CONTAINS_ALL operations
- **Entitlements:** Array of entitlement set ID + value ID pairs (max 10 per list)

**Example Use Cases:**
- Maker-Checker: Invoice creator ≠ invoice approver
- Change Management: Change implementer ≠ change approver
- Financial Controls: Payment creator ≠ payment authorizer
- Data Access: Database admin ≠ production deployer

**Docs:** See `docs/API_MANAGEMENT.md` (Risk Rules section) for complete guide

### API-Only Features
Some OIG features are API-only (not in Terraform):
- Resource owners (use Python scripts: `scripts/apply_resource_owners.py`)
- Governance labels (use Python scripts: `scripts/apply_admin_labels.py`, `scripts/sync_label_mappings.py`)
- Risk rules / SOD policies (use Python scripts: `scripts/import_risk_rules.py`, `scripts/apply_risk_rules.py`)
- Principal assignments to bundles (manage via Okta Admin Console)

## Infrastructure Resources (AWS)

**Important:** Infrastructure resources are in `environments/{env}/infrastructure/`, NOT in `terraform/` directory.

### aws_vpc
VPC for Active Directory infrastructure
- **Docs:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc
- **Use for:** Creating isolated network for Domain Controller
- **Typical CIDR:** 10.0.0.0/16

### aws_subnet
Subnets within VPC
- **Docs:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/subnet
- **Use for:** Public subnet for Domain Controller, private subnet for future resources

### aws_security_group
Firewall rules for EC2 instances
- **Docs:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group
- **Use for:** Opening Active Directory ports (DNS 53, LDAP 389, Kerberos 88, SMB 445, RDP 3389, etc.)
- **Critical:** Must include ALL AD ports for proper functionality

### aws_instance
EC2 instances (Windows Server)
- **Docs:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance
- **Use for:** Domain Controller (Windows Server 2022)
- **AMI:** Use data source to find latest Windows Server 2022 AMI
- **Instance type:** t3.medium minimum for Domain Controller
- **User data:** PowerShell script for automated DC promotion

### aws_eip
Elastic IP for stable public address
- **Docs:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eip
- **Use for:** Providing stable IP for RDP access and Okta AD Agent connection

### Infrastructure Typical Flow
1. Create VPC and networking (`aws_vpc`, `aws_subnet`, `aws_internet_gateway`)
2. Set up security groups with AD ports (`aws_security_group`)
3. Deploy Domain Controller EC2 instance (`aws_instance`)
4. Assign Elastic IP (`aws_eip`)
5. Wait for automated setup (PowerShell user_data script)
6. Install Okta AD Agent manually (installer is pre-downloaded)

## Additional Resources

- **Full Resource Catalog:** `docs/TERRAFORM_RESOURCES.md`
- **Provider Documentation:** https://registry.terraform.io/providers/okta/okta/latest/docs
- **Okta Developer Docs:** https://developer.okta.com/
