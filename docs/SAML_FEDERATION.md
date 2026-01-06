# SAML Federation Guide

This guide covers SAML federation configuration using the `saml-federation` Terraform module. Learn how to set up Okta-to-Okta federation, integrate external identity providers, and troubleshoot common issues.

## Table of Contents

- [Overview](#overview)
- [SAML Federation Concepts](#saml-federation-concepts)
- [Module Architecture](#module-architecture)
- [Okta-to-Okta Federation](#okta-to-okta-federation)
- [External IdP Integration](#external-idp-integration)
- [JIT Provisioning](#jit-provisioning)
- [IdP Discovery & Routing](#idp-discovery--routing)
- [Attribute Mapping](#attribute-mapping)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

---

## Overview

SAML federation allows users from one identity provider (IdP) to access resources in another organization (Service Provider/SP) without creating separate accounts. This is essential for:

- **Partner access**: Allow partner employees to access your applications
- **M&A integration**: Temporary federation during mergers
- **Hub-and-spoke**: Central identity for multiple Okta tenants
- **External IdP**: Integrate Azure AD, Google Workspace, etc.

---

## SAML Federation Concepts

### Roles in SAML

| Role | Description | Module Mode |
|------|-------------|-------------|
| **Identity Provider (IdP)** | Authenticates users, issues assertions | `federation_mode = "idp"` |
| **Service Provider (SP)** | Receives assertions, grants access | `federation_mode = "sp"` |

### SAML Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                          SAML Flow                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. User accesses SP application                                  │
│     ↓                                                             │
│  2. SP redirects to IdP (AuthnRequest)                           │
│     ↓                                                             │
│  3. IdP authenticates user                                        │
│     ↓                                                             │
│  4. IdP sends assertion to SP (via ACS URL)                      │
│     ↓                                                             │
│  5. SP validates assertion, creates session                       │
│     ↓                                                             │
│  6. User accesses application                                     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Key SAML Components

| Component | Description | Where Configured |
|-----------|-------------|------------------|
| **Issuer/Entity ID** | Unique identifier for IdP | IdP side |
| **SSO URL** | Where SP sends AuthnRequests | IdP side |
| **ACS URL** | Where IdP sends assertions | SP side |
| **Audience** | Expected recipient of assertion | SP side |
| **Signing Certificate** | X.509 cert for assertion validation | IdP provides, SP stores |

---

## Module Architecture

The `saml-federation` module operates in two modes:

### SP Mode (`federation_mode = "sp"`)

Creates resources for **receiving** SAML assertions:

- `okta_idp_saml_key` - Stores IdP's signing certificate
- `okta_idp_saml` - External IdP configuration
- `okta_policy_rule_idp_discovery` - Routing rules (optional)

### IdP Mode (`federation_mode = "idp"`)

Creates resources for **sending** SAML assertions:

- `okta_app_saml` - SAML application configured for partner SP
- `okta_app_group_assignments` - Controls who can federate

### Cross-Org Coordination

The module uses `terraform_remote_state` for automatic configuration exchange:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Remote State Pattern                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Hub Org (IdP)                    Spoke Org (SP)                │
│  ┌──────────────┐                 ┌──────────────┐              │
│  │  IdP Mode    │  ◄── reads ──   │  SP Mode     │              │
│  │              │                 │              │              │
│  │  Outputs:    │                 │  Outputs:    │              │
│  │  - issuer    │  ── reads ──►   │  - idp_id    │              │
│  │  - sso_url   │                 │  - acs_url   │              │
│  │  - cert      │                 │  - audience  │              │
│  └──────────────┘                 └──────────────┘              │
│        │                                │                        │
│        └────────── S3 State ────────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Okta-to-Okta Federation

### Use Case

You have multiple Okta organizations (production, staging, partner tenants) and want users to authenticate once and access resources across organizations.

### Architecture

```
         Hub Organization               Spoke Organizations
        ┌───────────────┐              ┌───────────────┐
        │               │   SAML       │               │
        │  Central IdP  │ ──────────►  │   Spoke 1     │
        │  (IdP Mode)   │              │   (SP Mode)   │
        │               │              │               │
        └───────────────┘              └───────────────┘
               │
               │                       ┌───────────────┐
               │          SAML         │               │
               └────────────────────►  │   Spoke 2     │
                                       │   (SP Mode)   │
                                       │               │
                                       └───────────────┘
```

### Step-by-Step Setup

#### Prerequisites

- Both Okta organizations accessible
- Shared S3 bucket for Terraform state
- AWS credentials configured

#### Step 1: Configure Spoke Organization (SP)

Create `environments/spoke/terraform/federation.tf`:

```hcl
# =============================================================================
# SAML Federation - Receive Assertions from Hub
# =============================================================================

module "federation_from_hub" {
  source = "../../../modules/saml-federation"

  federation_mode = "sp"
  federation_name = "hub-org"
  okta_org_name   = var.okta_org_name
  okta_base_url   = var.okta_base_url

  # Don't use remote state yet - hub isn't deployed
  use_remote_state = false

  # JIT provisioning settings
  provisioning_action = "AUTO"
  account_link_action = "AUTO"
  username_template   = "idpuser.email"

  # Assign federated users to a group
  groups_action     = "ASSIGN"
  groups_assignment = [okta_group.federated_users.id]
}

# Group for federated users
resource "okta_group" "federated_users" {
  name        = "Federated Users - Hub"
  description = "Users authenticated via Hub org federation"
}

# Outputs for Hub to reference
output "idp_id" {
  value = module.federation_from_hub.idp_id
}

output "idp_acs_url" {
  value = module.federation_from_hub.idp_acs_url
}

output "okta_org_name" {
  value = var.okta_org_name
}

output "okta_base_url" {
  value = var.okta_base_url
}
```

#### Step 2: Deploy Spoke (Partial)

```bash
cd environments/spoke/terraform
terraform init
terraform apply

# Note: IdP won't have full config yet (no issuer/sso_url/cert)
# This creates the IdP resource and outputs ACS URL
```

#### Step 3: Configure Hub Organization (IdP)

Create `environments/hub/terraform/federation.tf`:

```hcl
# =============================================================================
# SAML Federation - Send Assertions to Spoke
# =============================================================================

module "federation_to_spoke" {
  source = "../../../modules/saml-federation"

  federation_mode = "idp"
  federation_name = "spoke-org"
  okta_org_name   = var.okta_org_name
  okta_base_url   = var.okta_base_url

  # Read SP configuration from Spoke's state
  use_remote_state = true
  remote_state_config = {
    bucket = "okta-terraform-state"
    key    = "okta/spoke/terraform.tfstate"
    region = "us-east-1"
  }

  # Groups that can federate
  assigned_group_ids = [okta_group.employees.id]

  # Attribute statements
  attribute_statements = [
    {
      name   = "firstName"
      values = ["user.firstName"]
    },
    {
      name   = "lastName"
      values = ["user.lastName"]
    },
    {
      name   = "email"
      values = ["user.email"]
    },
  ]
}

# Outputs for Spoke to reference
output "federation_issuer" {
  value = module.federation_to_spoke.federation_issuer
}

output "federation_sso_url" {
  value = module.federation_to_spoke.federation_sso_url
}

output "federation_certificate" {
  value     = module.federation_to_spoke.federation_certificate
  sensitive = true
}

output "okta_org_name" {
  value = var.okta_org_name
}

output "okta_base_url" {
  value = var.okta_base_url
}
```

#### Step 4: Deploy Hub

```bash
cd environments/hub/terraform
terraform init
terraform apply

# This creates the SAML app and outputs issuer/sso_url/cert
```

#### Step 5: Update Spoke to Read Hub State

Update `environments/spoke/terraform/federation.tf`:

```hcl
module "federation_from_hub" {
  source = "../../../modules/saml-federation"

  federation_mode = "sp"
  federation_name = "hub-org"
  okta_org_name   = var.okta_org_name
  okta_base_url   = var.okta_base_url

  # NOW enable remote state to read Hub's config
  use_remote_state = true
  remote_state_config = {
    bucket = "okta-terraform-state"
    key    = "okta/hub/terraform.tfstate"
    region = "us-east-1"
  }

  # ... rest of config unchanged
}
```

#### Step 6: Re-apply Spoke

```bash
cd environments/spoke/terraform
terraform apply

# IdP is now fully configured with Hub's issuer/sso_url/cert
```

#### Step 7: Test Federation

1. Access the Spoke organization's Okta dashboard
2. Click "Sign in with Hub Org" (or the IdP name you configured)
3. Authenticate with Hub credentials
4. Verify you're redirected back to Spoke with a session

---

## External IdP Integration

### Azure AD Integration

#### Azure AD Configuration

1. **Create Enterprise Application:**
   - Azure Portal → Enterprise Applications → New Application
   - Create your own application → Non-gallery
   - Name: "Okta Federation"

2. **Configure SAML:**
   - Single sign-on → SAML
   - Note the following (you'll use these in Terraform):
     - Login URL
     - Azure AD Identifier
   - Download: Certificate (Base64)

3. **Save certificate:**
   ```bash
   # Save downloaded cert to your environment
   mv ~/Downloads/AzureAD_Certificate.cer \
      environments/myorg/terraform/certs/azure-ad.pem
   ```

#### Terraform Configuration

```hcl
# =============================================================================
# Azure AD Federation
# =============================================================================

# Get IdP discovery policy
data "okta_policy" "idp_discovery" {
  name = "Idp Discovery Policy"
  type = "IDP_DISCOVERY"
}

# Azure AD federation module
module "azure_ad" {
  source = "../../../modules/saml-federation"

  federation_mode = "sp"
  federation_name = "azure-ad"
  okta_org_name   = var.okta_org_name
  okta_base_url   = var.okta_base_url

  # Azure AD configuration
  idp_name        = "Azure AD - Corporate"
  idp_issuer      = "https://sts.windows.net/${var.azure_tenant_id}/"
  idp_sso_url     = "https://login.microsoftonline.com/${var.azure_tenant_id}/saml2"
  idp_certificate = file("${path.module}/certs/azure-ad.pem")

  # JIT provisioning
  provisioning_action = "AUTO"
  account_link_action = "AUTO"
  username_template   = "idpuser.email"

  # Route corporate users
  enable_routing_rule   = true
  routing_policy_id     = data.okta_policy.idp_discovery.id
  routing_domain_suffix = "@company.com"
}

# Output URLs for Azure configuration
output "azure_reply_url" {
  description = "Configure in Azure: Reply URL"
  value       = module.azure_ad.idp_acs_url
}

output "azure_identifier" {
  description = "Configure in Azure: Identifier (Entity ID)"
  value       = module.azure_ad.idp_audience
}
```

#### Complete Azure Configuration

1. **In Azure Portal**, update SAML settings:
   - Identifier (Entity ID): `terraform output azure_identifier`
   - Reply URL (ACS URL): `terraform output azure_reply_url`

2. **Configure Attribute Claims:**
   | Claim Name | Value |
   |------------|-------|
   | emailaddress | user.mail |
   | givenname | user.givenname |
   | surname | user.surname |

### Google Workspace Integration

```hcl
module "google_workspace" {
  source = "../../../modules/saml-federation"

  federation_mode = "sp"
  federation_name = "google-workspace"
  okta_org_name   = var.okta_org_name
  okta_base_url   = var.okta_base_url

  idp_name        = "Google Workspace"
  idp_issuer      = "https://accounts.google.com/o/saml2?idpid=${var.google_idp_id}"
  idp_sso_url     = "https://accounts.google.com/o/saml2/idp?idpid=${var.google_idp_id}"
  idp_certificate = file("${path.module}/certs/google.pem")

  provisioning_action = "AUTO"
  account_link_action = "AUTO"
  username_template   = "idpuser.email"
}
```

---

## JIT Provisioning

Just-In-Time (JIT) provisioning creates users in Okta when they first federate.

### Provisioning Actions

| Action | Description |
|--------|-------------|
| `AUTO` | Create user on first federation |
| `DISABLED` | User must exist (no creation) |
| `CALL_OUT` | Use inline hook for custom logic |

### Account Linking

| Action | Description |
|--------|-------------|
| `AUTO` | Match by email address |
| `DISABLED` | Always create new user |
| `CALL_OUT` | Use inline hook |

### Subject Matching

| Type | Description |
|------|-------------|
| `EMAIL` | Match by email (most common) |
| `USERNAME` | Match by username |
| `USERNAME_OR_EMAIL` | Try both |
| `CUSTOM_ATTRIBUTE` | Match by custom attribute |

### Example: Full JIT Configuration

```hcl
module "partner_federation" {
  source = "../../../modules/saml-federation"

  federation_mode = "sp"
  # ...

  # Create users automatically
  provisioning_action = "AUTO"

  # Link to existing users by email
  account_link_action = "AUTO"
  subject_match_type  = "EMAIL"

  # Username template
  username_template = "idpuser.email"

  # Make IdP the profile master
  profile_master = false

  # Assign to groups
  groups_action     = "ASSIGN"
  groups_assignment = [okta_group.partners.id]
}
```

---

## IdP Discovery & Routing

Route users to specific identity providers based on their email domain.

### How It Works

1. User enters email at Okta sign-in
2. Okta checks IdP discovery rules
3. If domain matches, redirect to external IdP
4. User authenticates with their IdP
5. Return to Okta with assertion

### Configuration

```hcl
# Get the default IdP discovery policy
data "okta_policy" "idp_discovery" {
  name = "Idp Discovery Policy"
  type = "IDP_DISCOVERY"
}

module "partner_federation" {
  source = "../../../modules/saml-federation"

  federation_mode = "sp"
  federation_name = "partner"
  # ...

  # Enable routing
  enable_routing_rule   = true
  routing_policy_id     = data.okta_policy.idp_discovery.id
  routing_domain_suffix = "@partner.com"
  routing_rule_priority = 1  # Lower = higher priority
}
```

### Multiple Routing Rules

```hcl
# Partner A
module "partner_a" {
  # ...
  routing_domain_suffix = "@partnera.com"
  routing_rule_priority = 1
}

# Partner B
module "partner_b" {
  # ...
  routing_domain_suffix = "@partnerb.com"
  routing_rule_priority = 2
}

# Azure AD for corporate
module "azure_ad" {
  # ...
  routing_domain_suffix = "@company.com"
  routing_rule_priority = 3
}
```

---

## Attribute Mapping

### Default Attributes

The module sends these attributes by default:

| Attribute | Value |
|-----------|-------|
| firstName | user.firstName |
| lastName | user.lastName |
| email | user.email |

### Custom Attributes

```hcl
module "federation" {
  # ...

  attribute_statements = [
    # Basic attributes
    {
      name   = "firstName"
      values = ["user.firstName"]
    },
    {
      name   = "lastName"
      values = ["user.lastName"]
    },
    {
      name   = "email"
      values = ["user.email"]
    },
    # Custom attributes
    {
      name   = "employeeNumber"
      values = ["user.employeeNumber"]
    },
    {
      name   = "department"
      values = ["user.department"]
    },
    {
      name   = "manager"
      values = ["user.manager"]
    },
    # Group membership
    {
      name         = "groups"
      type         = "GROUP"
      values       = []
      filter_type  = "REGEX"
      filter_value = ".*"  # All groups
    },
    # Filtered groups
    {
      name         = "awsRoles"
      type         = "GROUP"
      values       = []
      filter_type  = "STARTS_WITH"
      filter_value = "AWS_"  # Only AWS role groups
    },
  ]
}
```

### Attribute Namespaces

| Namespace | Use Case |
|-----------|----------|
| `urn:oasis:names:tc:SAML:2.0:attrname-format:unspecified` | Default, most compatible |
| `urn:oasis:names:tc:SAML:2.0:attrname-format:basic` | Simple string names |
| `urn:oasis:names:tc:SAML:2.0:attrname-format:uri` | URI-based names |

---

## Troubleshooting

### Common Issues

#### 1. "SAML assertion cannot be verified"

**Cause:** Certificate mismatch or invalid signature

**Fix:**
- Verify certificate is in PEM format
- Remove any headers/footers if needed
- Check signature algorithm matches (SHA-256 vs SHA-1)

```bash
# Verify certificate
openssl x509 -in cert.pem -text -noout
```

#### 2. "User not found"

**Cause:** Account linking failed

**Fix:**
- Enable JIT provisioning: `provisioning_action = "AUTO"`
- Check `subject_match_type` matches user attribute
- Verify `username_template` produces valid usernames

#### 3. "Access denied"

**Cause:** User not assigned to federation app

**Fix:**
- Check `assigned_group_ids` on IdP side
- Verify user is in assigned groups
- Check app status is ACTIVE

#### 4. "Invalid request"

**Cause:** ACS URL or audience mismatch

**Fix:**
- Verify ACS URL matches exactly (no trailing slash)
- Check audience restriction
- Compare metadata between orgs

#### 5. "Clock skew" error

**Cause:** Time difference between IdP and SP

**Fix:**
- Default `max_clock_skew` is 5 minutes
- Sync NTP on all servers
- Increase skew if needed (not recommended)

### Debug Commands

```bash
# Check IdP configuration
curl -s -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_ORG}.okta.com/api/v1/idps" | jq '.[] | {id, name, status}'

# Check SAML app
curl -s -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_ORG}.okta.com/api/v1/apps?filter=name+sw+%22saml%22" | jq

# Get IdP metadata
curl -s "https://${OKTA_ORG}.okta.com/api/v1/idps/${IDP_ID}/metadata.xml"

# Test IdP (returns test assertion)
curl -s -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_ORG}.okta.com/api/v1/idps/${IDP_ID}/credentials/keys"
```

### SAML Tracer

Use a browser extension to capture SAML traffic:

1. Install "SAML-tracer" browser extension
2. Initiate federation
3. Capture AuthnRequest and Response
4. Check for:
   - Correct ACS URL
   - Valid signature
   - Matching issuer
   - Proper attributes

---

## Security Considerations

### Best Practices

1. **Use SHA-256 signatures** (not SHA-1)
2. **Rotate certificates** before expiration
3. **Limit group access** on IdP side
4. **Disable unused IdPs** promptly
5. **Audit federation events** regularly

### Certificate Rotation

```hcl
# Prepare new certificate before rotation
variable "idp_certificate_next" {
  description = "Next certificate for rotation"
  type        = string
  default     = ""
}

# During rotation, both certs should be valid
# Update idp_certificate when ready
```

### Audit Logging

Monitor these System Log events:

| Event Type | Description |
|------------|-------------|
| `user.authentication.sso` | Successful SSO |
| `user.authentication.auth_via_IDP` | IdP authentication |
| `user.session.start` | Session created |

```bash
# Query federation events
curl -s -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_ORG}.okta.com/api/v1/logs?filter=eventType+eq+%22user.authentication.sso%22"
```

---

## Related Documentation

- [Module README](../modules/saml-federation/README.md)
- [AI Prompt Template](../ai-assisted/prompts/setup_saml_federation.md)
- [Okta SAML IdP API](https://developer.okta.com/docs/reference/api/idps/)
- [Okta SAML App API](https://developer.okta.com/docs/reference/api/apps/)

---

**Last Updated:** 2026-01-06
