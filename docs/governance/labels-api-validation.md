# Okta IGA Labels API - Validation & Import

## 📋 Overview

This document describes the validation of the Okta Identity Governance (IGA) Labels API integration and the process for importing existing labels from your Okta environment.

**Based on:** [Okta IGA Labels API Documentation](https://developer.okta.com/docs/api/iga/openapi/governance.api/tag/Labels/)

## 🎯 Expected Environment State

For the MyOrg environment:
- **Existing Labels**: 2 labels already created
- **Resource Assignments**: 0 (no resources assigned yet)
- **Goal**: Validate import, then apply labels to admin entitlements

## 🔗 Labels API Endpoints

### Base URL
```
https://{org-name}.{base-url}/governance/api/v1
```

### Endpoints

#### 1. List All Labels
```http
GET /governance/api/v1/labels
```

**Parameters:**
- `limit` (optional): Number of results per page (default: 20, max: 200)
- `after` (optional): Pagination cursor

**Response:**
```json
{
  "data": [
    {
      "id": "label-id-123",
      "name": "Privileged",
      "description": "High-privilege access requiring enhanced monitoring",
      "color": "#FF0000",
      "created": "2025-11-01T00:00:00.000Z",
      "lastUpdated": "2025-11-01T00:00:00.000Z"
    }
  ],
  "_links": {
    "next": {
      "href": "..."
    }
  }
}
```

#### 2. Get Specific Label
```http
GET /governance/api/v1/labels/{labelName}
```

**Response:** Single label object (same structure as above)

#### 3. Create Label
```http
POST /governance/api/v1/labels
```

**Request Body:**
```json
{
  "name": "Privileged",
  "description": "High-privilege access requiring enhanced monitoring",
  "color": "#FF0000"
}
```

#### 4. Get Resources for Label
```http
GET /governance/api/v1/labels/{labelName}/resources
```

**Response:**
```json
{
  "data": [
    {
      "orn": "orn:okta:governance:org:entitlement-bundles:ent123",
      "type": "ENTITLEMENT_BUNDLE",
      "name": "Salesforce Admin Access",
      "labels": ["Privileged", "Compliance-Required"]
    }
  ]
}
```

#### 5. Apply Label to Resources
```http
PUT /governance/api/v1/labels/{labelName}/resources
```

**Request Body:**
```json
{
  "resourceOrns": [
    "orn:okta:governance:org:entitlement-bundles:ent123",
    "orn:okta:governance:org:entitlement-bundles:ent456"
  ]
}
```

#### 6. Remove Label from Resources
```http
DELETE /governance/api/v1/labels/{labelName}/resources
```

**Request Body:** Same as PUT (list of resource ORNs)

## 📊 Label Data Model

### Required Fields
- `name` (string): Unique label identifier

### Optional Fields
- `id` (string): System-generated label ID
- `description` (string): Human-readable description
- `color` (string): Hex color code (e.g., "#FF0000")
- `created` (ISO 8601): Creation timestamp
- `lastUpdated` (ISO 8601): Last modification timestamp

### Validation Rules
1. Label names must be unique
2. Color codes must be valid hex format
3. Names are used as identifiers in API calls
4. IDs are system-generated, don't include in CREATE requests

## 🧪 Validation Script

We provide a comprehensive validation script to test Labels API integration:

### Usage

```bash
# Set credentials
export OKTA_API_TOKEN="your-token"
export OKTA_ORG_NAME="demo-myorg"
export OKTA_BASE_URL="oktapreview.com"

# Run validation
python3 scripts/validate_labels_api.py

# Run with import comparison
python3 scripts/validate_labels_api.py --validate-imports
```

### What It Tests

1. **API Connection**: Verifies basic Okta API access
2. **List Labels**: Tests GET /labels endpoint
3. **Individual Label Retrieval**: Tests GET /labels/{name}
4. **Resource Assignments**: Tests GET /labels/{name}/resources
5. **Data Structure**: Validates response matches spec
6. **Import Comparison**: Compares with previous export data

### Expected Results

For MyOrg environment:
```
✅ API Connection: SUCCESS
✅ List Labels: SUCCESS
✅ Labels Found: 2
✅ Resource Assignments: 0 (for each label)
```

## 🔄 Import Workflow

### Step 1: Validate Current State

Run the validation workflow to verify we can access existing labels:

```bash
# Via GitHub Actions
Go to: Actions → "MyOrg - Validate Labels API" → Run workflow
```

**Expected Output:**
- Connection: ✅ SUCCESS
- Labels Found: 2
- Each label has 0 resource assignments

### Step 2: Export Existing Labels

Export labels to understand current configuration:

```bash
# Local
python3 scripts/okta_api_manager.py \
  --action export \
  --export-labels \
  --output current_labels.json

# Via GitHub Actions
Actions → "MyOrg - Export OIG Labels" → Run workflow
```

**Export Structure:**
```json
{
  "export_date": "2025-11-07T21:28:31Z",
  "okta_org": "demo-myorg",
  "export_status": {
    "labels": "success"
  },
  "labels": [
    {
      "name": "Privileged",
      "description": "High-privilege access",
      "resources": []
    },
    {
      "name": "Standard",
      "description": "Standard user access",
      "resources": []
    }
  ]
}
```

### Step 3: Update Configuration

Update `config/api_config.json` to match existing labels:

```json
{
  "labels": {
    "definitions": [
      {
        "name": "Privileged",
        "description": "High-privilege access requiring enhanced monitoring and approval",
        "color": "#FF0000"
      },
      {
        "name": "Standard",
        "description": "Standard user access with normal approval workflows",
        "color": "#00FF00"
      }
    ],
    "assignments": {
      "entitlements": {
        "salesforce_admin": ["Privileged"],
        "workday_admin": ["Privileged"],
        "aws_admin": ["Privileged"],
        "okta_super_admin": ["Privileged"],
        "salesforce_user": ["Standard"],
        "jira_user": ["Standard"]
      }
    }
  }
}
```

### Step 4: Apply Label Assignments

Apply labels to your entitlements:

```bash
# Via GitHub Actions
Actions → "MyOrg - Apply OIG Labels" → Run workflow

# Local
python3 scripts/okta_api_manager.py \
  --action apply \
  --config config/api_config.json
```

### Step 5: Verify Application

Export labels again to verify assignments were applied:

```bash
python3 scripts/okta_api_manager.py \
  --action export \
  --export-labels \
  --output labels_after_apply.json
```

**Expected Result:**
```json
{
  "labels": [
    {
      "name": "Privileged",
      "description": "High-privilege access",
      "resources": [
        {
          "orn": "orn:okta:governance:...:entitlement-bundles:ent_salesforce_admin",
          "name": "Salesforce Admin Access",
          "type": "ENTITLEMENT_BUNDLE"
        },
        // ... 3 more admin entitlements
      ]
    },
    {
      "name": "Standard",
      "description": "Standard user access",
      "resources": [
        {
          "orn": "orn:okta:governance:...:entitlement-bundles:ent_salesforce_user",
          "name": "Salesforce Standard User",
          "type": "ENTITLEMENT_BUNDLE"
        },
        // ... 1 more standard entitlement
      ]
    }
  ]
}
```

## 🐛 Troubleshooting

### Issue: "400 Bad Request" when listing labels

**Cause:** Labels API may not be available or enabled on the tenant

**Solutions:**
1. Verify OIG is enabled: Admin Console → Settings → Features → Identity Governance
2. Check API token has correct scopes: `okta.governance.labels.read` and `okta.governance.labels.manage`
3. Verify tenant is on a plan that includes OIG features

### Issue: "404 Not Found" on labels endpoint

**Cause:** Labels API endpoint doesn't exist or isn't accessible

**Solutions:**
1. Confirm base URL is correct: `{org}.okta.com` or `{org}.oktapreview.com`
2. Verify API path: `/governance/api/v1/labels` (not `/api/v1/labels`)
3. Check Okta tenant version supports IGA features

### Issue: Labels found in validation but export shows 0

**Cause:** Mismatch between validation script and export script

**Solutions:**
1. Both scripts should use the same endpoint: `/governance/api/v1/labels`
2. Check for error handling that silently fails in export
3. Verify response parsing is correct (check `data` array)

### Issue: Cannot apply labels to entitlements

**Cause:** Resources not found or incorrect ORN format

**Solutions:**
1. Verify entitlements exist in Okta first
2. Check ORN format: `orn:okta:governance:{org}:entitlement-bundles:{id}`
3. Use the correct resource type in ORN
4. Import/create entitlements in Terraform before applying labels

## 📚 Related Documentation

- [API Management Guide](API_MANAGEMENT.md)
- [Label Configuration Guide](../config/README.md)
- [OIG Manual Import](OIG_MANUAL_IMPORT.md)
- [Okta IGA API Docs](https://developer.okta.com/docs/api/iga/)

## ✅ Validation Checklist

Before applying labels to production:

- [ ] Run validation script locally
- [ ] Verify 2 existing labels are detected
- [ ] Confirm 0 resource assignments for each label
- [ ] Export current labels to JSON
- [ ] Update `api_config.json` with correct label names
- [ ] Test label application in dry-run mode
- [ ] Review GitHub Actions workflow results
- [ ] Verify labels in Okta Admin Console
- [ ] Document any discrepancies or issues

## 🔐 Required API Scopes

Ensure your API token has these scopes:

- `okta.governance.labels.read` - Read labels and assignments
- `okta.governance.labels.manage` - Create labels and apply to resources
- `okta.governance.accessRequests.read` - View entitlements (for ORN lookup)
- `okta.apps.read` - Read apps (for app ORNs)
- `okta.groups.read` - Read groups (for group ORNs)

## 📊 Success Metrics

After successful validation and import:

| Metric | Expected | Actual |
|--------|----------|--------|
| Labels Found | 2 | ___ |
| API Connection | ✅ | ___ |
| List Labels Works | ✅ | ___ |
| Resource Assignments (initial) | 0 per label | ___ |
| Resource Assignments (after apply) | 4 for Privileged, 2 for Standard | ___ |

## 🎯 Next Steps

1. ✅ Run validation workflow
2. ✅ Confirm 2 labels exist with 0 assignments
3. ✅ Update api_config.json with label assignments
4. ✅ Run apply workflow to assign labels to admin entitlements
5. ✅ Verify in Okta Admin Console
6. ✅ Document results

---

**Last Updated:** 2025-11-07
**Status:** Ready for validation testing
