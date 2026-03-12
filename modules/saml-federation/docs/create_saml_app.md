# Create SAML Application Prompt Template

Use this template to generate Terraform code for SAML 2.0 applications in Okta.

## Context to Provide

Before using this prompt, gather:
1. Application name and purpose
2. SP (Service Provider) details:
   - SSO URL (ACS URL)
   - Entity ID / Audience
   - Name ID format preference
3. Attribute statements needed
4. Groups to assign
5. Signature/encryption requirements

## Prompt Template

```
Create a SAML 2.0 application in Okta with these specifications:

## Application Details
- Name: [App Name]
- Description: [Purpose of the app]

## Service Provider Configuration
- SSO URL (ACS): [https://app.example.com/sso/saml]
- Audience URI (Entity ID): [https://app.example.com]
- Default Relay State: [optional - redirect URL after SSO]

## Name ID Configuration
- Format: [emailAddress | unspecified | persistent | transient]
- Value: [user.email | user.login | custom expression]

## Attribute Statements
[List attributes the SP needs, e.g.:]
- email → user.email
- firstName → user.firstName
- lastName → user.lastName
- department → user.department
- groups → (group membership filter)

## Group Attribute Statement (if needed)
- Attribute name: groups
- Filter type: [REGEX | STARTS_WITH | EQUALS | CONTAINS]
- Filter value: [pattern to match groups]

## Signature Settings
- Response signed: [yes/no]
- Assertion signed: [yes/no]
- Signature algorithm: [RSA_SHA256 | RSA_SHA1]
- Digest algorithm: [SHA256 | SHA1]

## Group Assignments
Assign these groups to the application:
- [Group 1 name]
- [Group 2 name]

## Additional Requirements
- [Any specific requirements like honor_force_authn, inline_hook, etc.]

Generate complete Terraform code including:
1. okta_app_saml resource
2. Attribute statements
3. Group attribute statement (if needed)
4. okta_app_group_assignments for group access
5. Outputs for SP configuration (metadata URL, certificate, SSO URL)
```

## Example: Corporate ServiceNow

```
Create a SAML 2.0 application in Okta with these specifications:

## Application Details
- Name: ServiceNow Production
- Description: Corporate IT service management platform

## Service Provider Configuration
- SSO URL (ACS): https://company.service-now.com/navpage.do
- Audience URI (Entity ID): https://company.service-now.com
- Default Relay State: (none)

## Name ID Configuration
- Format: emailAddress
- Value: user.email

## Attribute Statements
- email → user.email
- first_name → user.firstName
- last_name → user.lastName
- title → user.title
- department → user.department
- employee_number → user.employeeNumber

## Group Attribute Statement
- Attribute name: groups
- Filter type: STARTS_WITH
- Filter value: ServiceNow_

## Signature Settings
- Response signed: yes
- Assertion signed: yes
- Signature algorithm: RSA_SHA256
- Digest algorithm: SHA256

## Group Assignments
Assign these groups to the application:
- IT Support
- IT Administrators
- All Employees

Generate complete Terraform code.
```

## Expected Output Structure

The AI should generate:

```hcl
# =============================================================================
# SAML APPLICATION: [App Name]
# =============================================================================

resource "okta_app_saml" "app_name" {
  label             = "App Name"
  status            = "ACTIVE"

  # SSO Configuration
  sso_url           = "https://..."
  recipient         = "https://..."
  destination       = "https://..."
  audience          = "https://..."

  # Name ID
  subject_name_id_template = "$${user.email}"
  subject_name_id_format   = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"

  # Signature Settings
  response_signed          = true
  assertion_signed         = true
  signature_algorithm      = "RSA_SHA256"
  digest_algorithm         = "SHA256"

  # Attribute Statements
  attribute_statements {
    name   = "email"
    type   = "EXPRESSION"
    values = ["user.email"]
  }

  # Group Attribute Statement
  attribute_statements {
    name         = "groups"
    type         = "GROUP"
    filter_type  = "STARTS_WITH"
    filter_value = "ServiceNow_"
  }
}

# Group Assignments
resource "okta_app_group_assignments" "app_name_groups" {
  app_id = okta_app_saml.app_name.id

  group {
    id = okta_group.it_support.id
  }
  group {
    id = okta_group.it_administrators.id
  }
}

# Outputs for SP Configuration
output "app_name_metadata_url" {
  value = "https://${var.okta_org_name}.${var.okta_base_url}/app/${okta_app_saml.app_name.id}/sso/saml/metadata"
}

output "app_name_sso_url" {
  value = okta_app_saml.app_name.http_post_binding
}
```

## Post-Generation Steps

1. **Validate the code:**
   ```bash
   terraform fmt
   terraform validate
   ```

2. **Review attribute mappings:**
   - Verify all required attributes are included
   - Check expression syntax uses `$$` escaping

3. **Plan and apply:**
   ```bash
   terraform plan
   terraform apply
   ```

4. **Configure the Service Provider:**
   - Download metadata from Okta: `terraform output app_name_metadata_url`
   - Or manually configure with SSO URL and certificate

5. **Test SSO:**
   - Assign a test user
   - Initiate SP-initiated or IdP-initiated SSO
   - Verify attributes are passed correctly

## Common Variations

### SAML with Custom Authentication Context
```hcl
authn_context_class_ref = "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport"
```

### SAML with Inline Hook
```hcl
inline_hook_id = okta_inline_hook.saml_hook.id
```

### SAML with Honor Force Authn
```hcl
honor_force_authn = true
```

### SAML with SP-Initiated Login
```hcl
sp_issuer = "https://sp.example.com"
```

## See Also

- [create_app.md](create_app.md) - OAuth/OIDC application template
- [oig_setup.md](oig_setup.md) - Entitlement bundles for apps
- [Okta SAML Documentation](https://developer.okta.com/docs/concepts/saml/)
