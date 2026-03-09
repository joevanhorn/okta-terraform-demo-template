# Okta Terraform Provider - Coverage & Analysis

**Last Updated:** 2025-11-19
**Provider Version:** v6.4.0
**Purpose:** Track which Okta features are available in Terraform vs API-only vs Manual

---

## Summary

The Okta Terraform Provider (v6.4.0) includes **103 resources** and **47 data sources** across 28 categories. Key highlights:

- **OIG support** added in v6.0.0-v6.4.0: 10 resources and 13 data sources for entitlements, reviews, requests, and approvals
- **3 CRITICAL gaps** remain: resource owners, governance labels, and risk rules (SOD policies) -- managed via Python scripts
- **95% OIG coverage**, 100% Users & Groups, 90% Applications, 95% Auth & Policies
- **~37% of resources** lack comprehensive examples in the demo template

### OIG Resources Added in v6.x

| Resource | Version | Purpose |
|----------|---------|---------|
| `okta_campaign` | v6.0.0 | Access review campaigns |
| `okta_entitlement` | v6.0.0 | Individual entitlements |
| `okta_entitlement_bundle` | v6.2.0 | Entitlement bundles |
| `okta_review` | v6.1.0 | Access reviews |
| `okta_principal_entitlements` | v6.1.0 | Principal entitlement assignments |
| `okta_request_condition` | v6.1.0 | Access request conditions |
| `okta_request_sequence` | v6.1.0 | Approval workflows |
| `okta_request_setting_organization` | v6.1.0 | Org-level request settings |
| `okta_request_setting_resource` | v6.1.0 | Resource-level request settings |
| `okta_request_v2` | v6.1.0 | Access requests |

---

## Coverage Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Fully supported in Terraform Provider |
| ⚠️ | Partially supported (limitations exist) |
| 🔧 | Available via Python API scripts |
| 👤 | Manual management in Okta Admin UI only |
| ❌ | Not available in provider or API |

---

## Identity Governance (OIG) Features

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Entitlement Bundles (Definitions)** | ✅ `okta_entitlement_bundle` | ✅ `oig_entitlements.tf` | Bundle definitions only | - |
| **Entitlement Bundles (Assignments)** | 👤 Manual Only | 👤 Okta Admin UI | WHO has bundles - NOT in Terraform | HIGH |
| **Individual Entitlements** | ✅ `okta_entitlement` | ✅ Auto-generated | Low-level entitlements | - |
| **Principal Entitlements** | ✅ `okta_principal_entitlements` | ✅ Data source | Query assignments | - |
| **Access Review Campaigns** | ✅ `okta_campaign` | ✅ `oig_reviews.tf` | Full CRUD support | - |
| **Access Reviews** | ✅ `okta_review` | ✅ `oig_reviews.tf` | Campaign-based reviews | - |
| **Approval Workflows** | ✅ `okta_request_sequence` | ✅ `oig_request_sequences.tf` | Multi-step approvals | - |
| **Catalog Entries** | ✅ `okta_catalog_entry_default` | ✅ Data source | Self-service catalog | - |
| **Request Settings (Org)** | ✅ `okta_request_setting_organization` | ✅ `oig_request_settings.tf` | Org-wide settings | - |
| **Request Settings (Resource)** | ✅ `okta_request_setting_resource` | ✅ `oig_request_settings.tf` | Per-resource settings | - |
| **Access Requests** | ✅ `okta_request_v2` | ✅ Data source | Query requests | - |
| **Request Conditions** | ✅ `okta_request_condition` | ✅ `oig_request_settings.tf` | Conditional access | - |
| **Resource Owners** | 🔧 `scripts/apply_resource_owners.py` | 🔧 `config/owner_mappings.json` | NOT in provider | **CRITICAL** |
| **Governance Labels** | 🔧 `scripts/apply_admin_labels.py` | 🔧 `config/label_mappings.json` | NOT in provider | **CRITICAL** |
| **Risk Rules (SOD Policies)** | 🔧 `scripts/apply_risk_rules.py` | 🔧 `config/risk_rules.json` | NOT in provider | **CRITICAL** |

---

## Applications

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **OAuth 2.0 Apps** | ✅ `okta_app_oauth` | ✅ Examples available | Full support | - |
| **SAML Apps** | ✅ `okta_app_saml` | ✅ Examples available | Full support | - |
| **SWA Apps** | ✅ `okta_app_swa` | ✅ Examples available | Template-based | - |
| **Bookmark Apps** | ✅ `okta_app_bookmark` | ✅ Examples available | Simple links | - |
| **Basic Auth Apps** | ✅ `okta_app_basic_auth` | ✅ Examples available | HTTP Basic | - |
| **Auto Login Apps** | ✅ `okta_app_auto_login` | ✅ Examples available | Auto-submit forms | - |
| **Three-Field Apps** | ✅ `okta_app_three_field` | ✅ Examples available | Extra field support | - |
| **Secure Password Store** | ✅ `okta_app_secure_password_store` | ⚠️ Limited examples | SWA variant | LOW |
| **Shared Credentials** | ✅ `okta_app_shared_credentials` | ⚠️ Limited examples | Shared login | LOW |
| **App Logos** | ❌ Not Available | 👤 Manual Only | Logo upload | MEDIUM |
| **App Provisioning Connection** | ❌ Not Available | 👤 Manual Only | SCIM config | **HIGH** |
| **App Group Assignments** | ✅ `okta_app_group_assignment` | ✅ Examples available | Single assignment | - |
| **App Group Assignments (Bulk)** | ✅ `okta_app_group_assignments` | ✅ Examples available | Multiple assignments | - |
| **App User Assignments** | ✅ `okta_app_user` | ✅ Examples available | Individual users | - |
| **App Sign-On Policies** | ✅ `okta_app_signon_policy` | ✅ Examples available | App-level policies | - |
| **App Sign-On Policy Rules** | ✅ `okta_app_signon_policy_rule` | ✅ Examples available | Conditional access | - |
| **OAuth API Scopes** | ✅ `okta_app_oauth_api_scope` | ✅ Examples available | Grant scopes | - |
| **OAuth Redirect URIs** | ✅ `okta_app_oauth_redirect_uri` | ✅ Examples available | Callback URLs | - |
| **OAuth Post Logout URIs** | ✅ `okta_app_oauth_post_logout_redirect_uri` | ✅ Examples available | Logout URLs | - |
| **OAuth Role Assignments** | ✅ `okta_app_oauth_role_assignment` | ⚠️ Limited examples | Admin roles | LOW |

---

## Users & Groups

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Users** | ✅ `okta_user` | ✅ `users.tf` | Full CRUD | - |
| **User Types** | ✅ `okta_user_type` | ⚠️ Limited examples | Custom types | LOW |
| **User Base Schema** | ✅ `okta_user_base_schema_property` | ⚠️ Limited examples | Modify base attrs | LOW |
| **User Custom Schema** | ✅ `okta_user_custom_schema_property` | ✅ Examples available | Custom attributes | - |
| **User Admin Roles** | ✅ `okta_user_admin_roles` | ⚠️ Limited examples | Assign admin roles | LOW |
| **User Group Memberships** | ✅ `okta_user_group_memberships` | ✅ Examples available | Bulk group assignment | - |
| **User Factor Question** | ✅ `okta_user_factor_question` | ⚠️ Limited examples | Security questions | LOW |
| **Groups** | ✅ `okta_group` | ✅ `groups.tf` | Full CRUD | - |
| **Group Memberships** | ✅ `okta_group_memberships` | ✅ Examples available | Bulk user assignment | - |
| **Group Owners** | ✅ `okta_group_owner` | ⚠️ Limited examples | Group ownership | MEDIUM |
| **Group Rules** | ✅ `okta_group_rule` | ✅ Examples available | Dynamic groups | - |
| **Group Roles** | ✅ `okta_group_role` | ⚠️ Limited examples | Admin roles | LOW |
| **Group Custom Schema** | ✅ `okta_group_custom_schema_property` | ⚠️ Limited examples | Custom attributes | LOW |

---

## Authentication & Authorization

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Auth Servers** | ✅ `okta_auth_server` | ✅ Examples available | Custom AS | - |
| **Auth Server Default** | ✅ `okta_auth_server_default` | ⚠️ Limited examples | Default AS config | LOW |
| **Auth Server Claims** | ✅ `okta_auth_server_claim` | ✅ Examples available | Custom claims | - |
| **Auth Server Default Claims** | ✅ `okta_auth_server_claim_default` | ⚠️ Limited examples | Modify default claims | LOW |
| **Auth Server Scopes** | ✅ `okta_auth_server_scope` | ✅ Examples available | Custom scopes | - |
| **Auth Server Policies** | ✅ `okta_auth_server_policy` | ✅ Examples available | Access policies | - |
| **Auth Server Policy Rules** | ✅ `okta_auth_server_policy_rule` | ✅ Examples available | Policy rules | - |
| **Authenticators** | ✅ `okta_authenticator` | ⚠️ Limited examples | MFA config | MEDIUM |
| **MFA Factors** | ✅ `okta_factor` | ⚠️ Limited examples | Factor config | MEDIUM |
| **TOTP Factors** | ✅ `okta_factor_totp` | ⚠️ Limited examples | TOTP config | LOW |

---

## Policies

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Sign-On Policies** | ✅ `okta_policy_sign_on` | ✅ Examples available | Global sign-on | - |
| **Sign-On Policy Rules** | ✅ `okta_policy_rule_sign_on` | ✅ Examples available | Conditional access | - |
| **MFA Policies** | ✅ `okta_policy_mfa` | ✅ Examples available | MFA requirements | - |
| **MFA Policy Default** | ✅ `okta_policy_mfa_default` | ⚠️ Limited examples | Default MFA policy | LOW |
| **MFA Policy Rules** | ✅ `okta_policy_rule_mfa` | ✅ Examples available | MFA rules | - |
| **Password Policies** | ✅ `okta_policy_password` | ✅ Examples available | Password requirements | - |
| **Password Policy Default** | ✅ `okta_policy_password_default` | ⚠️ Limited examples | Default password policy | LOW |
| **Password Policy Rules** | ✅ `okta_policy_rule_password` | ✅ Examples available | Password rules | - |
| **Profile Enrollment Policies** | ✅ `okta_policy_profile_enrollment` | ⚠️ Limited examples | Self-service registration | MEDIUM |
| **Profile Enrollment Apps** | ✅ `okta_policy_profile_enrollment_apps` | ⚠️ Limited examples | App-level enrollment | MEDIUM |
| **Profile Enrollment Rules** | ✅ `okta_policy_rule_profile_enrollment` | ⚠️ Limited examples | Enrollment rules | MEDIUM |
| **IdP Discovery Policies** | ✅ Implied in rules | ✅ Examples available | Routing rules | - |
| **IdP Discovery Rules** | ✅ `okta_policy_rule_idp_discovery` | ✅ Examples available | IdP routing | - |
| **Session Policies** | ❌ Not Available | 👤 Manual Only | Global session config | MEDIUM |
| **Device Assurance (Android)** | ✅ `okta_policy_device_assurance_android` | ⚠️ Limited examples | Device trust | MEDIUM |
| **Device Assurance (ChromeOS)** | ✅ `okta_policy_device_assurance_chromeos` | ⚠️ Limited examples | Device trust | MEDIUM |
| **Device Assurance (iOS)** | ✅ `okta_policy_device_assurance_ios` | ⚠️ Limited examples | Device trust | MEDIUM |
| **Device Assurance (macOS)** | ✅ `okta_policy_device_assurance_macos` | ⚠️ Limited examples | Device trust | MEDIUM |
| **Device Assurance (Windows)** | ✅ `okta_policy_device_assurance_windows` | ⚠️ Limited examples | Device trust | MEDIUM |

---

## Identity Providers

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **OIDC IdP** | ✅ `okta_idp_oidc` | ✅ Examples available | OpenID Connect | - |
| **SAML IdP** | ✅ `okta_idp_saml` | ✅ Examples available | SAML 2.0 | - |
| **SAML IdP Keys** | ✅ `okta_idp_saml_key` | ⚠️ Limited examples | Signing certificates | LOW |
| **Social IdP** | ✅ `okta_idp_social` | ✅ Examples available | Google, Facebook, etc. | - |

---

## Organization & Settings

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Org Configuration** | ✅ `okta_org_configuration` | ⚠️ Limited examples | Global org settings | MEDIUM |
| **Org Support** | ✅ `okta_org_support` | ⚠️ Limited examples | Support settings | LOW |
| **Org Contacts** | ❌ Not Available | 👤 Manual Only | Technical/billing | LOW |
| **Rate Limiting** | ✅ `okta_rate_limiting` | ⚠️ Limited examples | DEPRECATED - use new resources | - |
| **Principal Rate Limits** | ✅ `okta_principal_rate_limits` | ❌ No examples | Per-user/app limits (v6.3.0+) | MEDIUM |
| **Rate Limit Admin Notification** | ✅ `okta_rate_limit_admin_notification` | ❌ No examples | Notification settings (v6.3.0+) | LOW |
| **Rate Limit Warning Threshold** | ✅ `okta_rate_limit_warning_threshold` | ❌ No examples | Warning thresholds (v6.3.0+) | LOW |
| **Security Notification Emails** | ✅ `okta_security_notification_emails` | ⚠️ Limited examples | Security alerts | MEDIUM |
| **Threat Insight Settings** | ✅ `okta_threat_insight_settings` | ⚠️ Limited examples | Threat detection | MEDIUM |
| **Feature Flags** | ⚠️ Partial via org_configuration | ⚠️ Limited examples | EA/Beta features | MEDIUM |

---

## Admin & Roles

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Custom Admin Roles** | ✅ `okta_admin_role_custom` | ⚠️ Limited examples | Custom permissions | MEDIUM |
| **Custom Admin Role Assignments** | ✅ `okta_admin_role_custom_assignments` | ⚠️ Limited examples | Assign custom roles | MEDIUM |
| **Admin Role Targets** | ✅ `okta_admin_role_targets` | ⚠️ Limited examples | Scope admin roles | MEDIUM |
| **Resource Sets** | ✅ `okta_resource_set` | ⚠️ Limited examples | Admin resources | MEDIUM |
| **Role Subscriptions** | ✅ `okta_role_subscription` | ❌ No examples | Role notifications | LOW |

---

## Security & Networks

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Network Zones** | ✅ `okta_network_zone` | ✅ Examples available | IP allowlists | - |
| **Trusted Origins** | ✅ `okta_trusted_origin` | ✅ Examples available | CORS config | - |
| **Trusted Servers** | ✅ `okta_trusted_server` | ⚠️ Limited examples | Server trust | LOW |
| **Behaviors** | ✅ `okta_behavior` | ⚠️ Limited examples | Risk behaviors | MEDIUM |
| **CAPTCHA** | ✅ `okta_captcha` | ⚠️ Limited examples | Bot protection | MEDIUM |
| **CAPTCHA Org Settings** | ✅ `okta_captcha_org_wide_settings` | ⚠️ Limited examples | Global CAPTCHA | MEDIUM |

---

## Customization & Branding

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Brands** | ✅ `okta_brand` | ⚠️ Limited examples | Brand identity | MEDIUM |
| **Themes** | ✅ `okta_theme` | ⚠️ Limited examples | Visual themes | MEDIUM |
| **Customized Sign-In Page** | ✅ `okta_customized_signin_page` | ⚠️ Limited examples | Custom HTML/CSS | MEDIUM |
| **Preview Sign-In Page** | ✅ `okta_preview_signin_page` | ⚠️ Limited examples | Preview changes | LOW |
| **Email Templates** | ✅ `okta_email_template_settings` | ⚠️ Limited examples | Email customization | MEDIUM |
| **Email Customizations** | ✅ `okta_email_customization` | ⚠️ Limited examples | Custom emails | MEDIUM |
| **SMS Templates** | ✅ `okta_template_sms` | ⚠️ Limited examples | SMS messages | LOW |

---

## Domains & Email

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Custom Domains** | ✅ `okta_domain` | ⚠️ Limited examples | Custom URLs | MEDIUM |
| **Domain Certificates** | ✅ `okta_domain_certificate` | ⚠️ Limited examples | TLS certs | MEDIUM |
| **Domain Verification** | ✅ `okta_domain_verification` | ⚠️ Limited examples | DNS verification | MEDIUM |
| **Email Domains** | ✅ `okta_email_domain` | ⚠️ Limited examples | Custom email domains | MEDIUM |
| **Email Domain Verification** | ✅ `okta_email_domain_verification` | ⚠️ Limited examples | DNS verification | MEDIUM |
| **Email Senders** | ✅ `okta_email_sender` | ⚠️ Limited examples | From addresses | MEDIUM |
| **Email Sender Verification** | ✅ `okta_email_sender_verification` | ⚠️ Limited examples | Email verification | MEDIUM |
| **Email SMTP Server** | ✅ `okta_email_smtp_server` | ⚠️ Limited examples | Custom SMTP (v4.19.0+) | MEDIUM |

---

## Integrations & Hooks

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Event Hooks** | ✅ `okta_event_hook` | ✅ Examples available | Webhook events | - |
| **Event Hook Verification** | ✅ `okta_event_hook_verification` | ⚠️ Limited examples | Verify ownership | LOW |
| **Inline Hooks** | ✅ `okta_inline_hook` | ✅ Examples available | Real-time hooks | - |
| **Log Streams** | ✅ `okta_log_stream` | ⚠️ Limited examples | Log forwarding | MEDIUM |

---

## Profile & Schema

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Profile Mappings** | ✅ `okta_profile_mapping` | ✅ Examples available | Attribute mapping | - |
| **App User Base Schema** | ✅ `okta_app_user_base_schema_property` | ⚠️ Limited examples | Modify base attrs | LOW |
| **App User Custom Schema** | ✅ `okta_app_user_custom_schema_property` | ⚠️ Limited examples | Custom app attrs | LOW |
| **SAML App Settings** | ✅ `okta_app_saml_app_settings` | ⚠️ Limited examples | SAML config | LOW |

---

## Links & Metadata

| Feature | Provider Resource | Demo Template | Notes | Priority |
|---------|-------------------|---------------|-------|----------|
| **Link Definitions** | ✅ `okta_link_definition` | ❌ No examples | Link types | LOW |
| **Link Values** | ✅ `okta_link_value` | ❌ No examples | Link instances | LOW |

---

## Summary Statistics

### Overall Coverage

- **Total Provider Resources:** 103
- **Total Data Sources:** 47
- **Resources with Examples:** ~65 (63%)
- **Resources without Examples:** ~38 (37%)
- **Critical Missing Features:** 3 (Resource Owners, Labels, Risk Rules)

### Priority Breakdown

| Priority | Count | Description |
|----------|-------|-------------|
| **CRITICAL** | 3 | Blocks full OIG automation (owners, labels, SOD policies) |
| **HIGH** | 2 | Significant workflow improvement (provisioning, assignments) |
| **MEDIUM** | 25+ | Nice to have, improves automation |
| **LOW** | 50+ | Edge cases, rarely used |

### Coverage by Category

| Category | Coverage | Notes |
|----------|----------|-------|
| **OIG Core** | 95% | Missing: owners, labels, risk rules, principal assignments |
| **Applications** | 90% | Missing: logos, provisioning connection |
| **Users & Groups** | 100% | Fully covered |
| **Auth & Policies** | 95% | Missing: session policies |
| **Customization** | 80% | Most features available, limited examples |
| **Admin & Security** | 85% | Good coverage, some advanced features missing |

---

## Recommendations

### For Immediate Action

1. **Add Examples for Medium Priority Resources**
   - Rate limiting (new v6.3.0 resources)
   - Device assurance policies
   - Email SMTP server
   - Profile enrollment policies
   - Admin roles and resource sets

2. **Request Critical Missing Resources from Okta**
   - `okta_resource_owner` (CRITICAL)
   - `okta_governance_label` (CRITICAL)
   - `okta_risk_rule` (CRITICAL)
   - `okta_app_provisioning_connection` (HIGH)

3. **Document Python Workarounds**
   - Clear guide on when to use Terraform vs Python scripts
   - Migration path when resources are added to provider
   - API-only features reference

### For Demo Template Enhancement

1. **Create comprehensive RESOURCE_EXAMPLES.tf**
   - One example per resource
   - Real-world scenarios
   - Integration patterns

2. **Build example demo scenarios**
   - Healthcare compliance demo
   - Financial SOD demo
   - SaaS tiered access demo

3. **Add validation for all resource types**
   - Extend terraform-validate.yml workflow
   - Add resource-specific checks
   - Create validation library

---

## Missing Resources -- Priority Request List

These resources are not yet available in the Terraform provider.

### Tier 1 -- CRITICAL (Blocks Full OIG Automation)

| Resource | Current Workaround | Impact |
|----------|-------------------|--------|
| `okta_resource_owner` | `scripts/apply_resource_owners.py` | Cannot assign owners in Terraform |
| `okta_governance_label` | `scripts/apply_admin_labels.py` | Cannot categorize resources in Terraform |
| `okta_risk_rule` / `okta_sod_policy` | `scripts/apply_risk_rules.py` | Cannot define SOD policies in code |

### Tier 2 -- HIGH (Reduces Manual Work)

| Resource | Current Workaround | Impact |
|----------|-------------------|--------|
| `okta_app_provisioning_connection` | Manual UI | Cannot automate SCIM provisioning setup |
| `okta_bundle_grant` | Manual UI | Cannot assign bundles to users/groups in Terraform |
| `okta_app_logo` | Manual UI | Cannot automate app branding |

### Tier 3 -- Nice to Have

| Resource | Priority |
|----------|----------|
| `okta_session_policy` | MEDIUM |
| `okta_feature_flag` | MEDIUM |
| `okta_org_contact` | LOW |

---

## Related Documents

- **[API Management](./api-management.md)** -- Python API scripts reference
- **[Terraform Basics](./terraform-basics.md)** -- Resource examples and HCL patterns
- **[Workflow Reference](./workflow-reference.md)** -- GitHub Actions workflows

---

**Document Version:** 2.0
**Last Updated:** 2025-11-19
**Maintained By:** okta-terraform-demo-template maintainers
