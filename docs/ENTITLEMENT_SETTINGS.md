# Entitlement Settings API

Enable or disable entitlement management on Okta applications via API.

## Overview

The **Entitlement Settings API** was released in December 2025 (release 2025.12.0) and is currently in **Beta**. This API allows administrators to programmatically enable or disable entitlement management for applications, which was previously only possible through the Okta Admin Console.

**API Reference:** [Entitlement Settings API](https://developer.okta.com/docs/api/iga/openapi/governance.api/tag/Entitlement-Settings/)

## Why Use This API?

Before this API, enabling entitlement management required:
1. Navigate to Okta Admin Console
2. Go to Applications → Select App → Provisioning
3. Click "Enable Governance Engine"

Now you can automate this with a single API call or workflow.

## Use Cases

- **Batch enable** entitlement management on multiple apps
- **Automate** app setup in GitOps pipelines
- **Audit** which apps have entitlement management enabled
- **Programmatic control** for demo environment setup

## Prerequisites

1. **Okta Identity Governance (OIG) license** - Required for entitlement management
2. **API token** with governance permissions
3. **App must be provisioning-enabled** - Only provisioning-capable apps can have entitlement management

## Usage

### Script: manage_entitlement_settings.py

Located at: `scripts/manage_entitlement_settings.py`

#### List All Apps with Entitlement Status

```bash
# Set environment variables
export OKTA_ORG_NAME="your-org"
export OKTA_BASE_URL="okta.com"
export OKTA_API_TOKEN="your-token"

# List all apps and their entitlement management status
python scripts/manage_entitlement_settings.py --action list
```

Output:
```
ID                        Label                                   Entitlement Mgmt     Status
====================================================================================================
0oaXXXXXXXX1              Salesforce                              ENABLED              ACTIVE
0oaXXXXXXXX2              ServiceNow                              Not Enabled          ACTIVE
0oaXXXXXXXX3              Workday                                 ENABLED              ACTIVE
====================================================================================================

Total: 15 apps, 3 with entitlement management enabled
```

#### Check Status for Specific App

```bash
python scripts/manage_entitlement_settings.py \
  --action status \
  --app-id 0oaXXXXXXXX
```

#### Enable Entitlement Management (Dry Run)

```bash
# Preview what would happen
python scripts/manage_entitlement_settings.py \
  --action enable \
  --app-id 0oaXXXXXXXX \
  --dry-run
```

#### Enable Entitlement Management (Apply)

```bash
# Actually enable it
python scripts/manage_entitlement_settings.py \
  --action enable \
  --app-id 0oaXXXXXXXX
```

#### Enable for Multiple Apps by Label Pattern

```bash
# Enable for all apps matching "Sales*"
python scripts/manage_entitlement_settings.py \
  --action enable \
  --app-label "Sales*" \
  --dry-run
```

#### Disable Entitlement Management

```bash
# WARNING: This may cause data loss - see warnings below
python scripts/manage_entitlement_settings.py \
  --action disable \
  --app-id 0oaXXXXXXXX
```

### GitHub Workflow

A workflow is provided at `.github/workflows/manage-entitlement-settings.yml`.

#### Run via GitHub CLI

```bash
# List all apps
gh workflow run manage-entitlement-settings.yml \
  -f environment=myorg \
  -f action=list

# Enable for specific app (dry run)
gh workflow run manage-entitlement-settings.yml \
  -f environment=myorg \
  -f action=enable \
  -f app_id=0oaXXXXXXXX \
  -f dry_run=true

# Enable for specific app (apply)
gh workflow run manage-entitlement-settings.yml \
  -f environment=myorg \
  -f action=enable \
  -f app_id=0oaXXXXXXXX \
  -f dry_run=false
```

#### Workflow Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `environment` | Yes | Target GitHub environment (for secrets) |
| `action` | Yes | `list`, `status`, `enable`, or `disable` |
| `app_id` | No* | Okta application ID |
| `app_label` | No* | App label pattern (supports wildcards) |
| `dry_run` | Yes | Preview changes without applying |

*Required for `status`, `enable`, and `disable` actions

## Important Warnings

### Disabling Entitlement Management

From Okta documentation:

> **WARNING:** With Entitlement Management, Governance Engine is the source of entitlements for apps. Disabling entitlement management may cause:
> - Loss of entitlement configurations
> - Loss of access review data
> - Loss of bundle assignments

**Recommendation:** Do not disable entitlement management on apps with active entitlement configurations unless you have a specific migration plan.

### Fresh App Instances

From Okta documentation:

> Entitlement Management can't be enabled on existing app instances that are configured for provisioning. Instead, wait for Okta to provide a migration path. Create a fresh app instance of a provisioning-enabled application to use connectors that support Entitlement Management.

### System Apps

The script automatically skips Okta system apps that cannot have entitlement management:
- okta-iga-reviewer
- okta-flow-sso
- okta-access-requests-resource-catalog
- flow
- okta-atspoke-sso
- okta-admin-console
- okta-dashboard
- okta-browser-plugin

## API Endpoint Details

**Base URL:** `https://{org}.{domain}/governance/api/v1/entitlement-settings`

### Get Entitlement Settings

```
GET /governance/api/v1/entitlement-settings/{appId}
```

### Enable Entitlement Management

```
POST /governance/api/v1/entitlement-settings
Content-Type: application/json

{
  "resourceId": "0oaXXXXXXXX",
  "resourceType": "APPLICATION",
  "enabled": true
}
```

Or:

```
PUT /governance/api/v1/entitlement-settings/{appId}
Content-Type: application/json

{
  "enabled": true
}
```

### Disable Entitlement Management

```
DELETE /governance/api/v1/entitlement-settings/{appId}
```

Or:

```
PUT /governance/api/v1/entitlement-settings/{appId}
Content-Type: application/json

{
  "enabled": false
}
```

## Integration with GitOps

### Typical Workflow

1. **Create app via Terraform**
   ```hcl
   resource "okta_app_oauth" "my_app" {
     label = "My Application"
     # ...
   }
   ```

2. **Enable entitlement management via API** (after Terraform apply)
   ```bash
   python scripts/manage_entitlement_settings.py \
     --action enable \
     --app-id ${okta_app_oauth.my_app.id}
   ```

3. **Create entitlements via Terraform**
   ```hcl
   resource "okta_entitlement" "my_app_access" {
     app_id = okta_app_oauth.my_app.id
     # ...
   }
   ```

4. **Create bundles via Terraform**
   ```hcl
   resource "okta_entitlement_bundle" "standard_access" {
     # ...
   }
   ```

### Why Not Terraform?

The Okta Terraform provider does not currently support the Entitlement Settings API. This is a new Beta API (December 2025) and may be added to the provider in a future release.

In the meantime, use:
- This Python script for automation
- The GitHub workflow for CI/CD integration
- The Okta Admin Console for manual operations

## Troubleshooting

### "App not eligible for entitlement management"

- Ensure the app is provisioning-enabled
- Check if the app connector supports entitlement management
- Verify OIG license is active on the org

### "Permission denied"

- Verify API token has governance permissions
- Check if token has expired
- Ensure user has Super Admin or appropriate role

### "Rate limited"

The script handles rate limiting automatically with exponential backoff. For bulk operations, consider:
- Running during off-peak hours
- Using smaller batches
- Increasing delay between requests

## Related Documentation

- [Enable Entitlement Management](https://help.okta.com/oie/en-us/content/topics/identity-governance/em/enable-ge.htm)
- [Okta Identity Governance API](https://developer.okta.com/docs/api/iga/)
- [2025 OIG API Release Notes](https://developer.okta.com/docs/release-notes/2025-okta-identity-governance/)
- [API_MANAGEMENT.md](./API_MANAGEMENT.md) - Other OIG API operations
