# SAML Federation Module

Terraform module for configuring SAML federation between Okta organizations or with external identity providers.

## Features

- **Dual Mode Operation**: Supports both SP (receive assertions) and IdP (send assertions) modes
- **Cross-Org Coordination**: Uses `terraform_remote_state` for automatic configuration exchange
- **Flexible Configuration**: Remote state values with variable fallback via `coalesce()`
- **JIT Provisioning**: Full control over user provisioning and account linking
- **IdP Discovery**: Optional routing rules based on email domain
- **External IdP Support**: Works with Azure AD, Google Workspace, and other SAML IdPs

## Quick Start

### Okta-to-Okta Federation (Recommended)

This example shows hub-and-spoke federation using remote state for automatic configuration.

**Hub Organization (IdP Mode):**

```hcl
module "federation_to_spoke" {
  source = "../../modules/saml-federation"

  federation_mode = "idp"
  federation_name = "spoke-org"
  okta_org_name   = "hub-org"
  okta_base_url   = "okta.com"

  # Read SP configuration from spoke's Terraform state
  use_remote_state = true
  remote_state_config = {
    bucket = "my-terraform-state"
    key    = "okta/spoke-org/terraform.tfstate"
    region = "us-east-1"
  }

  # Assign groups that can federate
  assigned_group_ids = [okta_group.employees.id]
}
```

**Spoke Organization (SP Mode):**

```hcl
module "federation_from_hub" {
  source = "../../modules/saml-federation"

  federation_mode = "sp"
  federation_name = "hub-org"
  okta_org_name   = "spoke-org"
  okta_base_url   = "okta.com"

  # Read IdP configuration from hub's Terraform state
  use_remote_state = true
  remote_state_config = {
    bucket = "my-terraform-state"
    key    = "okta/hub-org/terraform.tfstate"
    region = "us-east-1"
  }

  # JIT provisioning settings
  provisioning_action = "AUTO"
  account_link_action = "AUTO"
}
```

### External IdP (Azure AD)

**Okta as SP, Azure AD as IdP:**

```hcl
module "azure_ad_federation" {
  source = "../../modules/saml-federation"

  federation_mode = "sp"
  federation_name = "azure-ad"
  okta_org_name   = "my-okta-org"
  okta_base_url   = "okta.com"

  # Azure AD SAML configuration (from Azure portal)
  idp_name        = "Azure AD"
  idp_issuer      = "https://sts.windows.net/TENANT_ID/"
  idp_sso_url     = "https://login.microsoftonline.com/TENANT_ID/saml2"
  idp_certificate = file("${path.module}/azure-ad-cert.pem")

  # JIT provisioning
  provisioning_action = "AUTO"
  account_link_action = "AUTO"
  username_template   = "idpuser.email"

  # Optional: Route users with @company.com to Azure AD
  enable_routing_rule   = true
  routing_policy_id     = data.okta_policy.idp_discovery.id
  routing_domain_suffix = "@company.com"
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.9.0 |
| okta | >= 6.4.0, < 7.0.0 |

## Inputs

### Required Variables

| Name | Description | Type |
|------|-------------|------|
| `federation_mode` | Federation mode: 'sp' or 'idp' | `string` |
| `federation_name` | Name for federation resources | `string` |
| `okta_org_name` | This organization's Okta subdomain | `string` |
| `okta_base_url` | Okta base URL domain (default: okta.com) | `string` |

### Remote State Configuration

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `use_remote_state` | Enable terraform_remote_state | `bool` | `false` |
| `remote_state_backend` | Backend type: 's3' or 'local' | `string` | `"s3"` |
| `remote_state_config` | Backend configuration | `map(string)` | `{}` |

### SP Mode Variables

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `idp_name` | Display name for external IdP | `string` | `""` |
| `idp_issuer` | SAML issuer of external IdP | `string` | `""` |
| `idp_sso_url` | SSO URL of external IdP | `string` | `""` |
| `idp_certificate` | X.509 certificate (PEM format) | `string` | `""` |

### IdP Mode Variables

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `app_label` | SAML app label | `string` | `""` |
| `sp_org_name` | SP organization's Okta subdomain | `string` | `""` |
| `sp_base_url` | SP organization's base URL | `string` | `""` |
| `sp_idp_id` | SP's IdP resource ID | `string` | `""` |
| `sp_acs_url` | SP's ACS URL (non-Okta SPs) | `string` | `""` |
| `sp_audience` | SP's audience/entity ID | `string` | `""` |
| `attribute_statements` | SAML attributes to send | `list(object)` | `[]` |
| `assigned_group_ids` | Groups to assign to app | `list(string)` | `[]` |

### JIT Provisioning (SP Mode)

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `provisioning_action` | AUTO, DISABLED, or CALL_OUT | `string` | `"AUTO"` |
| `account_link_action` | AUTO, DISABLED, or CALL_OUT | `string` | `"AUTO"` |
| `groups_action` | NONE, SYNC, APPEND, or ASSIGN | `string` | `"NONE"` |
| `groups_attribute` | Attribute with group info | `string` | `""` |
| `groups_assignment` | Default groups for users | `list(string)` | `[]` |
| `profile_master` | IdP is profile master | `bool` | `false` |
| `subject_match_type` | USERNAME, EMAIL, etc. | `string` | `"EMAIL"` |
| `username_template` | Okta EL template | `string` | `"idpuser.email"` |

### Routing Rules (SP Mode)

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `enable_routing_rule` | Enable IdP discovery rule | `bool` | `false` |
| `routing_policy_id` | IdP discovery policy ID | `string` | `""` |
| `routing_domain_suffix` | Email domain to route | `string` | `""` |
| `routing_rule_priority` | Rule priority | `number` | `1` |

### Signature Settings

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `request_signature_algorithm` | SHA-256 or SHA-1 | `string` | `"SHA-256"` |
| `response_signature_algorithm` | RSA_SHA256 or RSA_SHA1 | `string` | `"RSA_SHA256"` |
| `assertion_signed` | Sign assertions | `bool` | `true` |
| `digest_algorithm` | SHA256 or SHA1 | `string` | `"SHA256"` |

## Outputs

### SP Mode Outputs

| Name | Description |
|------|-------------|
| `idp_id` | IdP resource ID |
| `idp_acs_url` | Assertion Consumer Service URL |
| `idp_audience` | Audience restriction / Entity ID |
| `idp_metadata_url` | IdP metadata URL |

### IdP Mode Outputs

| Name | Description |
|------|-------------|
| `app_id` | SAML app ID |
| `federation_issuer` | SAML issuer / Entity ID |
| `federation_sso_url` | SSO URL |
| `federation_certificate` | X.509 signing certificate |
| `federation_metadata_url` | SAML metadata URL |

### Shared Outputs

| Name | Description |
|------|-------------|
| `okta_org_name` | Organization subdomain |
| `okta_base_url` | Organization base URL |
| `federation_config` | Complete configuration object |
| `status` | Resource creation summary |

## Use Cases

### 1. Hub-and-Spoke (Okta-to-Okta)

Central identity hub authenticates users for multiple spoke organizations.

```
┌─────────────┐     SAML      ┌─────────────┐
│  Hub Org    │ ────────────► │  Spoke 1    │
│  (IdP Mode) │               │  (SP Mode)  │
└─────────────┘               └─────────────┘
       │
       │        SAML          ┌─────────────┐
       └────────────────────► │  Spoke 2    │
                              │  (SP Mode)  │
                              └─────────────┘
```

### 2. Partner Federation

Allow users from partner organizations to access your applications.

```hcl
module "partner_federation" {
  source = "../../modules/saml-federation"

  federation_mode = "sp"
  federation_name = "partner-company"
  okta_org_name   = var.okta_org_name
  okta_base_url   = var.okta_base_url

  idp_name   = "Partner Company"
  idp_issuer = "https://partner-idp.example.com"
  # ... other partner IdP configuration

  # Route partner users to their IdP
  enable_routing_rule   = true
  routing_domain_suffix = "@partner-company.com"
}
```

### 3. M&A Integration

Temporary federation during merger/acquisition before full migration.

### 4. Development/Production Separation

Federate dev org users to production for testing without separate accounts.

## Cross-Org Bootstrap Workflow

When setting up Okta-to-Okta federation with remote state:

### Phase 1: Initial Deployment

1. **SP Organization First** - Deploy with empty IdP config:
   ```hcl
   module "federation" {
     federation_mode  = "sp"
     use_remote_state = false  # IdP not deployed yet
     # SP outputs will be available for IdP
   }
   ```

2. **IdP Organization** - Deploy reading SP state:
   ```hcl
   module "federation" {
     federation_mode  = "idp"
     use_remote_state = true
     remote_state_config = {
       # Points to SP's state
     }
   }
   ```

### Phase 2: Complete Federation

3. **Update SP** - Enable remote state to read IdP config:
   ```hcl
   module "federation" {
     federation_mode  = "sp"
     use_remote_state = true  # Now reads IdP config
     remote_state_config = {
       # Points to IdP's state
     }
   }
   ```

4. **Re-apply SP** - IdP will now be fully configured.

## Troubleshooting

### Common Issues

**1. "Missing IdP configuration"**
- Ensure remote state bucket/key is correct
- Verify IdP org has been deployed first
- Check that outputs match expected names

**2. "Invalid signature"**
- Verify certificate is in PEM format
- Check signature algorithm matches between IdP and SP
- Ensure no extra whitespace in certificate

**3. "User not provisioned"**
- Check `provisioning_action = "AUTO"`
- Verify `username_template` produces valid username
- Ensure `subject_match_type` matches user attribute

**4. "Access denied" after federation**
- Assign appropriate groups to federated app (IdP mode)
- Check app assignment in SP organization
- Verify routing rule is active (SP mode)

### Debug Commands

```bash
# Check IdP configuration (SP side)
curl -s -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_ORG}.okta.com/api/v1/idps" | jq

# Check SAML app (IdP side)
curl -s -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_ORG}.okta.com/api/v1/apps?filter=name+sw+%22saml%22" | jq

# Get metadata
curl -s "https://${OKTA_ORG}.okta.com/api/v1/idps/${IDP_ID}/metadata.xml"
```

## Related Documentation

- [SAML Federation Guide](../../docs/SAML_FEDERATION.md) - Comprehensive setup guide
- [Okta SAML IdP Documentation](https://developer.okta.com/docs/reference/api/idps/)
- [Okta SAML App Documentation](https://developer.okta.com/docs/reference/api/apps/)

## Authors

Okta Terraform Demo Template Contributors

## License

MIT License
