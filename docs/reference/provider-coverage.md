# Okta Terraform Provider - Coverage & Analysis

**Last Updated:** 2026-10-20
**Provider Version:** okta/okta v7.0.0 (repo constraint `>= 7.0.0, < 8.0.0`)
**Purpose:** Track which Okta features are available in Terraform vs API-only vs Manual

Numbers and names below come from `terraform providers schema -json` for v7.0.0, not from memory. `environments/myorg/terraform/RESOURCE_EXAMPLES.tf` carries a validated example for most of them.

---

## Summary

The Okta Terraform Provider v7.0.0 ships **162 resources** and **109 data sources**. Key points for this template:

- **OIG coverage is now near-complete**: entitlements, bundles, campaigns, request conditions/sequences/settings, requests, and (since v6.13.0) `okta_resource_owner` and `okta_label`.
- **Still API-only** (Python scripts in `scripts/`): assigning label values to resources, risk rules / SOD policies, entitlement bundle grants (who holds a bundle), and per-app entitlement management enablement.
- **Provisioning** gained `okta_app_connection` (SCIM base URL + auth) and `okta_app_features` (provisioning capabilities); the "App Provisioning Connection: not available" gap from earlier versions is closed for OIN apps.
- **New areas since 6.4.0**: realms, group owners, ITP policy rules, Security Events Providers (SSF receivers), app sign-on policy bulk rules, `okta_oauth2_v1_clients_role_*`, identity sources, push providers, custom sign-in pages.

### Upgrading from 6.x to 7.0.0

v7.0.0 migrated several resources to the Plugin Framework with breaking schema changes. None of them are used by this template's modules, but check your own environment code for:

| Resource | Change |
|----------|--------|
| `okta_trusted_origin` | `scopes = ["CORS"]` → repeated `scopes { type = "CORS" }` blocks (min 1); `active` → `status = "ACTIVE"/"INACTIVE"` |
| `okta_threat_insight_settings` | `network_excludes` → `exclude_zones` |
| `okta_template_sms` | `translations` is now `map(string)` keyed by language code |
| `okta_role_subscription` | `role_type` → `role_ref`; `status` removed |
| `okta_captcha` | `name`, `type`, `site_key`, `secret_key` now optional; `type` updates in place |
| `okta_captcha_org_wide_settings` | Deprecated → `okta_org_captcha` (`enabled_for` → `enabled_pages`) |
| `okta_email_template_settings` | `recipients` now optional; `brand_id`/`template_name` force replacement |

Run `terraform init -upgrade` after bumping the constraint, then `terraform plan` and fix any of the above.

### OIG Resources by Provider Version

| Resource | Added | Purpose |
|----------|-------|---------|
| `okta_campaign` / `okta_review` | v6.0 / v6.1 | Access certification campaigns, review reassignment |
| `okta_entitlement` / `okta_entitlement_bundle` | v6.0 / v6.2 | App entitlements and bundles |
| `okta_request_condition` / `okta_request_sequence` | v6.1 | Requestable resources, approval sequence bindings |
| `okta_request_setting_organization` / `okta_request_setting_resource` | v6.1 | Org and per-resource request settings |
| `okta_request_v2` / `okta_end_user_my_requests` | v6.1 | Create access requests |
| `okta_resource_owner` | v6.13.0 | Owner assignment by ORN |
| `okta_label` | v6.13.0 | Label definitions and values |
| `okta_group_owners` / `okta_group_owner` | v6.x | Group ownership |

Data sources: `okta_catalog_entry_default`, `okta_catalog_entry_user_access_request_fields`, `okta_principal_entitlements`, `okta_resource_owner`, `okta_resource_owners_catalog_resource`, `okta_label`, `okta_resource_label`, `okta_campaign`, `okta_review`, `okta_entitlement`, `okta_entitlement_bundle`, `okta_request_condition`, `okta_request_sequence`, `okta_request_setting_*`, `okta_request_v2`, `okta_iam_resource_set`.

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

| Feature | Provider Resource | Demo Template | Notes |
|---------|-------------------|---------------|-------|
| **Entitlements** | ✅ `okta_entitlement` | ✅ `RESOURCE_EXAMPLES.tf` | Values must be alphabetical by `external_value` |
| **Entitlement Bundles (definitions)** | ✅ `okta_entitlement_bundle` | ✅ `RESOURCE_EXAMPLES.tf`, lifecycle module | `target` block is required |
| **Entitlement Bundle grants** | 👤 Manual / 🔧 `copy_grants_between_orgs.py` | 👤 Okta Admin UI | WHO holds a bundle; read-only via `okta_principal_entitlements` |
| **Access Certification Campaigns** | ✅ `okta_campaign` | ✅ `RESOURCE_EXAMPLES.tf` | Five settings blocks required |
| **Review reassignment** | ✅ `okta_review` | ✅ | Reassign review items |
| **Request Conditions** | ✅ `okta_request_condition` | ✅ | Makes a resource requestable |
| **Approval Sequences** | ⚠️ `okta_request_sequence` | ✅ | Binds an existing sequence; stages authored in Admin UI |
| **Request Settings (Org / Resource)** | ✅ `okta_request_setting_organization`, `okta_request_setting_resource` | ✅ | |
| **Access Requests** | ✅ `okta_request_v2` | ✅ | Create a request |
| **Catalog Entries** | ⚠️ data sources only | ✅ | Read-only |
| **Resource Owners** | ✅ `okta_resource_owner` | ✅ (+ `scripts/apply_resource_owners.py`) | v6.13.0; ORN based |
| **Governance Labels (definitions)** | ✅ `okta_label` | ✅ | v6.13.0 |
| **Governance Labels (assignment)** | 🔧 `scripts/apply_admin_labels.py` | 🔧 `config/label_mappings.json` | `/resource-labels/assign` has no resource |
| **Risk Rules (SOD Policies)** | 🔧 `scripts/apply_risk_rules.py` | 🔧 `config/risk_rules.json` | NOT in provider |
| **Entitlement Management enablement** | 🔧 `scripts/manage_entitlement_settings.py` | 🔧 | Beta API |

---

## Applications

| Feature | Provider Resource | Notes |
|---------|-------------------|-------|
| **OAuth 2.0 / SAML / SWA / Bookmark / Basic Auth / Auto Login / Three-Field / Secure Password Store / Shared Credentials** | ✅ `okta_app_*` | Examples for all |
| **App Logos** | ⚠️ `logo` attribute on each `okta_app_*` | Local file path |
| **Provisioning Connection (SCIM)** | ✅ `okta_app_connection` | Base URL + TOKEN/OAUTH2 auth, activate/deactivate |
| **Provisioning Features** | ⚠️ `okta_app_features` | OIN apps exposing the Application Features API only; cannot be destroyed |
| **Group Push** | ✅ `okta_push_group` | |
| **App assignments** | ✅ `okta_app_group_assignment(s)`, `okta_app_user` | |
| **App Sign-On Policies** | ✅ `okta_app_signon_policy`, `_rule`, `_rules` | `office365_client_include` since v6.14.0 |
| **OAuth API scopes / role assignments** | ✅ `okta_app_oauth_api_scope`, `okta_app_oauth_role_assignment`, `okta_oauth2_v1_clients_role_*` | 13 role-type variants |
| **Federated claims** | ✅ `okta_app_federated_claim` | |
| **App user schema** | ✅ `okta_app_user_schema_property`, `okta_app_user_base_schema_property` | |
| **API service integrations** | ✅ `okta_api_service_integration` | |

---

## Users, Groups & Realms

| Feature | Provider Resource | Notes |
|---------|-------------------|-------|
| **Users / User types / Schema** | ✅ `okta_user`, `okta_user_type`, `okta_user_schema_property`, `okta_user_base_schema_property` | |
| **Admin roles on users** | ✅ `okta_user_admin_roles`, `okta_admin_role_targets` | |
| **User risk (ITP)** | ✅ `okta_user_risk` | Demo trigger |
| **User notification subscriptions** | ✅ `okta_user_subscription` | v7.0.0 |
| **Groups / Rules / Memberships** | ✅ `okta_group`, `okta_group_rule`, `okta_group_memberships` (`users`), `okta_user_group_memberships` | |
| **Group owners** | ✅ `okta_group_owners` (authoritative), `okta_group_owner` | |
| **Group admin roles** | ✅ `okta_group_role` | |
| **Group schema** | ✅ `okta_group_schema_property` | |
| **Realms** | ✅ `okta_realm`, `okta_realm_assignment` | |
| **Linked objects** | ✅ `okta_link_definition`, `okta_link_value` | Manager relationships |
| **Identity sources (anything-as-a-source)** | ✅ `okta_identity_source_user`, `_group`, `_group_membership`, `_import` | |

---

## Authentication, Policies & Security

| Feature | Provider Resource | Notes |
|---------|-------------------|-------|
| **Authorization servers** | ✅ `okta_auth_server*`, `okta_trusted_server` | 8 resources |
| **Global session / MFA / password policies** | ✅ `okta_policy_signon`, `okta_policy_mfa`, `okta_policy_password` + `_rule_*` + `_default` | |
| **Profile enrollment** | ✅ `okta_policy_profile_enrollment`, `_apps`, `okta_policy_rule_profile_enrollment`, `okta_ui_schema` | |
| **IdP discovery** | ✅ `okta_policy_rule_idp_discovery` | `idp_providers` block |
| **Device assurance** | ✅ `okta_policy_device_assurance_{android,chromeos,ios,macos,windows}` | ChromeOS uses `tpsp_*` only |
| **ITP policies** | ✅ `okta_entity_risk_policy_rule`, `okta_session_violation_policy_rule`, `okta_post_auth_session_policy_rule` | System policies via data sources |
| **Security Events Provider (SSF)** | ✅ `okta_security_events_provider` | |
| **Authenticators** | ✅ `okta_authenticator`, `okta_authenticator_method_webauthn`, `okta_authenticator_webauthn_custom_aaguid`, `okta_factor`, `okta_factor_totp` | |
| **Push providers** | ✅ `okta_push_provider` | APNS / FCM |
| **Network zones / Trusted origins / Behaviors / ThreatInsight** | ✅ | v7 schema changes above |
| **CAPTCHA** | ✅ `okta_captcha`, `okta_org_captcha` | `okta_captcha_org_wide_settings` deprecated |
| **Rate limiting** | ✅ `okta_rate_limiting`, `okta_principal_rate_limits`, `okta_rate_limit_admin_notification_settings`, `okta_rate_limit_warning_threshold_percentage` | |
| **Security notification emails** | ✅ `okta_security_notification_emails` | SSWS token only |
| **Devices** | ⚠️ `okta_device` | Lifecycle action on an existing device |

---

## Identity Providers, Branding, Email, Domains, Hooks

| Feature | Provider Resource | Notes |
|---------|-------------------|-------|
| **IdPs** | ✅ `okta_idp_saml` (+ `okta_idp_saml_key`, `kid` required), `okta_idp_oidc`, `okta_idp_social` | |
| **Profile mappings** | ✅ `okta_profile_mapping` | |
| **Brands / Themes** | ✅ `okta_brand`, `okta_theme`, `okta_customized_signin_page`, `okta_preview_signin_page` | |
| **Email** | ✅ `okta_email_customization`, `okta_email_template_settings`, `okta_email_domain(+_verification)`, `okta_email_sender(+_verification)`, `okta_email_smtp_server` | |
| **Domains** | ✅ `okta_domain` (`name`, `certificate_source_type`), `okta_domain_verification`, `okta_domain_certificate` | |
| **SMS templates** | ✅ `okta_template_sms` | map translations in v7 |
| **Hooks** | ✅ `okta_event_hook`, `okta_event_hook_verification`, `okta_inline_hook`, `okta_hook_key` | `channel`/`auth` are map attributes |
| **Log streams** | ✅ `okta_log_stream` | `settings` block |

---

## Admin & Org

| Feature | Provider Resource | Notes |
|---------|-------------------|-------|
| **Custom admin roles** | ✅ `okta_admin_role_custom`, `okta_admin_role_custom_assignments`, `okta_resource_set` | Resource sets take endpoints or ORNs |
| **Role notification subscriptions** | ✅ `okta_role_subscription` | `role_ref` in v7 |
| **API tokens / app tokens** | ⚠️ `okta_api_token`, `okta_app_token` | Mostly read/revoke |
| **Agent pool updates** | ✅ `okta_agent_pool_update` | |
| **Org configuration / support** | ✅ `okta_org_configuration`, `okta_org_support` | |
| **Feature flags** | ✅ `okta_feature` | `feature_id` + `life_cycle` |
| **Session policies (global)** | ✅ `okta_policy_signon` | Classic naming; OIE uses app sign-on policies |

---

## Still Missing from the Provider

| Need | Current Workaround |
|------|-------------------|
| Label-to-resource assignment | `scripts/apply_admin_labels.py`, `labels-apply*.yml` |
| Risk rules / SOD policies | `scripts/apply_risk_rules.py`, `oig-risk-rules-*.yml` |
| Entitlement bundle grants | Okta Admin UI; `scripts/copy_grants_between_orgs.py` for migration |
| Entitlement management enablement per app | `scripts/manage_entitlement_settings.py` |
| Approval sequence stages | Access Requests admin UI (`okta_request_sequence` only binds) |

---

## Related Documents

- **[API Management](./api-management.md)** -- Python API scripts reference
- **[Terraform Basics](./terraform-basics.md)** -- Resource examples and HCL patterns
- **[Workflow Reference](./workflow-reference.md)** -- GitHub Actions workflows
- **Provider changelog** -- https://github.com/okta/terraform-provider-okta/releases

---

**Document Version:** 3.0
**Last Updated:** 2026-10-20
**Maintained By:** okta-terraform-demo-template maintainers
