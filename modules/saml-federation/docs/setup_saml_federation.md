# AI Prompt: Set Up SAML Federation

Use this prompt to generate Terraform code for SAML federation between Okta organizations or with external identity providers.

---

## Instructions for AI

You are a Terraform expert helping configure SAML federation. Generate complete, working Terraform code using the `saml-federation` module.

### Context Files to Include

Before using this prompt, provide these context files to the AI:

1. `ai-assisted/context/repository_structure.md` - Project structure
2. `ai-assisted/context/okta_resource_guide.md` - Okta resources reference
3. `modules/saml-federation/README.md` - Module documentation

---

## Prompt Template

```
I need to set up SAML federation with the following requirements:

## Federation Type
- [ ] Okta-to-Okta (hub-and-spoke)
- [ ] External IdP to Okta (Azure AD, Google, etc.)
- [ ] Okta to External SP

## My Organization Details
- Okta org name: [e.g., dev-12345]
- Okta base URL: [okta.com / oktapreview.com]
- Environment directory: [e.g., environments/myorg]

## Partner/External IdP Details (if applicable)
- Partner org name: [e.g., partner-org]
- Partner base URL: [okta.com / oktapreview.com]
- For external IdP:
  - IdP name: [e.g., Azure AD, Google Workspace]
  - IdP issuer/entity ID: [URL]
  - IdP SSO URL: [URL]
  - Certificate file location: [path to PEM file]

## State Backend (for Okta-to-Okta)
- [ ] Using shared S3 backend
  - Bucket name: [e.g., my-terraform-state]
  - State key pattern: [e.g., okta/{env}/terraform.tfstate]
  - Region: [e.g., us-east-1]
- [ ] Manual configuration (no remote state)

## User Provisioning (SP side)
- [ ] JIT Provisioning enabled (AUTO)
- [ ] No provisioning (DISABLED)
- Profile master: [Yes/No]
- Username template: [e.g., idpuser.email]

## Routing (SP side, optional)
- [ ] Route by email domain
  - Domain suffix: [e.g., @partner.com]
  - IdP discovery policy ID: [from Okta]

## Groups (IdP side)
- Which groups should have access to federate:
  - [Group name 1]
  - [Group name 2]

## Attribute Statements (IdP side, optional)
- [ ] Use defaults (firstName, lastName, email)
- [ ] Custom attributes:
  - Attribute name → Okta expression
  - [e.g., department → user.department]

Please generate:
1. Complete Terraform code for my organization
2. If Okta-to-Okta, code for both organizations
3. Any supporting resources (groups, policies)
4. Step-by-step deployment instructions
```

---

## Example Outputs

### Example 1: Okta-to-Okta with Remote State

**Hub Organization (upstream/terraform/federation.tf):**

```hcl
# =============================================================================
# SAML Federation - Hub to Spoke
# =============================================================================
# This org acts as IdP, sending assertions to the spoke org
# =============================================================================

module "federation_to_spoke" {
  source = "../../modules/saml-federation"

  # Mode and identity
  federation_mode = "idp"
  federation_name = "spoke-org"
  okta_org_name   = var.okta_org_name
  okta_base_url   = var.okta_base_url

  # Read SP configuration from spoke's state
  use_remote_state = true
  remote_state_config = {
    bucket = "okta-terraform-state"
    key    = "okta/spoke/terraform.tfstate"
    region = "us-east-1"
  }

  # Groups that can federate
  assigned_group_ids = [
    okta_group.employees.id,
    okta_group.contractors.id,
  ]

  # Custom attributes
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
    {
      name   = "department"
      values = ["user.department"]
    },
    {
      name   = "groups"
      type   = "GROUP"
      values = []
      filter_type  = "REGEX"
      filter_value = ".*"
    },
  ]
}

# Output for spoke org to reference
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
```

**Spoke Organization (spoke/terraform/federation.tf):**

```hcl
# =============================================================================
# SAML Federation - Receive from Hub
# =============================================================================
# This org acts as SP, receiving assertions from the hub org
# =============================================================================

module "federation_from_hub" {
  source = "../../modules/saml-federation"

  # Mode and identity
  federation_mode = "sp"
  federation_name = "hub-org"
  okta_org_name   = var.okta_org_name
  okta_base_url   = var.okta_base_url

  # Read IdP configuration from hub's state
  use_remote_state = true
  remote_state_config = {
    bucket = "okta-terraform-state"
    key    = "okta/hub/terraform.tfstate"
    region = "us-east-1"
  }

  # JIT provisioning
  provisioning_action = "AUTO"
  account_link_action = "AUTO"
  username_template   = "idpuser.email"

  # Group sync
  groups_action    = "ASSIGN"
  groups_assignment = [okta_group.federated_users.id]
}

# Output for hub org to reference
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

### Example 2: Azure AD to Okta

```hcl
# =============================================================================
# SAML Federation - Azure AD
# =============================================================================
# Receives assertions from Azure AD for corporate users
# =============================================================================

# IdP discovery policy (get existing or create)
data "okta_policy" "idp_discovery" {
  name = "Idp Discovery Policy"
  type = "IDP_DISCOVERY"
}

# Azure AD federation
module "azure_ad_federation" {
  source = "../../modules/saml-federation"

  federation_mode = "sp"
  federation_name = "azure-ad"
  okta_org_name   = var.okta_org_name
  okta_base_url   = var.okta_base_url

  # Azure AD configuration (from Azure portal)
  idp_name   = "Azure AD - Corporate"
  idp_issuer = "https://sts.windows.net/${var.azure_tenant_id}/"
  idp_sso_url = "https://login.microsoftonline.com/${var.azure_tenant_id}/saml2"
  idp_certificate = file("${path.module}/certs/azure-ad-signing.pem")

  # JIT provisioning
  provisioning_action = "AUTO"
  account_link_action = "AUTO"
  profile_master      = false
  username_template   = "idpuser.email"

  # Route corporate users to Azure AD
  enable_routing_rule   = true
  routing_policy_id     = data.okta_policy.idp_discovery.id
  routing_domain_suffix = "@company.com"
  routing_rule_priority = 1
}

output "azure_ad_acs_url" {
  description = "Configure this in Azure AD as the Reply URL"
  value       = module.azure_ad_federation.idp_acs_url
}

output "azure_ad_entity_id" {
  description = "Configure this in Azure AD as the Identifier"
  value       = module.azure_ad_federation.idp_audience
}
```

---

## Deployment Instructions

### Okta-to-Okta Bootstrap

1. **Deploy SP first** (creates IdP resource, outputs ACS URL):
   ```bash
   cd environments/spoke/terraform
   terraform init
   terraform apply
   # Note: IdP won't have full config yet
   ```

2. **Deploy IdP** (reads SP outputs, creates SAML app):
   ```bash
   cd environments/hub/terraform
   terraform init
   terraform apply
   ```

3. **Re-apply SP** (now reads IdP outputs, completes config):
   ```bash
   cd environments/spoke/terraform
   terraform apply
   ```

### External IdP (Azure AD)

1. **Create Enterprise Application in Azure:**
   - Type: Non-gallery SAML application
   - Download signing certificate (Base64)

2. **Deploy Okta SP:**
   ```bash
   cd environments/myorg/terraform
   terraform init
   terraform apply
   ```

3. **Configure Azure with Okta outputs:**
   - Reply URL: `terraform output azure_ad_acs_url`
   - Identifier: `terraform output azure_ad_entity_id`

4. **Test federation:**
   - Access Okta with user@company.com
   - Should redirect to Azure AD

---

## Common Customizations

### Custom Attribute Mapping

```hcl
attribute_statements = [
  {
    name   = "employeeNumber"
    values = ["user.employeeNumber"]
  },
  {
    name   = "costCenter"
    values = ["user.costCenter"]
  },
  {
    name   = "memberOf"
    type   = "GROUP"
    values = []
    filter_type  = "STARTS_WITH"
    filter_value = "AWS_"
  },
]
```

### Multiple Partner Organizations

```hcl
# Partner 1
module "federation_partner1" {
  source          = "../../modules/saml-federation"
  federation_mode = "sp"
  federation_name = "partner1"
  # ...
}

# Partner 2
module "federation_partner2" {
  source          = "../../modules/saml-federation"
  federation_mode = "sp"
  federation_name = "partner2"
  # ...
}
```

---

## Troubleshooting Tips

1. **Certificate format:** Must be PEM, remove headers if needed
2. **Chicken-and-egg:** SP must deploy first in Okta-to-Okta
3. **Routing priority:** Lower number = higher priority
4. **Username mismatch:** Ensure template produces valid Okta username
