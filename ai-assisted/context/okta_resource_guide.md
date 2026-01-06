# Okta Resource Quick Reference

Comprehensive reference for Okta Terraform resources. This guide covers 80+ resources commonly used in demo environments and production deployments.

**Provider Version:** Okta Terraform Provider 6.4.0+ (OIG support requires 6.4.0+)

## Table of Contents

- [Core Resources](#core-resources) - Users, Groups, Applications
- [OIG (Identity Governance) Resources](#oig-identity-governance-resources) - Entitlements, Bundles, Reviews
- [Authorization & Security](#authorization--security) - Auth Servers, Policies
- [Sign-On and Access Policies](#sign-on-and-access-policies) - Authentication flows
- [Network and Security](#network-and-security) - Zones, Trusted Origins
- [Identity Providers](#identity-providers) - Social, SAML, OIDC IdPs
- [User Schema and Profiles](#user-schema-and-profiles) - Custom attributes
- [Authenticators and Factors](#authenticators-and-factors) - MFA configuration
- [Hooks and Automation](#hooks-and-automation) - Event and Inline hooks
- [Admin Roles](#admin-roles) - Custom admin roles
- [Email and Branding](#email-and-branding) - Email templates, domains
- [Common Data Sources](#common-data-sources) - Lookups
- [Infrastructure Resources (AWS)](#infrastructure-resources-aws) - VPC, EC2
- [Okta Privileged Access (OPA)](#okta-privileged-access-opa-resources) - Server access

---

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
- **Key attributes:** `sso_url`, `audience`, `subject_name_id_template`, `attribute_statements`

### okta_app_bookmark
Creates bookmark (chiclet) applications
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_bookmark
- **Use for:** Simple link apps in the Okta dashboard
- **Key attributes:** `url`, `label`

### okta_app_secure_password_store
Creates Secure Web Authentication (SWA) apps
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_secure_password_store
- **Use for:** Apps that require username/password fill

### okta_app_basic_auth
Creates basic auth applications
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_basic_auth
- **Use for:** Legacy apps requiring HTTP basic auth

### okta_app_auto_login
Creates auto-login (SWA) applications
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_auto_login
- **Use for:** Apps with form-based login that Okta can auto-fill

### okta_app_group_assignment
Assigns a single group to an application
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_group_assignment
- **Use for:** Controlling which groups can access which apps
- **Note:** Use `okta_app_group_assignments` (plural) to assign multiple groups in one resource

### okta_app_group_assignments
Assigns multiple groups to an application
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_group_assignments
- **Use for:** Bulk group assignments to apps
- **Preferred over:** Multiple `okta_app_group_assignment` resources

### okta_app_user
Assigns a user directly to an application
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_user
- **Use for:** Direct user-to-app assignments (prefer group assignments when possible)

### okta_app_oauth_api_scope
Grants OAuth scopes to an OAuth app
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_oauth_api_scope
- **Use for:** Granting Okta API scopes to service apps

### okta_app_oauth_post_logout_redirect_uri
Manages post-logout redirect URIs
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_oauth_post_logout_redirect_uri
- **Use for:** Adding logout redirect URIs to OAuth apps

### okta_app_oauth_redirect_uri
Manages redirect URIs for OAuth apps
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_oauth_redirect_uri
- **Use for:** Dynamically managing redirect URIs

### okta_app_saml_app_settings
Manages SAML app settings separately
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_saml_app_settings
- **Use for:** Managing SAML settings independently from the app

### okta_app_signon_policy
Application sign-on policies
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_signon_policy
- **Use for:** App-specific authentication requirements
- **Note:** Different from global sign-on policies

### okta_app_signon_policy_rule
Rules within app sign-on policies
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_signon_policy_rule
- **Use for:** Defining conditions and actions for app authentication

---

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

### okta_policy_password_rule
Password policy rules
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/policy_password_rule
- **Use for:** Defining password policy rule conditions

### okta_policy_mfa_rule
MFA policy rules
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/policy_mfa_rule
- **Use for:** Defining MFA enrollment conditions and requirements

### okta_auth_server_policy
Authorization server access policies
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/auth_server_policy
- **Use for:** Defining token issuance policies for custom auth servers

### okta_auth_server_policy_rule
Authorization server policy rules
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/auth_server_policy_rule
- **Use for:** Defining conditions for token grants (scopes, grant types, users)

---

## Sign-On and Access Policies

### okta_policy_signon
Global session policies (formerly sign-on policies)
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/policy_signon
- **Use for:** Controlling session behavior, device trust, location-based access

### okta_policy_signon_rule
Sign-on policy rules
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/policy_signon_rule
- **Use for:** Defining conditions for session creation

### okta_policy_rule_idp_discovery
Identity Provider discovery rules
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/policy_rule_idp_discovery
- **Use for:** Routing users to different IdPs based on conditions

### okta_policy_profile_enrollment
Profile enrollment policies
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/policy_profile_enrollment
- **Use for:** Self-service registration policies

### okta_policy_profile_enrollment_apps
Apps assigned to profile enrollment policies
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/policy_profile_enrollment_apps
- **Use for:** Assigning apps to enrollment policies

### okta_policy_access
Access policies for resource access
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/policy_access
- **Use for:** Defining access policies for protected resources

---

## Network and Security

### okta_network_zone
Network zones for location-based policies
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/network_zone
- **Use for:** Defining trusted networks, blocklists, geolocation zones
- **Types:** IP (CIDRs), DYNAMIC (geolocation)
- **Example use:** Block access from certain countries, allow only corporate IPs

### okta_trusted_origin
Trusted origins for CORS and redirect
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/trusted_origin
- **Use for:** Allowing cross-origin requests from your applications
- **Scopes:** CORS, REDIRECT, or both

### okta_threat_insight_settings
ThreatInsight configuration
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/threat_insight_settings
- **Use for:** Enabling and configuring Okta ThreatInsight

### okta_security_notification_emails
Security notification settings
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/security_notification_emails
- **Use for:** Configuring security email notifications

---

## Identity Providers

### okta_idp_oidc
OpenID Connect Identity Providers
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/idp_oidc
- **Use for:** Federating with external OIDC providers

### okta_idp_saml
SAML Identity Providers
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/idp_saml
- **Use for:** Federating with external SAML IdPs (Azure AD, other Okta orgs)

### okta_idp_social
Social Identity Providers
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/idp_social
- **Use for:** Google, Facebook, Microsoft, LinkedIn, etc.
- **Types:** GOOGLE, FACEBOOK, MICROSOFT, LINKEDIN, APPLE

### okta_idp_saml_key
SAML IdP signing keys
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/idp_saml_key
- **Use for:** Managing SAML signing certificates

### SAML Federation Module
**Recommended:** Use `modules/saml-federation/` for SAML federation scenarios:
- **Module:** `modules/saml-federation/`
- **Docs:** `docs/SAML_FEDERATION.md`
- **AI Prompt:** `ai-assisted/prompts/setup_saml_federation.md`
- **Use for:** Okta-to-Okta federation, external IdP integration (Azure AD, Google)
- **Features:** Dual-mode (SP/IdP), remote state coordination, JIT provisioning

### okta_profile_mapping
Attribute mappings between IdP and Okta profiles
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/profile_mapping
- **Use for:** Mapping attributes from IdP to Okta user profile
- **Note:** Also used for app-to-user profile mappings

---

## User Schema and Profiles

### okta_user_schema_property
Custom user profile attributes
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/user_schema_property
- **Use for:** Adding custom attributes to user profiles
- **Types:** string, boolean, number, integer, array, object

### okta_user_base_schema_property
Base schema property overrides
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/user_base_schema_property
- **Use for:** Modifying base profile attributes (firstName, lastName, etc.)

### okta_user_type
Custom user types
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/user_type
- **Use for:** Creating different user types (Employee, Contractor, Partner)

### okta_group_schema_property
Custom group profile attributes
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/group_schema_property
- **Use for:** Adding custom attributes to group profiles

### okta_app_user_schema_property
Application user profile attributes
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_user_schema_property
- **Use for:** Custom attributes in app user profiles

### okta_app_user_base_schema_property
Application base schema overrides
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/app_user_base_schema_property
- **Use for:** Modifying base app user attributes

### okta_link_definition
Custom relationship definitions
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/link_definition
- **Use for:** Creating custom relationships between users (e.g., manager-report)

### okta_link_value
User relationship assignments
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/link_value
- **Use for:** Setting manager relationships, custom links between users
- **Example:** Assigning managers to employees

---

## Authenticators and Factors

### okta_authenticator
Authenticator configuration
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/authenticator
- **Use for:** Enabling and configuring authenticators (email, phone, security key)
- **Types:** email, phone, password, security_question, app (Okta Verify), webauthn

### okta_factor
Factor configuration (deprecated, use authenticator)
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/factor
- **Use for:** Legacy factor management
- **Note:** Prefer `okta_authenticator` for new implementations

### okta_factor_totp
TOTP factor settings
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/factor_totp
- **Use for:** Configuring time-based OTP settings

---

## Hooks and Automation

### okta_event_hook
Event hooks for external integrations
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/event_hook
- **Use for:** Sending events to external services (user creation, login, etc.)
- **Events:** user.lifecycle.create, user.session.start, etc.

### okta_inline_hook
Inline hooks for customization
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/inline_hook
- **Use for:** Customizing registration, import, SAML assertions, token claims
- **Types:** com.okta.user.pre-registration, com.okta.tokens.transform, etc.

### okta_event_hook_verification
Event hook verification
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/event_hook_verification
- **Use for:** Triggering verification of event hook endpoints

---

## Admin Roles

### okta_admin_role_custom
Custom admin roles
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/admin_role_custom
- **Use for:** Creating custom admin roles with specific permissions
- **Example:** Help desk role with limited user management

### okta_admin_role_custom_assignments
Custom role assignments
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/admin_role_custom_assignments
- **Use for:** Assigning custom roles to users or groups

### okta_admin_role_targets
Admin role target restrictions
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/admin_role_targets
- **Use for:** Limiting admin role scope to specific apps or groups

### okta_user_admin_roles
User admin role assignments
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/user_admin_roles
- **Use for:** Assigning built-in admin roles to users

### okta_group_role
Group admin role assignments
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/group_role
- **Use for:** Assigning admin roles to groups

---

## Email and Branding

### okta_email_customization
Email template customization
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/email_customization
- **Use for:** Customizing Okta email templates (welcome, password reset, etc.)

### okta_email_domain
Custom email domain
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/email_domain
- **Use for:** Sending Okta emails from your domain

### okta_email_sender
Email sender configuration
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/email_sender
- **Use for:** Configuring email sender addresses

### okta_domain
Custom domain for Okta org
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/domain
- **Use for:** Custom domain (login.yourcompany.com)

### okta_domain_certificate
SSL certificate for custom domain
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/domain_certificate
- **Use for:** Managing SSL certificates for custom domains

### okta_brand
Branding configuration
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/brand
- **Use for:** Configuring org branding settings

### okta_theme
UI theme configuration
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/resources/theme
- **Use for:** Customizing sign-in page appearance

---

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

### data "okta_app_oauth"
Look up OAuth applications
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/app_oauth
- **Use for:** Getting OAuth app details (client_id, etc.)

### data "okta_app_saml"
Look up SAML applications
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/app_saml
- **Use for:** Getting SAML app metadata

### data "okta_users"
Look up multiple users
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/users
- **Use for:** Searching users by filter expression

### data "okta_groups"
Look up multiple groups
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/groups
- **Use for:** Searching groups by filter

### data "okta_auth_server"
Look up authorization server
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/auth_server
- **Use for:** Getting auth server details

### data "okta_auth_server_scopes"
Look up auth server scopes
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/auth_server_scopes
- **Use for:** Listing available scopes on auth server

### data "okta_authenticator"
Look up authenticator
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/authenticator
- **Use for:** Getting authenticator configuration

### data "okta_network_zone"
Look up network zone
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/network_zone
- **Use for:** Referencing existing network zones

### data "okta_idp_social"
Look up social IdP
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/idp_social
- **Use for:** Getting social IdP configuration

### data "okta_policy"
Look up policy by type and name
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/policy
- **Use for:** Referencing default policies

### data "okta_brands"
List all brands
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/brands
- **Use for:** Getting brand IDs for customization

### data "okta_default_signin_page"
Get default sign-in page
- **Docs:** https://registry.terraform.io/providers/okta/okta/latest/docs/data-sources/default_signin_page
- **Use for:** Referencing default sign-in page settings

---

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

## Okta Privileged Access (OPA) Resources

**Provider:** `okta/oktapam` (optional, separate from okta/okta)
**Setup:** See `docs/OPA_SETUP.md`
**Examples:** `environments/myorg/terraform/opa_resources.tf.example`

### oktapam_resource_group
Top-level organizational unit for OPA
- **Docs:** https://registry.terraform.io/providers/okta/oktapam/latest/docs/resources/resource_group
- **Use for:** Organizing servers, secrets, and policies by team or environment

### oktapam_resource_group_project
Project within a resource group
- **Docs:** https://registry.terraform.io/providers/okta/oktapam/latest/docs/resources/resource_group_project
- **Use for:** Grouping servers by function (web servers, databases, etc.)

### oktapam_resource_group_server_enrollment_token
Token for enrolling servers into OPA
- **Docs:** https://registry.terraform.io/providers/okta/oktapam/latest/docs/resources/resource_group_server_enrollment_token
- **Use for:** Automating server enrollment during provisioning

### oktapam_gateway_setup_token
Token for registering OPA gateways
- **Docs:** https://registry.terraform.io/providers/okta/oktapam/latest/docs/resources/gateway_setup_token
- **Use for:** Deploying gateways for network connectivity

### oktapam_secret_folder / oktapam_secret
Secret storage in OPA
- **Docs:** https://registry.terraform.io/providers/okta/oktapam/latest/docs/resources/secret_folder
- **Use for:** Storing credentials, API keys, and sensitive data

### oktapam_security_policy_v2
Access policies for servers and resources
- **Docs:** https://registry.terraform.io/providers/okta/oktapam/latest/docs/resources/security_policy_v2
- **Use for:** Defining who can access which servers with what privileges
- **Note:** Under active development, breaking changes may occur

### oktapam_group / oktapam_project_group
OPA groups and project assignments
- **Docs:** https://registry.terraform.io/providers/okta/oktapam/latest/docs/resources/group
- **Use for:** Organizing users and assigning server access permissions

## Additional Resources

- **Full Resource Catalog:** `docs/TERRAFORM_RESOURCES.md`
- **Provider Documentation:** https://registry.terraform.io/providers/okta/okta/latest/docs
- **OPA Provider Documentation:** https://registry.terraform.io/providers/okta/oktapam/latest/docs
- **Okta Developer Docs:** https://developer.okta.com/
